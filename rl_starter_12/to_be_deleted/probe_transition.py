import os
import sys
import json
import pickle
import gymnasium as gym
import ale_py
import numpy as np
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent import Agent

JSON_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "complete_mazes.json")
SCRATCH    = os.path.dirname(os.path.abspath(__file__))

def get_maze_id(level):
    """2 levels per maze, cycling every 8 stages."""
    return (level // 2) % 4 + 1

def load_graphs():
    maze_graphs = {i: defaultdict(set) for i in range(1, 5)}
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r") as f:
                data = json.load(f)
            for m_id in range(1, 5):
                key = f"maze_{m_id}"
                if key in data:
                    for k_str, neighbors in data[key].items():
                        kx, ky = map(int, k_str.split(","))
                        for nx, ny in neighbors:
                            maze_graphs[m_id][(kx, ky)].add((nx, ny))
            totals = {i: len(maze_graphs[i]) for i in range(1, 5)}
            print(f"[Load] Loaded: {totals}")
        except Exception as e:
            print(f"[Load] Error: {e}")
    return maze_graphs

def save_graphs(maze_graphs):
    output = {}
    for m_id, g in maze_graphs.items():
        output[f"maze_{m_id}"] = {
            f"{k[0]},{k[1]}": [list(v) for v in vs]
            for k, vs in g.items()
        }
    with open(JSON_PATH, "w") as f:
        json.dump(output, f, indent=2)
    totals = {i: len(maze_graphs[i]) for i in range(1, 5)}
    print(f"[Save] {totals}")

def update_graph(maze_graphs, px, py, prev_p, current_maze_id):
    if prev_p is None:
        return
    ppx, ppy = prev_p
    if (ppx, ppy) == (px, py):
        return
    dist = abs(px - ppx) + abs(py - ppy)
    is_warp = (ppy == py) and ((ppx < 25 and px > 140) or (ppx > 140 and px < 25))
    if dist <= 15 or is_warp:
        graph = maze_graphs[current_maze_id]
        graph[(ppx, ppy)].add((px, py))
        graph[(px, py)].add((ppx, ppy))

def save_ale_state(env, filename):
    """Save ALE state using pickle."""
    state = env.unwrapped.clone_state()
    path = os.path.join(SCRATCH, filename)
    with open(path, "wb") as f:
        pickle.dump(state, f)
    print(f"[State Save] Saved → {path}")

def main():
    gym.register_envs(ale_py)
    env = gym.make("ALE/MsPacman-v5", obs_type="ram")
    obs, info = env.reset()

    agent = Agent()

    # Inject a pure-heuristic model (no PPO weights needed)
    class HeuristicModel:
        def predict(self, feats, state=None, deterministic=True):
            min_non_blue_dist = feats[14] * 100.0
            blue_timer        = feats[15] * 255.0
            min_blue_dist     = feats[32] * 100.0
            if min_non_blue_dist < 16.0:
                sid = 2  # Escape
            elif blue_timer > 0.05 and min_blue_dist < 50.0:
                sid = 3  # Chase Blue
            else:
                sid = 0  # Eat Pellet
            return np.array(sid), state

    agent.model = HeuristicModel()
    agent.reset(obs)

    maze_graphs = load_graphs()

    prev_p     = None
    prev_lives = 3
    target_level = 2   # Maze 2 starts at RAM level 2

    print(f"Agent is playing to clear Levels 0–1 (Maze 1) and reach Level {target_level} (Maze 2)...")

    saved_state = {m: False for m in range(2, 5)}  # track which state files are saved
    record_steps = {m: 0 for m in range(2, 5)}
    RECORD_LIMIT = 300

    for step in range(50000):
        action = agent.act(obs, env.action_space)
        obs, reward, terminated, truncated, info = env.step(action)

        px, py  = int(obs[10]), int(obs[16])
        level   = int(obs[123]) >> 4
        lives   = int(obs[123]) & 0x0F
        maze_id = get_maze_id(level)

        # --- Save state & record nodes for Mazes 2–4 ---
        if level >= target_level:
            # Save state on first frame of each new maze
            if not saved_state[maze_id]:
                print(f"\n🎉 Reached Level {level} (Maze {maze_id}) at step {step}!")
                save_ale_state(env, f"maze_{maze_id}_state.pkl")
                saved_state[maze_id] = True
                prev_p = None  # reset chain at level boundary

            # Record graph nodes
            if lives >= prev_lives:
                update_graph(maze_graphs, px, py, prev_p, maze_id)
            else:
                prev_p = None

            record_steps[maze_id] += 1
            if record_steps[maze_id] >= RECORD_LIMIT:
                print(f"Recorded {len(maze_graphs[maze_id])} nodes for Maze {maze_id}.")
                save_graphs(maze_graphs)
                # Stop once we've recorded Maze 2 (can extend to 3/4 if needed)
                if maze_id == 2:
                    print("Done! Exiting.")
                    break

        # Infinite lives patch
        raw_level = int(obs[123]) >> 4
        env.unwrapped.ale.setRAM(123, (raw_level << 4) | 3)
        obs[123] = (raw_level << 4) | 3

        prev_p     = (px, py)
        prev_lives = 3

        if terminated or truncated:
            print("Episode ended, resetting...")
            obs, info = env.reset()
            env.unwrapped.ale.setRAM(123, 3)
            obs[123] = 3
            agent.reset(obs)
            prev_p     = None
            prev_lives = 3

if __name__ == "__main__":
    main()
