"""
ML Arena — MsPacman SB3 Training Script with Option D Hierarchical Wrapper
"""

import ale_py
import gymnasium as gym
from collections import defaultdict
import numpy as np
import random
import pickle
import os
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import BaseCallback

from model import (
    ALGORITHM, POLICY, POLICY_KWARGS, SAVE_PATH, PPO_HYPERPARAMS,
    extract_strategic_features, heuristic_execute, check_action_safety, is_in_house, dijkstra_distance,
    load_prebuilt_graph, get_maze_id, init_pellets_and_energizers, align_coordinates_to_graph,
    MAZE_1_BASE64, MAZE_2_BASE64, MAZE_3_BASE64, MAZE_4_BASE64
)

gym.register_envs(ale_py)

# ═══ ✅ Tune training hyperparameters ══════════════════════════════
TOTAL_TIMESTEPS = 2_000_000 # 2M timesteps for PPO to converge
N_ENVS          = 4         # parallel environments for faster sampling
# ══════════════════════════════════════════════════════════════════

class EntropyDecayCallback(BaseCallback):
    """
    Custom callback to decay the entropy coefficient (ent_coef) linearly over training.
    """
    def __init__(self, initial_ent_coef: float, total_timesteps: int, verbose: int = 0):
        super().__init__(verbose)
        self.initial_ent_coef = initial_ent_coef
        self.total_timesteps = total_timesteps

    def _on_step(self) -> bool:
        # Calculate progress remaining (1.0 at start, 0.0 at end)
        progress = 1.0 - (self.num_timesteps / self.total_timesteps)
        self.model.ent_coef = max(self.initial_ent_coef * progress, 0.0)
        return True

