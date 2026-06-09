import ale_py
import gymnasium as gym
import numpy as np
from collections import defaultdict
import json
import os
import heapq

gym.register_envs(ale_py)

# ═══ Heuristic Helpers ═══════════════════════════════════════════════
def is_in_house(x, y):
    return (75 <= x <= 101) and (72 <= y <= 88)

def get_neighbor_by_action(graph, px, py, action):
    for nx, ny in graph[(px, py)]:
        if action == 3: # LEFT
            if px > 140 and nx < 25: return (nx, ny)
            if nx < px - 2 and abs(ny - py) < 5: return (nx, ny)
        elif action == 2: # RIGHT
            if px < 25 and nx > 140: return (nx, ny)
            if nx > px + 2 and abs(ny - py) < 5: return (nx, ny)
        elif action == 1: # UP
            if ny < py - 2 and abs(nx - px) < 5: return (nx, ny)
        elif action == 4: # DOWN
            if ny > py + 2 and abs(nx - px) < 5: return (nx, ny)
    return None

def get_neighbor_fallback(px, py, action):
    if action == 1: return (px, py - 3)
    if action == 2: return (px + 3, py)
    if action == 3: return (px - 3, py)
    if action == 4: return (px, py + 3)
    return None

def get_action_to_neighbor(px, py, nx, ny):
    if px > 140 and nx < 25: return 3
    if px < 25 and nx > 140: return 2
    if nx < px - 2 and abs(ny - py) < 5: return 3
    if nx > px + 2 and abs(ny - py) < 5: return 2
    if ny < py - 2 and abs(nx - px) < 5: return 1
    if ny > py + 2 and abs(nx - px) < 5: return 4
    return 0

def get_ghost_valid_moves(graph, gx, gy, prev_gx, prev_gy):
    neighbors = graph[(gx, gy)]
    if prev_gx is None or prev_gy is None:
        return neighbors
    dx = gx - prev_gx
    dy = gy - prev_gy
    if dx == 0 and dy == 0:
        return neighbors
    valid = set()
    for nx, ny in neighbors:
        if (dx > 0 and nx < gx - 2) or (dx < 0 and nx > gx + 2) or (dy > 0 and ny < gy - 2) or (dy < 0 and ny > gy + 2):
            continue
        valid.add((nx, ny))
    return valid if valid else neighbors

def dijkstra_distance_map(graph, start, max_dist=None):
    start = (int(start[0]), int(start[1]))
    dist_map = {start: 0.0}
    if start not in graph:
        return dist_map
    queue = [(0.0, start)]
    while queue:
        d, curr = heapq.heappop(queue)
        if max_dist is not None and d > max_dist:
            break
        if d > dist_map[curr]:
            continue
        for neighbor in graph[curr]:
            weight = float(abs(curr[0] - neighbor[0]) + abs(curr[1] - neighbor[1]))
            if weight > 20: # Warp tunnel
                weight = 4.0
            nd = d + weight
            if neighbor not in dist_map or nd < dist_map[neighbor]:
                dist_map[neighbor] = nd
                heapq.heappush(queue, (nd, neighbor))
    return dist_map

def get_dist_from_map(dist_map, target, start_pos):
    target = (int(target[0]), int(target[1]))
    if target in dist_map:
        return float(dist_map[target])
    return float(abs(start_pos[0] - target[0]) + abs(start_pos[1] - target[1]))

def dijkstra_distance(graph, start, target, max_dist=None):
    start = (int(start[0]), int(start[1]))
    target = (int(target[0]), int(target[1]))
    if start == target:
        return 0.0
    if start not in graph or target not in graph:
        return float(abs(start[0] - target[0]) + abs(start[1] - target[1]))
    dist_map = {start: 0.0}
    queue = [(0.0, start)]
    while queue:
        d, curr = heapq.heappop(queue)
        if curr == target:
            return d
        if max_dist is not None and d > max_dist:
            break
        if d > dist_map[curr]:
            continue
        for neighbor in graph[curr]:
            weight = float(abs(curr[0] - neighbor[0]) + abs(curr[1] - neighbor[1]))
            if weight > 20:
                weight = 4.0
            nd = d + weight
            if neighbor not in dist_map or nd < dist_map[neighbor]:
                dist_map[neighbor] = nd
                heapq.heappush(queue, (nd, neighbor))
    return float(abs(start[0] - target[0]) + abs(start[1] - target[1]))

