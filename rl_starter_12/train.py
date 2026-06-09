"""
ML Arena — MsPacman SB3 Training Script with Option D Hierarchical Wrapper
"""

import ale_py
import gymnasium as gym
from collections import defaultdict
import numpy as np
from stable_baselines3.common.env_util import make_vec_env

from model import (
    ALGORITHM, POLICY, POLICY_KWARGS, SAVE_PATH,
    extract_strategic_features, heuristic_execute, check_action_safety, is_in_house, dijkstra_distance,
    load_prebuilt_graph, get_maze_id, init_pellets_and_energizers,
    MAZE_1_BASE64, MAZE_2_BASE64, MAZE_3_BASE64, MAZE_4_BASE64
)

gym.register_envs(ale_py)

# ═══ ✅ Tune training hyperparameters ══════════════════════════════
TOTAL_TIMESTEPS = 2_000_000 # 2M timesteps for PPO to converge
N_ENVS          = 4         # parallel environments for faster sampling
# ══════════════════════════════════════════════════════════════════

class PacmanStrategicWrapper(gym.Wrapper):
    """
    Environment wrapper that exposes a Discrete(5) macro-action space
    and a 34-dimensional strategic feature observation space.
    """
    def __init__(self, env):
        super().__init__(env)
        # Load all pre-built graphs for Mazes 1-4
        self.graphs = {
            1: load_prebuilt_graph(MAZE_1_BASE64),
            2: load_prebuilt_graph(MAZE_2_BASE64),
            3: load_prebuilt_graph(MAZE_3_BASE64),
            4: load_prebuilt_graph(MAZE_4_BASE64),
        }
        self.graph = self.graphs[1]
        
        self.prev_p = None
        self.remaining_pellets = set()
        self.remaining_energizers = set()
        self.visited_nodes = set()
        self.prev_extra_lives = 2
        self.prev_level = None
        self.last_raw_obs = None
        self.prev_ghosts_pos = None
        self.last_action = 0
        
        # Action space: 5 macro actions
        self.action_space = gym.spaces.Discrete(5)
        
        # Observation space: 34 dimensions
        self.observation_space = gym.spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(34,),
            dtype=np.float32
        )

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self.prev_p = None
        self.prev_extra_lives = int(obs[123]) & 0x0F
        self.prev_level = int(obs[123]) >> 4
        self.last_raw_obs = obs
        self.prev_ghosts_pos = None
        self.last_action = 0
        
        maze_id = get_maze_id(self.prev_level)
        self.graph = self.graphs[maze_id]
        
        self.visited_nodes.clear()
        self.remaining_pellets.clear()
        self.remaining_energizers.clear()
        
        # Pre-populate maze targets
        p, e = init_pellets_and_energizers(self.graph, maze_id)
        self.remaining_pellets.update(p)
        self.remaining_energizers.update(e)
            
        feats, self.prev_p = extract_strategic_features(
            obs, self.graph, self.prev_p, self.remaining_pellets, self.remaining_energizers, self.visited_nodes, self.prev_ghosts_pos
        )
        return feats, info

    def step(self, strategy_id):
        # Translate strategy_id to low level cardinal action (1-4)
        low_level_action = heuristic_execute(
            strategy_id, self.last_raw_obs, self.graph, self.remaining_pellets, self.remaining_energizers, self.last_action
        )
        
        # Decode current raw variables for safety check
        px, py = int(self.last_raw_obs[10]), int(self.last_raw_obs[16])
        blue_timer = int(self.last_raw_obs[116])
        
        ghosts_pos = []
        ghosts_in_house = []
        is_blue = []
        for i in range(4):
            gx = int(self.last_raw_obs[6 + i])
            gy = int(self.last_raw_obs[12 + i])
            ghosts_pos.append((gx, gy))
            in_h = is_in_house(gx, gy)
            ghosts_in_house.append(in_h)
            is_blue.append((blue_timer > 0) and not in_h)
            
        # Verify proposing action safety using 3-step Lookahead Safety Filter
        if low_level_action in [1, 2, 3, 4] and check_action_safety(
            self.graph, px, py, low_level_action, ghosts_pos, self.prev_ghosts_pos, is_blue, ghosts_in_house
        ):
            actual_action = low_level_action
            action_overridden = False
        else:
            # Override with safest escape action (strategy 2)
            escape_action = heuristic_execute(
                2, self.last_raw_obs, self.graph, self.remaining_pellets, self.remaining_energizers, self.last_action
            )
            if escape_action in [1, 2, 3, 4]:
                actual_action = escape_action
            else:
                actual_action = low_level_action # fallback if escape itself is invalid
            action_overridden = (actual_action != low_level_action)
                
        # Take step in Gym environment
        obs, reward, terminated, truncated, info = self.env.step(actual_action)
        self.last_raw_obs = obs
        
        # Level transition detection
        level = int(obs[123]) >> 4
        if self.prev_level is not None and level != self.prev_level:
            maze_id = get_maze_id(level)
            self.graph = self.graphs[maze_id]
            self.visited_nodes.clear()
            self.remaining_pellets.clear()
            self.remaining_energizers.clear()
            p, e = init_pellets_and_energizers(self.graph, maze_id)
            self.remaining_pellets.update(p)
            self.remaining_energizers.update(e)
            self.prev_p = None
        self.prev_level = level
        
        # Reward shaping:
        # 1. Death penalty (extra lives decreased)
        curr_extra_lives = int(obs[123]) & 0x0F
        if curr_extra_lives < self.prev_extra_lives:
            reward -= 150.0
            self.prev_p = None  # Reset prev_p on death
        self.prev_extra_lives = curr_extra_lives
        
        # 2. Action masking override penalty
        if action_overridden:
            reward -= 20.0
        
        # 3. Step penalty to encourage quick eating
        reward -= 0.02
        
        # 4. Eating blue ghost bonus
        if reward in [200, 400, 800, 1600]:
            reward += 100.0
            
        # 5. Proximity warning (only for non-blue ghosts)
        px, py = int(obs[10]), int(obs[16])
        blue_timer = int(obs[116])
        if blue_timer == 0:
            min_dist = 999.0
            for i in range(4):
                if not is_blue[i] and not ghosts_in_house[i]:
                    dist = dijkstra_distance(self.graph, (px, py), ghosts_pos[i])
                    if dist < min_dist:
                        min_dist = dist
            if min_dist <= 8:
                reward -= 1.0  # Scaled warnings
            if min_dist <= 4:
                reward -= 3.0  # Scaled warnings
                
        # Extract next features
        self.prev_ghosts_pos = ghosts_pos
        self.last_action = actual_action
        
        feats, self.prev_p = extract_strategic_features(
            obs, self.graph, self.prev_p, self.remaining_pellets, self.remaining_energizers, self.visited_nodes, self.prev_ghosts_pos
        )
        return feats, reward, terminated, truncated, info

def main():
    print("Initializing environment...")
    # Wrap environment with custom wrapper class to output 34-dim strategic features
    env = make_vec_env(
        "ALE/MsPacman-v5",
        n_envs=N_ENVS,
        env_kwargs={"obs_type": "ram"},
        wrapper_class=PacmanStrategicWrapper,
    )

    model = ALGORITHM(
        POLICY,
        env,
        policy_kwargs=POLICY_KWARGS or None,
        verbose=1,
    )

    print(f"Training {ALGORITHM.__name__} for {TOTAL_TIMESTEPS:,} timesteps...")
    model.learn(total_timesteps=TOTAL_TIMESTEPS)
    model.save(SAVE_PATH)
    print(f"\nModel saved as {SAVE_PATH}.zip — ready to upload with run.py")
    env.close()

if __name__ == "__main__":
    main()