class PacmanStrategicWrapper(gym.Wrapper):
    """
    Environment wrapper that exposes a Discrete(6) macro-action space
    and a 36-dimensional strategic feature observation space.
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
        
        self.num_steps_total = 0
        self.safety_margin = 12.0
        self.proximity_warning_8_triggered = False
        self.proximity_warning_4_triggered = False
        
        # Action space: 6 macro actions
        self.action_space = gym.spaces.Discrete(6)
        
        # Observation space: 44 dimensions (36 strategic + 2 fruit position + 6 RAM optimizations)
        self.observation_space = gym.spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(44,),
            dtype=np.float32
        )

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        
        # Automated starting level curriculum:
        # We want to fully unlock all 6 pickle levels by 60% of the training process.
        # Step interval is scaled dynamically based on TOTAL_TIMESTEPS and N_ENVS.
        step_interval = max(int((TOTAL_TIMESTEPS * 0.6) // (N_ENVS * 6)), 1000)
        max_level = min(self.num_steps_total // step_interval, 6)
        level = random.randint(0, max_level)
        
        if level > 0:
            scratch_path = os.path.dirname(os.path.abspath(__file__))
            state_file = os.path.join(scratch_path, "scratch", "data", f"level_{level}_state.pkl")
            if os.path.exists(state_file):
                try:
                    with open(state_file, "rb") as f:
                        s = pickle.load(f)
                    self.env.unwrapped.restore_state(s)
                    obs = np.array(self.env.unwrapped.ale.getRAM(), dtype=np.uint8)
                except Exception:
                    pass
                    
        self.prev_p = None
        self.prev_extra_lives = int(obs[123]) & 0x0F
        self.prev_level = int(obs[123]) >> 4
        self.last_raw_obs = obs
        self.prev_ghosts_pos = None
        self.last_action = 0
        
        self.proximity_warning_8_triggered = False
        self.proximity_warning_4_triggered = False
        
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

    def action_masks(self) -> np.ndarray:
        if self.last_raw_obs is None:
            return np.array([True, True, True, True, True, True], dtype=bool)
            
        px, py = int(self.last_raw_obs[10]), int(self.last_raw_obs[16])
        px, py = align_coordinates_to_graph(self.graph, px, py)
        blue_timer = int(self.last_raw_obs[116]) & 0x3F
        
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
            
        masks = []
        for strategy_id in range(6):
            low_level_action = heuristic_execute(
                strategy_id, self.last_raw_obs, self.graph, self.remaining_pellets, self.remaining_energizers, self.last_action
            )
            if low_level_action in [1, 2, 3, 4]:
                is_safe = check_action_safety(
                    self.graph, px, py, low_level_action, ghosts_pos, self.prev_ghosts_pos, is_blue, ghosts_in_house, safety_margin=self.safety_margin
                )
            else:
                is_safe = False
            masks.append(is_safe)
            
        # Ensure at least Strategy 2 (Escape) is active to prevent PPO collapse
        if not any(masks):
            masks[2] = True
            
        return np.array(masks, dtype=bool)

    def step(self, strategy_id):
        self.num_steps_total += 1
        
        # Dynamic Safety Margin Linear Decay:
        # 0 ~ 0.5M steps: 12.0
        # 0.5M ~ 1.5M steps: decay linearly from 12.0 to 7.0
        # 1.5M+ steps: lock at 7.0
        decay_start = 500000 // N_ENVS
        decay_end = 1500000 // N_ENVS
        if self.num_steps_total < decay_start:
            base_margin = 12.0
        elif self.num_steps_total < decay_end:
            frac = (self.num_steps_total - decay_start) / (decay_end - decay_start)
            base_margin = 12.0 - frac * 5.0
        else:
            base_margin = 7.0
            
        # Add level-based safety buffer (ghosts speed up in later levels)
        current_level = (int(self.last_raw_obs[123]) >> 4) if self.last_raw_obs is not None else 0
        level_buffer = min(current_level * 0.8, 4.0)
        self.safety_margin = base_margin + level_buffer
            
        # Translate strategy_id to low level cardinal action (1-4)
        low_level_action = heuristic_execute(
            strategy_id, self.last_raw_obs, self.graph, self.remaining_pellets, self.remaining_energizers, self.last_action
        )
        actual_action = low_level_action if low_level_action in [1, 2, 3, 4] else 0
        
        # Take step in Gym environment
        obs, reward, terminated, truncated, info = self.env.step(actual_action)
        self.last_raw_obs = obs
        
        # Decode current variables from the new observation
        px, py = int(obs[10]), int(obs[16])
        blue_timer = int(obs[116]) & 0x3F
        
        ghosts_pos = []
        ghosts_in_house = []
        is_blue = []
        for i in range(4):
            gx = int(obs[6 + i])
            gy = int(obs[12 + i])
            ghosts_pos.append((gx, gy))
            in_h = is_in_house(gx, gy)
            ghosts_in_house.append(in_h)
            is_blue.append((blue_timer > 0) and not in_h)
            
        # Level transition detection
        level = int(obs[123]) >> 4
        if self.prev_level is not None and level != self.prev_level:
            reward += 500.0  # Big Level Clear reward (increased from 150.0 to encourage clearing)
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
        # 1. Death penalty (extra lives decreased, increased from 150.0 to 500.0 to value lives above greedy scoring)
        curr_extra_lives = int(obs[123]) & 0x0F
        if curr_extra_lives < self.prev_extra_lives:
            reward -= 500.0
            self.prev_p = None  # Reset prev_p on death
        self.prev_extra_lives = curr_extra_lives
        
        # 2. Step penalty to encourage quick eating
        reward -= 0.02
        
        # 3. Eating blue ghost bonus (exponentially increasing consecutive reward)
        if reward == 200:
            reward += 100.0
        elif reward == 400:
            reward += 200.0
        elif reward == 800:
            reward += 400.0
        elif reward == 1600:
            reward += 800.0
            
        # 4. Proximity warning (only for non-blue ghosts, one-time cross trigger)
        if blue_timer == 0:
            aligned_px, aligned_py = align_coordinates_to_graph(self.graph, px, py)
            min_dist = 999.0
            for i in range(4):
                if not is_blue[i] and not ghosts_in_house[i]:
                    aligned_gx, aligned_gy = align_coordinates_to_graph(self.graph, ghosts_pos[i][0], ghosts_pos[i][1])
                    dist = dijkstra_distance(self.graph, (aligned_px, aligned_py), (aligned_gx, aligned_gy))
                    if dist < min_dist:
                        min_dist = dist
            
            # Trigger 8-pixel warning
            if min_dist <= 8.0:
                if not self.proximity_warning_8_triggered:
                    reward -= 1.0
                    self.proximity_warning_8_triggered = True
            else:
                self.proximity_warning_8_triggered = False
                
            # Trigger 4-pixel warning
            if min_dist <= 4.0:
                if not self.proximity_warning_4_triggered:
                    reward -= 3.0
                    self.proximity_warning_4_triggered = True
            else:
                self.proximity_warning_4_triggered = False
        else:
            self.proximity_warning_8_triggered = False
            self.proximity_warning_4_triggered = False
            
        # Extract next features
        self.prev_ghosts_pos = ghosts_pos
        self.last_action = actual_action
        
        feats, self.prev_p = extract_strategic_features(
            obs, self.graph, self.prev_p, self.remaining_pellets, self.remaining_energizers, self.visited_nodes, self.prev_ghosts_pos
        )
        return feats, reward, terminated, truncated, info

def main():
    print("Initializing environment...")
    # Wrap environment with custom wrapper class to output 36-dim strategic features
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
        **PPO_HYPERPARAMS
    )

    print(f"Training {ALGORITHM.__name__} for {TOTAL_TIMESTEPS:,} timesteps...")
    entropy_decay_callback = EntropyDecayCallback(
        initial_ent_coef=PPO_HYPERPARAMS.get("ent_coef", 0.015),
        total_timesteps=TOTAL_TIMESTEPS
    )
    model.learn(total_timesteps=TOTAL_TIMESTEPS, callback=entropy_decay_callback)
    model.save(SAVE_PATH)
    print(f"\nModel saved as {SAVE_PATH}.zip — ready to upload with run.py")
    env.close()

if __name__ == "__main__":
    main()