def dijkstra_from_pacman(graph, start):
    start = (int(start[0]), int(start[1]))
    paths_map = {start: (0.0, start)}
    if start not in graph:
        return paths_map
    queue = [(0.0, start)]
    while queue:
        d, curr = heapq.heappop(queue)
        if d > paths_map[curr][0]:
            continue
        for neighbor in graph[curr]:
            weight = float(abs(curr[0] - neighbor[0]) + abs(curr[1] - neighbor[1]))
            if weight > 20:
                weight = 4.0
            nd = d + weight
            if neighbor not in paths_map or nd < paths_map[neighbor][0]:
                first_step = paths_map[curr][1] if curr != start else neighbor
                paths_map[neighbor] = (nd, first_step)
                heapq.heappush(queue, (nd, neighbor))
    return paths_map

def dijkstra_closest_target(paths_map, targets, start_pos):
    if not targets:
        return None, 9999.0, None
    reachable_targets = [t for t in targets if t in paths_map]
    if reachable_targets:
        closest = min(reachable_targets, key=lambda t: paths_map[t][0])
        dist, first_step = paths_map[closest]
        return closest, float(dist), first_step
    else:
        best_t = min(targets, key=lambda t: abs(start_pos[0]-t[0]) + abs(start_pos[1]-t[1]))
        dist = float(abs(start_pos[0]-best_t[0]) + abs(start_pos[1]-best_t[1]))
        return best_t, dist, None

def check_action_safety(graph, px, py, action, ghosts_pos, prev_ghosts_pos, is_blue, ghosts_in_house):
    P1 = get_neighbor_by_action(graph, px, py, action)
    active_ghost_indices = [i for i in range(4) if not is_blue[i] and not ghosts_in_house[i]]
    if not active_ghost_indices:
        return True
        
    if P1 is None:
        P1_est = get_neighbor_fallback(px, py, action)
        if P1_est is None:
            return False
        for i in active_ghost_indices:
            g = ghosts_pos[i]
            if abs(P1_est[0] - g[0]) + abs(P1_est[1] - g[1]) <= 12.0:
                return False
        return True
        
    SAFETY_MARGIN = 12.0
    
    # Precompute ghost potential states (cx, cy, px, py) at t=0, 1, 2, 3 to prevent reversal
    ghost_states_t = {0: []}
    for i in range(4):
        g = ghosts_pos[i]
        pg = prev_ghosts_pos[i] if prev_ghosts_pos else None
        ghost_states_t[0].append({(int(g[0]), int(g[1]), int(pg[0]) if pg else None, int(pg[1]) if pg else None)})
        
    for t in [1, 2, 3]:
        states_t = []
        for i in range(4):
            curr_states = ghost_states_t[t-1][i]
            next_states = set()
            for cx, cy, p_gx, p_gy in curr_states:
                valid_moves = get_ghost_valid_moves(graph, cx, cy, p_gx, p_gy)
                for nx, ny in valid_moves:
                    next_states.add((nx, ny, cx, cy))
            states_t.append(next_states)
        ghost_states_t[t] = states_t
        
    # Check t=1 safety at P1
    for i in active_ghost_indices:
        for gx, gy, _, _ in ghost_states_t[1][i]:
            d = dijkstra_distance(graph, P1, (gx, gy), max_dist=SAFETY_MARGIN)
            if d <= SAFETY_MARGIN:
                return False
                
    # Helper to check if a node is safe at step t (t=2, 3)
    def is_node_safe(node, t):
        for i in active_ghost_indices:
            for gx, gy, _, _ in ghost_states_t[t][i]:
                d = dijkstra_distance(graph, node, (gx, gy), max_dist=SAFETY_MARGIN)
                if d <= SAFETY_MARGIN:
                    return False
        return True

    for P2 in graph[P1]:
        if is_node_safe(P2, 2):
            for P3 in graph[P2]:
                if is_node_safe(P3, 3):
                    return True
    return False

