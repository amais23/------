"""
ML Arena — Pacman Agent with Lookahead Safety Filter and Hierarchical Policy
"""

import os
from collections import defaultdict
import numpy as np

from model import (
    ALGORITHM, extract_strategic_features, heuristic_execute, check_action_safety, is_in_house
)

class Agent:
    def __init__(self):
        weights_path = os.path.join(os.path.dirname(__file__), "model.zip")
        self.model = ALGORITHM.load(weights_path, device="cpu")
        self._state = None
        self.prev_level = None
        
        # Load all pre-built graphs for Mazes 1-4
        from model import (
            load_prebuilt_graph, MAZE_1_BASE64, MAZE_2_BASE64, MAZE_3_BASE64, MAZE_4_BASE64
        )
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
        self.prev_extra_lives = None
        self.prev_ghosts_pos = None
        self.last_action = 0

    def reset(self, observation: np.ndarray):
        """Reset state at the start of each episode."""
        self._state = None
        self.prev_p = None
        self.prev_level = int(observation[123]) >> 4
        self.prev_extra_lives = int(observation[123]) & 0x0F
        self.prev_ghosts_pos = None
        self.last_action = 0
        
        from model import get_maze_id, init_pellets_and_energizers
        maze_id = get_maze_id(self.prev_level)
        self.graph = self.graphs[maze_id]
        
        self.visited_nodes.clear()
        self.remaining_pellets.clear()
        self.remaining_energizers.clear()
        
        p, e = init_pellets_and_energizers(self.graph, maze_id)
        self.remaining_pellets.update(p)
        self.remaining_energizers.update(e)

    def act(self, observation: np.ndarray, _action_space) -> int:
        """
        Extract strategic features, predict macro action with PPO,
        translate to cardinal moves, and apply lookahead safety filter.
        """
        level = int(observation[123]) >> 4
        if self.prev_level is not None and level != self.prev_level:
            from model import get_maze_id, init_pellets_and_energizers
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
        
        # Death reset logic
        curr_extra_lives = int(observation[123]) & 0x0F
        if self.prev_extra_lives is not None and curr_extra_lives < self.prev_extra_lives:
            self.prev_p = None
        self.prev_extra_lives = curr_extra_lives

        # 1. Extract strategic features
        feats, self.prev_p = extract_strategic_features(
            observation, self.graph, self.prev_p, self.remaining_pellets, self.remaining_energizers, self.visited_nodes, self.prev_ghosts_pos
        )
        
        # 2. Get PPO action prediction (strategy_id)
        strategy_id, self._state = self.model.predict(
            feats, state=self._state, deterministic=True
        )
        strategy_id = int(strategy_id)
        
        # 3. Translate strategy to low level cardinal action (1-4)
        low_level_action = heuristic_execute(
            strategy_id, observation, self.graph, self.remaining_pellets, self.remaining_energizers, self.last_action
        )
        
        # 4. Apply Safety Lookahead Filter
        px, py = int(observation[10]), int(observation[16])
        blue_timer = int(observation[116])
        
        ghosts_pos = []
        ghosts_in_house = []
        is_blue = []
        for i in range(4):
            gx = int(observation[6 + i])
            gy = int(observation[12 + i])
            ghosts_pos.append((gx, gy))
            in_h = is_in_house(gx, gy)
            ghosts_in_house.append(in_h)
            is_blue.append((blue_timer > 0) and not in_h)
            
        if low_level_action in [1, 2, 3, 4] and check_action_safety(
            self.graph, px, py, low_level_action, ghosts_pos, self.prev_ghosts_pos, is_blue, ghosts_in_house
        ):
            actual_action = low_level_action
        else:
            # Override with safest escape action (strategy 2)
            escape_action = heuristic_execute(
                2, observation, self.graph, self.remaining_pellets, self.remaining_energizers, self.last_action
            )
            if escape_action in [1, 2, 3, 4]:
                actual_action = escape_action
            else:
                actual_action = low_level_action # fallback if escape itself is invalid
                
        self.prev_ghosts_pos = ghosts_pos
        self.last_action = actual_action
        return actual_action
