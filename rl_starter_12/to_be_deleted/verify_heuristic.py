import ale_py
import gymnasium as gym
import numpy as np
from collections import defaultdict
import json
import os
import heapq

gym.register_envs(ale_py)

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collect_all_mazes import (
    get_neighbor_by_action, get_neighbor_fallback, get_action_to_neighbor,
    get_ghost_valid_moves, dijkstra_distance_map, get_dist_from_map, dijkstra_distance,
    dijkstra_from_pacman, dijkstra_closest_target, check_action_safety, is_in_house,
    init_pellets_and_energizers
)

def verify():
    json_path = "/Users/Shared/西洋棋代理人/rl_starter_12/scratch/complete_mazes.json"
    maze_graphs = {1: defaultdict(set), 2: defaultdict(set), 3: defaultdict(set), 4: defaultdict(set)}
    
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
            for m_id in [1, 2, 3, 4]:
                key = f"maze_{m_id}"
                if key in data:
                    for k_str, val in data[key].items():
                        kx, ky = map(int, k_str.split(","))
                        for vx, vy in val:
                            maze_graphs[m_id][(kx, ky)].add((vx, vy))
                            
    env = gym.make("ALE/MsPacman-v5", obs_type="ram")
    obs, info = env.reset()
    
    prev_p = None
    current_level = int(obs[123]) >> 4
    prev_extra_lives = int(obs[123]) & 0x0F
    prev_ghosts_pos = None
    
    remaining_pellets = set()
    remaining_energizers = set()
    visited_nodes = set()
    
    graph = maze_graphs[1] # Start with Maze 1
    
    # Pre-populate targets
    p, e = init_pellets_and_energizers(graph, 1)
    remaining_pellets.update(p)
    remaining_energizers.update(e)
    
    visited_nodes.add((int(obs[10]), int(obs[16])))
    
    step = 0
    last_action = 0
    total_score = 0
    
    print("Step | Pacman  | Action | Ghosts Pos / dists | Lives | Score | Rem Pellets")
    print("-" * 75)
    
    while True:
        px, py = int(obs[10]), int(obs[16])
        level = int(obs[123]) >> 4
        
        # Level transition check
        if level != current_level:
            print(f"Level Up {current_level} -> {level}!")
            current_level = level
            prev_p = None
            visited_nodes.clear()
            remaining_pellets.clear()
            remaining_energizers.clear()
            p, e = init_pellets_and_energizers(graph, 1)
            remaining_pellets.update(p)
            remaining_energizers.update(e)
            
        # connectivity graph dynamic learn
        new_nodes_discovered = []
        if prev_p is not None:
            ppx, ppy = prev_p
            if (ppx, ppy) != (px, py):
                dist = abs(px - ppx) + abs(py - ppy)
                is_warp = (ppy == py) and ((ppx < 25 and px > 140) or (ppx > 140 and px < 25))
                if dist <= 15 or is_warp:
                    if (px, py) not in graph:
                        new_nodes_discovered.append((px, py))
                    if (ppx, ppy) not in graph:
                        new_nodes_discovered.append((ppx, ppy))
                    graph[(ppx, ppy)].add((px, py))
                    graph[(px, py)].add((ppx, ppy))
                    
        # Add new discovered pellets
        for node in new_nodes_discovered:
            x, y = node[0], node[1]
            in_h = is_in_house(x, y)
            in_tunnel = (72 <= y <= 88) and (x < 25 or x > 140)
            if not in_h and not in_tunnel and node not in visited_nodes:
                remaining_pellets.add(node)
                
        visited_nodes.add((px, py))
        
        # Discard eaten
        for node in list(remaining_pellets):
            if abs(px - node[0]) + abs(py - node[1]) <= 3:
                remaining_pellets.discard(node)
                
        # Death reset logic
        curr_extra_lives = int(obs[123]) & 0x0F
        if curr_extra_lives < prev_extra_lives:
            prev_p = None
        prev_extra_lives = curr_extra_lives
        
        prev_p = (px, py)
        
        blue_timer = int(obs[116])
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
            
        pacman_paths = dijkstra_from_pacman(graph, (px, py))
        
        # Find distance to closest non-blue active ghost
        min_non_blue_dist = 9999.0
        for i in range(4):
            if not is_blue[i] and not ghosts_in_house[i]:
                d = dijkstra_distance(graph, (px, py), ghosts_pos[i])
                if d < min_non_blue_dist:
                    min_non_blue_dist = d
                    
        strategy_id = 0
        if min_non_blue_dist <= 24.0:
            strategy_id = 2
        else:
            blue_ghosts = {ghosts_pos[i] for i in range(4) if is_blue[i]}
            if blue_ghosts:
                closest_bg, dist, next_node = dijkstra_closest_target(pacman_paths, blue_ghosts, (px, py))
                if closest_bg is not None and blue_timer > dist / 1.2 * 4:
                    strategy_id = 3
                    
        # Heuristic execution
        def action_to_targets(targets):
            if not targets:
                return 0
            _, _, next_node = dijkstra_closest_target(pacman_paths, targets, (px, py))
            if next_node is not None:
                return get_action_to_neighbor(px, py, next_node[0], next_node[1])
            return 0
            
        proposed_action = 0
        if strategy_id == 3:
            blue_ghosts = {ghosts_pos[i] for i in range(4) if is_blue[i]}
            _, dist, next_node = dijkstra_closest_target(pacman_paths, blue_ghosts, (px, py))
            if next_node is not None:
                proposed_action = get_action_to_neighbor(px, py, next_node[0], next_node[1])
        elif strategy_id == 2:
            best_a = 0
            max_safety = -9999.0
            ghost_dist_maps = [dijkstra_distance_map(graph, g) for g in ghosts_pos]
            OPPOSITE_ACTIONS = {1: 4, 2: 3, 3: 2, 4: 1}
            for a in [1, 2, 3, 4]:
                neighbor = get_neighbor_by_action(graph, px, py, a)
                if neighbor is not None:
                    min_g_dist = 9999.0
                    for i, g_pos in enumerate(ghosts_pos):
                        if not is_blue[i] and not ghosts_in_house[i]:
                            d = get_dist_from_map(ghost_dist_maps[i], neighbor, g_pos)
                            if d < min_g_dist:
                                min_g_dist = d
                    score = min_g_dist
                    if min_g_dist > 24.0 and last_action > 0:
                        if a == last_action:
                            score += 5.0
                        elif a == OPPOSITE_ACTIONS.get(last_action):
                            score -= 5.0
                    if score > max_safety:
                        max_safety = score
                        best_a = a
            proposed_action = best_a
            
        if proposed_action == 0:
            unvisited = {node for node in graph if node not in visited_nodes}
            if unvisited:
                proposed_action = action_to_targets(unvisited)
            else:
                proposed_action = action_to_targets(remaining_pellets)
                
        if proposed_action == 0:
            proposed_action = np.random.choice([1, 2, 3, 4])
            
        if check_action_safety(graph, px, py, proposed_action, ghosts_pos, prev_ghosts_pos, is_blue, ghosts_in_house):
            actual_action = proposed_action
            safety_override = False
        else:
            best_a = 0
            max_safety = -9999.0
            ghost_dist_maps = [dijkstra_distance_map(graph, g) for g in ghosts_pos]
            OPPOSITE_ACTIONS = {1: 4, 2: 3, 3: 2, 4: 1}
            for a in [1, 2, 3, 4]:
                neighbor = get_neighbor_by_action(graph, px, py, a)
                if neighbor is not None:
                    min_g_dist = 9999.0
                    for i, g_pos in enumerate(ghosts_pos):
                        if not is_blue[i] and not ghosts_in_house[i]:
                            d = get_dist_from_map(ghost_dist_maps[i], neighbor, g_pos)
                            if d < min_g_dist:
                                min_g_dist = d
                    score = min_g_dist
                    if min_g_dist > 24.0 and last_action > 0:
                        if a == last_action:
                            score += 5.0
                        elif a == OPPOSITE_ACTIONS.get(last_action):
                            score -= 5.0
                    if score > max_safety:
                        max_safety = score
                        best_a = a
            actual_action = best_a if best_a != 0 else proposed_action
            safety_override = (actual_action != proposed_action)
            
        obs, reward, terminated, truncated, info = env.step(actual_action)
        total_score += reward
        
        # Print info every 10 steps
        if step % 20 == 0:
            g_infos = []
            for i, g_pos in enumerate(ghosts_pos):
                if not is_blue[i] and not ghosts_in_house[i]:
                    d = dijkstra_distance(graph, (px, py), g_pos)
                    g_infos.append(f"G{i}:{g_pos}(d={d:.0f})")
            g_str = ", ".join(g_infos)
            override_str = " (OVERRIDE)" if safety_override else ""
            print(f"{step:4d} | ({px:3d},{py:3d}) | Act: {actual_action}{override_str} | {g_str:<30} | {curr_extra_lives} | {total_score:.0f} | {len(remaining_pellets)}")
            
        prev_ghosts_pos = ghosts_pos
        last_action = actual_action
        step += 1
        
        if terminated or truncated:
            print(f"Episode finished! Steps: {step}, Final score: {total_score}")
            break
            
    env.close()

if __name__ == "__main__":
    verify()