# ═══ Targets Setup ═════════════════════════════════════════════════
def init_pellets_and_energizers(graph, maze_id):
    remaining_energizers = {(18, 14), (18, 146), (158, 14), (158, 146)}
    remaining_pellets = set()
    for node in graph:
        x, y = node[0], node[1]
        in_house = (70 <= x <= 106) and (68 <= y <= 92)
        in_tunnel = (68 <= y <= 92) and (x < 30 or x > 130)
        if not in_house and not in_tunnel:
            remaining_pellets.add(node)
    return remaining_pellets, remaining_energizers

# ═══ Main Collector ════════════════════════════════════════════════
def collect():
    json_path = "/Users/Shared/西洋棋代理人/rl_starter_12/scratch/data/complete_mazes.json"
    maze_graphs = {1: defaultdict(set), 2: defaultdict(set), 3: defaultdict(set), 4: defaultdict(set)}
    
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
                for m_id in [1, 2, 3, 4]:
                    key = f"maze_{m_id}"
                    if key in data:
                        for k_str, val in data[key].items():
                            kx, ky = map(int, k_str.split(","))
                            for vx, vy in val:
                                maze_graphs[m_id][(kx, ky)].add((vx, vy))
            print(f"Loaded existing graphs. Maze 1 nodes: {len(maze_graphs[1])}, Maze 2: {len(maze_graphs[2])}, Maze 3: {len(maze_graphs[3])}, Maze 4: {len(maze_graphs[4])}")
        except Exception as e:
            print(f"Could not load existing graphs: {e}")

    env = gym.make("ALE/MsPacman-v5", obs_type="ram")
    num_episodes = 200
    
    def get_maze_id(level):
        if level in [0, 1]: return 1
        elif level in [2, 3, 4]: return 2
        elif level in [5, 6, 7, 8]: return 3
        else: return 4

    print(f"Starting exploration of {num_episodes} episodes to map Maze 2-4...")
    
    for ep in range(num_episodes):
        obs, info = env.reset()
        prev_p = None
        current_level = int(obs[123]) >> 4
        prev_extra_lives = int(obs[123]) & 0x0F
        prev_ghosts_pos = None
        
        # Track dynamically remaining targets per episode
        remaining_pellets = set()
        remaining_energizers = set()
        visited_nodes = set()
        
        maze_id = get_maze_id(current_level)
        graph = maze_graphs[maze_id]
        
        # Pre-populate pellets and energizers from existing graph for current level
        p, e = init_pellets_and_energizers(graph, maze_id)
        remaining_pellets.update(p)
        remaining_energizers.update(e)
        
        visited_nodes.add((int(obs[10]), int(obs[16])))
        
        step = 0
        last_action = 0
        total_score = 0
        
        # Checkpoint History and death counters for Time Travel
        checkpoint_history = []
        consecutive_deaths = 0
        
        # Save initial checkpoint
        init_cp = (
            env.unwrapped.clone_state(),
            set(remaining_pellets),
            set(remaining_energizers),
            set(visited_nodes),
            prev_p,
            last_action,
            prev_extra_lives
        )
        checkpoint_history.append(init_cp)
        
        random_run_steps = 0
        
        while True:
            px, py = int(obs[10]), int(obs[16])
            level = int(obs[123]) >> 4
            
            # Live diagnostic print
            if step % 50 == 0:
                print(f"[Debug] Ep {ep+1}, Step {step}, Pacman ({px},{py}), Lives {prev_extra_lives}, Maze 1: {len(maze_graphs[1])}, Maze 2: {len(maze_graphs[2])}, Maze 3: {len(maze_graphs[3])}, Maze 4: {len(maze_graphs[4])}, Remaining: {len(remaining_pellets)}", flush=True)
            
            # Random run deadlock breaker
            if random_run_steps > 0:
                actual_action = np.random.choice([1, 2, 3, 4])
                obs, reward, terminated, truncated, info = env.step(actual_action)
                total_score += reward
                random_run_steps -= 1
                step += 1
                
                # Check for death even during random run
                curr_extra_lives = int(obs[123]) & 0x0F
                if curr_extra_lives < prev_extra_lives:
                    consecutive_deaths += 1
                    if consecutive_deaths >= 5 and len(checkpoint_history) > 1:
                        print(f"[TimeTravel] Death Loop Alert in Random Run! Popping latest checkpoint. History size: {len(checkpoint_history)}", flush=True)
                        checkpoint_history.pop()
                        consecutive_deaths = 0
                    
                    if checkpoint_history:
                        cp = checkpoint_history[-1]
                        env.unwrapped.restore_state(cp[0])
                        remaining_pellets = set(cp[1])
                        remaining_energizers = set(cp[2])
                        visited_nodes = set(cp[3])
                        prev_p = cp[4]
                        last_action = cp[5]
                        prev_extra_lives = cp[6]
                    random_run_steps = 50
                    obs = np.array(env.unwrapped.ale.getRAM(), dtype=np.uint8)
                    continue
                    
                prev_extra_lives = curr_extra_lives
                prev_p = (px, py)
                last_action = actual_action
                continue
            
            # Level transition check
            if level != current_level:
                print(f"Episode {ep+1}: Level Up {current_level} -> {level}!", flush=True)
                current_level = level
                maze_id = get_maze_id(current_level)
                graph = maze_graphs[maze_id]
                prev_p = None
                visited_nodes.clear()
                remaining_pellets.clear()
                remaining_energizers.clear()
                # Pre-populate targets for the new level
                p, e = init_pellets_and_energizers(graph, maze_id)
                remaining_pellets.update(p)
                remaining_energizers.update(e)
                
                # Auto-save immediately upon level transition
                checkpoint_history = []
                consecutive_deaths = 0
                checkpoint = (
                    env.unwrapped.clone_state(),
                    set(remaining_pellets),
                    set(remaining_energizers),
                    set(visited_nodes),
                    prev_p,
                    last_action,
                    prev_extra_lives
                )
                checkpoint_history.append(checkpoint)
                
                # Save graph immediately on level transition
                output = {}
                for m_id, g in maze_graphs.items():
                    output[f"maze_{m_id}"] = {f"{k[0]},{k[1]}": [list(v) for v in vs] for k, vs in g.items()}
                with open(json_path, 'w') as f:
                    json.dump(output, f, indent=2)
                print(f"[Save] Level transition. Saved graphs. Maze 1 nodes: {len(maze_graphs[1])}, Maze 2: {len(maze_graphs[2])}, Maze 3: {len(maze_graphs[3])}, Maze 4: {len(maze_graphs[4])}", flush=True)
            
            maze_id = get_maze_id(current_level)
            graph = maze_graphs[maze_id]
            
            # Record connectivity graph dynamically
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
            
            # Auto-connect warp tunnels
            for node in list(graph.keys()):
                if node[0] <= 20: # left entrance
                    for rx in [158, 157, 156]:
                        if (rx, node[1]) in graph:
                            graph[node].add((rx, node[1]))
                            graph[(rx, node[1])].add(node)
                            
            # Add new discovered pellets
            for node in new_nodes_discovered:
                x, y = node[0], node[1]
                in_h = is_in_house(x, y)
                in_tunnel = (72 <= y <= 88) and (x < 25 or x > 140)
                if not in_h and not in_tunnel and node not in visited_nodes:
                    remaining_pellets.add(node)
            
            visited_nodes.add((px, py))
            
            # Discard eaten pellets
            for node in list(remaining_pellets):
                if abs(px - node[0]) + abs(py - node[1]) <= 3:
                    remaining_pellets.discard(node)
                    
            # Ghost tracking
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
                
            # Auto-save Checkpoint every 50 steps if safe
            if step > 0 and step % 50 == 0:
                min_g_d = 9999.0
                for i in range(4):
                    if not is_blue[i] and not ghosts_in_house[i]:
                        d = dijkstra_distance(graph, (px, py), ghosts_pos[i])
                        if d < min_g_d:
                            min_g_d = d
                if min_g_d > 35.0: # Safe distance (35 pixels)
                    checkpoint = (
                        env.unwrapped.clone_state(),
                        set(remaining_pellets),
                        set(remaining_energizers),
                        set(visited_nodes),
                        prev_p,
                        last_action,
                        prev_extra_lives
                    )
                    checkpoint_history.append(checkpoint)
                    if len(checkpoint_history) > 5:
                        checkpoint_history.pop(0)
                    consecutive_deaths = 0
            
            # Decisions
            pacman_paths = dijkstra_from_pacman(graph, (px, py))
            
            # Choose macro strategy
            min_non_blue_dist = 9999.0
            for i in range(4):
                if not is_blue[i] and not ghosts_in_house[i]:
                    d = dijkstra_distance(graph, (px, py), ghosts_pos[i])
                    if d < min_non_blue_dist:
                        min_non_blue_dist = d
                        
            strategy_id = 0
            if min_non_blue_dist <= 24.0: # Close warning (24 pixels)
                strategy_id = 2 # Escape
            else:
                blue_ghosts = {ghosts_pos[i] for i in range(4) if is_blue[i]}
                if blue_ghosts:
                    closest_bg, dist, next_node = dijkstra_closest_target(pacman_paths, blue_ghosts, (px, py))
                    if closest_bg is not None and blue_timer > dist / 1.2 * 4: # speed adjusted timing guard
                        strategy_id = 3 # Chase blue
            
            # Heuristic Executor
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
                # Escape momentum
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
                                score += 5.0  # Momentum bonus in pixels
                            elif a == OPPOSITE_ACTIONS.get(last_action):
                                score -= 5.0
                        if score > max_safety:
                            max_safety = score
                            best_a = a
                proposed_action = best_a
            
            if proposed_action == 0:
                # Eat Pellets fallback
                unvisited = {node for node in graph if node not in visited_nodes}
                if unvisited:
                    proposed_action = action_to_targets(unvisited)
                else:
                    proposed_action = action_to_targets(remaining_pellets)
                    
            if proposed_action == 0:
                proposed_action = np.random.choice([1, 2, 3, 4])
                
            # Safety Filter Check
            if check_action_safety(graph, px, py, proposed_action, ghosts_pos, prev_ghosts_pos, is_blue, ghosts_in_house):
                actual_action = proposed_action
            else:
                # Escape override
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
                
            obs, reward, terminated, truncated, info = env.step(actual_action)
            total_score += reward
            
            # S/L Time travel restore on death
            curr_extra_lives = int(obs[123]) & 0x0F
            if curr_extra_lives < prev_extra_lives:
                consecutive_deaths += 1
                if consecutive_deaths >= 5 and len(checkpoint_history) > 1:
                    print(f"[TimeTravel] Death Loop Alert! Popping latest checkpoint. History size: {len(checkpoint_history)}", flush=True)
                    checkpoint_history.pop()
                    consecutive_deaths = 0
                
                if checkpoint_history:
                    cp = checkpoint_history[-1]
                    env.unwrapped.restore_state(cp[0])
                    remaining_pellets = set(cp[1])
                    remaining_energizers = set(cp[2])
                    visited_nodes = set(cp[3])
                    prev_p = cp[4]
                    last_action = cp[5]
                    prev_extra_lives = cp[6]
                random_run_steps = 50
                obs = np.array(env.unwrapped.ale.getRAM(), dtype=np.uint8)
                continue
                
            prev_extra_lives = curr_extra_lives
            prev_ghosts_pos = ghosts_pos
            last_action = actual_action
            prev_p = (px, py)
            step += 1
            
            # Save graphs dynamically every 200 steps
            if step > 0 and step % 200 == 0:
                output = {}
                for m_id, g in maze_graphs.items():
                    output[f"maze_{m_id}"] = {f"{k[0]},{k[1]}": [list(v) for v in vs] for k, vs in g.items()}
                with open(json_path, 'w') as f:
                    json.dump(output, f, indent=2)
                print(f"[Save] Step {step}. Saved graphs. Maze 1 nodes: {len(maze_graphs[1])}, Maze 2: {len(maze_graphs[2])}, Maze 3: {len(maze_graphs[3])}, Maze 4: {len(maze_graphs[4])}", flush=True)
            
            if terminated or truncated:
                break
                
        # Print episode stats and save incrementally every episode
        print(f"Episode {ep+1}/{num_episodes} finished. Steps: {step}, Score: {total_score:.0f}, Level: {current_level}, Maze 2 nodes: {len(maze_graphs[2])}, Maze 3: {len(maze_graphs[3])}, Maze 4: {len(maze_graphs[4])}", flush=True)
        
        output = {}
        for m_id, g in maze_graphs.items():
            output[f"maze_{m_id}"] = {f"{k[0]},{k[1]}": [list(v) for v in vs] for k, vs in g.items()}
        with open(json_path, 'w') as f:
            json.dump(output, f, indent=2)
                
    env.close()
    print("Exploration finished and saved.", flush=True)

if __name__ == "__main__":
    collect()
