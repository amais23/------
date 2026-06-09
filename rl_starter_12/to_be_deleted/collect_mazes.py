import ale_py
import gymnasium as gym
import numpy as np
from collections import defaultdict
import json
import os
import time

gym.register_envs(ale_py)

def get_neighbor_by_action(graph, px, py, action):
    for nx, ny in graph[(px, py)]:
        if action == 3: # LEFT
            if px > 140 and nx < 25: return (nx, ny)
            if nx < px - 1 and abs(ny - py) < 5: return (nx, ny)
        elif action == 2: # RIGHT
            if px < 25 and nx > 140: return (nx, ny)
            if nx > px + 1 and abs(ny - py) < 5: return (nx, ny)
        elif action == 1: # UP
            if ny < py - 1 and abs(nx - px) < 5: return (nx, ny)
        elif action == 4: # DOWN
            if ny > py + 1 and abs(nx - px) < 5: return (nx, ny)
    return None

def is_in_house(gx, gy):
    return (75 <= gx <= 101) and (72 <= gy <= 88)

def run_exploration(num_episodes=200):
    env = gym.make("ALE/MsPacman-v5", obs_type="ram")
    
    # Store graphs for each level
    # Level 1-2: Maze 1
    # Level 3-5: Maze 2
    # Level 6-9: Maze 3
    # Level 10-13: Maze 4
    maze_graphs = {
        1: defaultdict(set), # Maze 1
        2: defaultdict(set), # Maze 2
        3: defaultdict(set), # Maze 3
        4: defaultdict(set)  # Maze 4
    }
    
    # Track the active maze based on level
    # Level 1, 2 -> Maze 1
    # Level 3, 4, 5 -> Maze 2
    # Level 6, 7, 8, 9 -> Maze 3
    # Level 10+ -> Maze 4
    def get_maze_id(level):
        if level in [1, 2]: return 1
        elif level in [3, 4, 5]: return 2
        elif level in [6, 7, 8, 9]: return 3
        else: return 4

    print(f"Starting Ms. Pac-Man exploration to collect maze layouts ({num_episodes} episodes)...")
    
    for ep in range(num_episodes):
        obs, info = env.reset()
        prev_p = None
        prev_dots_eaten = 0
        current_level = 1
        
        step = 0
        while True:
            px, py = int(obs[10]), int(obs[16])
            dots_eaten = int(obs[119])
            
            # Check for level transition: dots_eaten reset to 0 and previous dots_eaten was high
            if dots_eaten < prev_dots_eaten and prev_dots_eaten > 180:
                old_level = current_level
                current_level += 1
                print(f"--- LEVEL UP! Level {old_level} -> {current_level} (dots eaten before: {prev_dots_eaten}) ---")
                prev_p = None # prevent spurious connection across levels
                
            prev_dots_eaten = dots_eaten
            maze_id = get_maze_id(current_level)
            graph = maze_graphs[maze_id]
            
            # Record coordinates and build connection graph
            if prev_p is not None:
                ppx, ppy = prev_p
                if (ppx, ppy) != (px, py):
                    dx = abs(px - ppx)
                    dy = abs(py - ppy)
                    is_warp = (ppy == py) and ((ppx < 25 and px > 140) or (ppx > 140 and px < 25))
                    if (dx + dy) <= 15 or is_warp:
                        graph[(ppx, ppy)].add((px, py))
                        graph[(px, py)].add((ppx, ppy))
                        
            prev_p = (px, py)
            
            # Heuristic action selection
            # 1. Escape ghosts
            min_g_dist = 999
            closest_ghost = None
            for i in range(4):
                gx, gy = int(obs[6 + i]), int(obs[12 + i])
                if not is_in_house(gx, gy) and obs[116] == 0: # non-blue active ghost
                    dist = abs(px - gx) + abs(py - gy)
                    if dist < min_g_dist:
                        min_g_dist = dist
                        closest_ghost = (gx, gy)
            
            action = 0
            if min_g_dist < 20 and closest_ghost is not None:
                # Run away! Choose direction that maximizes Manhattan distance to closest ghost
                best_act = 0
                max_d = -1
                for a in [1, 2, 3, 4]: # UP, RIGHT, LEFT, DOWN
                    # Try to estimate next position
                    npx, npy = px, py
                    if a == 1: npy -= 2
                    elif a == 4: npy += 2
                    elif a == 3: npx -= 2
                    elif a == 2: npx += 2
                    d = abs(npx - closest_ghost[0]) + abs(npy - closest_ghost[1])
                    if d > max_d:
                        max_d = d
                        best_act = a
                action = best_act
            else:
                # Explore / eat dots
                # Prefer moving in a direction we haven't visited or just random cardinal
                action = np.random.choice([1, 2, 3, 4], p=[0.25, 0.25, 0.25, 0.25])
                
            obs, reward, terminated, truncated, info = env.step(action)
            step += 1
            
            if terminated or truncated:
                break
                
        if (ep + 1) % 20 == 0:
            print(f"Episode {ep+1}/{num_episodes}:")
            for m_id, g in maze_graphs.items():
                print(f"  Maze {m_id}: {len(g)} nodes")
                
    env.close()
    
    # Save the graphs
    output = {}
    for m_id, g in maze_graphs.items():
        # Convert set of tuples to list of lists for JSON serialization
        output[f"maze_{m_id}"] = {f"{k[0]},{k[1]}": [list(v) for v in vs] for k, vs in g.items()}
        
    out_path = os.path.join(os.path.dirname(__file__), "complete_mazes.json")
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Successfully saved all maze graphs to {out_path}")

if __name__ == "__main__":
    run_exploration(200)
