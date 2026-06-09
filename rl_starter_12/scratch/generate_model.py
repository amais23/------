import os
import json
import base64
import zlib

def interpolate_graph(graph_dict):
    from collections import defaultdict
    # 1. build a set-based tuple graph
    g = defaultdict(set)
    for u_str, neighbors in graph_dict.items():
        u = tuple(map(int, u_str.split(",")))
        for v in neighbors:
            v_t = tuple(v)
            g[u].add(v_t)
            g[v_t].add(u)
            
    # 2. collect edges
    edges = set()
    for u, neighbors in g.items():
        for v in neighbors:
            if u < v:
                edges.add((u, v))
                
    # 3. refine with interpolation
    refined_g = defaultdict(set)
    for u, v in edges:
        dist = abs(u[0] - v[0]) + abs(u[1] - v[1])
        if dist > 30: # warp tunnel
            refined_g[u].add(v)
            refined_g[v].add(u)
            continue
            
        dx = v[0] - u[0]
        dy = v[1] - u[1]
        steps = max(abs(dx), abs(dy))
        
        chain = []
        for s in range(steps + 1):
            t = s / steps
            rx = int(round(u[0] + t * dx))
            ry = int(round(u[1] + t * dy))
            chain.append((rx, ry))
            
        for i in range(len(chain) - 1):
            p1 = chain[i]
            p2 = chain[i+1]
            refined_g[p1].add(p2)
            refined_g[p2].add(p1)
            
    # 4. return as dict of lists
    return {f"{u[0]},{u[1]}": [list(v) for v in vs] for u, vs in refined_g.items()}

def compress_graph(graph_dict):
    data = bytearray()
    for k_str, neighbors in graph_dict.items():
        x, y = map(int, k_str.split(","))
        data.append(x)
        data.append(y)
        data.append(len(neighbors))
        for nx, ny in neighbors:
            data.append(nx)
            data.append(ny)
    compressed = zlib.compress(data)
    b64_str = base64.b64encode(compressed).decode("utf-8")
    return b64_str

def generate():
    json_path = "/Users/Shared/西洋棋代理人/rl_starter_12/scratch/data/complete_levels.json"
    model_path = "/Users/Shared/西洋棋代理人/rl_starter_12/model.py"
    
    with open(json_path, "r") as f:
        level_data = json.load(f)
        
    from collections import defaultdict
    import heapq

    def dijkstra_dist(graph, start, target):
        if start not in graph or target not in graph:
            return float('inf')
        queue = [(0.0, start)]
        distances = {start: 0.0}
        while queue:
            d, curr = heapq.heappop(queue)
            if curr == target:
                return d
            if d > distances[curr]:
                continue
            for neighbor in graph[curr]:
                weight = float(abs(curr[0] - neighbor[0]) + abs(curr[1] - neighbor[1]))
                if weight > 20: # warp tunnel threshold
                    weight = 4.0
                nd = d + weight
                if neighbor not in distances or nd < distances[neighbor]:
                    distances[neighbor] = nd
                    heapq.heappush(queue, (nd, neighbor))
        return distances.get(target, float('inf'))

    def merge_levels(levels):
        merged = {}
        for lvl in levels:
            key = f"level_{lvl}"
            g = level_data.get(key, {})
            for k, neighbors in g.items():
                if k not in merged:
                    merged[k] = set()
                for n in neighbors:
                    merged[k].add(tuple(n))
        
        # Convert to dict of sets of tuples
        graph = {}
        for k, ns in merged.items():
            u = tuple(map(int, k.split(",")))
            graph[u] = set(ns)
            
        # Ensure bidirectional and self-nodes
        for u in list(graph.keys()):
            for v in list(graph[u]):
                if v not in graph:
                    graph[v] = set()
                graph[v].add(u)
                
        # Auto-healing gaps (within 3 pixels)
        nodes = list(graph.keys())
        
        # Horizontal
        y_groups = defaultdict(list)
        for x, y in nodes:
            y_groups[y].append(x)
        for y, x_list in y_groups.items():
            x_list.sort()
            for i in range(len(x_list) - 1):
                x1, x2 = x_list[i], x_list[i+1]
                gap_size = x2 - x1
                if 1 < gap_size <= 3:
                    u = (x1, y)
                    v = (x2, y)
                    if v not in graph[u]:
                        d = dijkstra_dist(graph, u, v)
                        if d > gap_size + 5:
                            print(f"Auto-healing horizontal gap: {u} <-> {v} (size {gap_size}, dist {d})")
                            graph[u].add(v)
                            graph[v].add(u)
                            
        # Vertical
        x_groups = defaultdict(list)
        for x, y in nodes:
            x_groups[x].append(y)
        for x, y_list in x_groups.items():
            y_list.sort()
            for i in range(len(y_list) - 1):
                y1, y2 = y_list[i], y_list[i+1]
                gap_size = y2 - y1
                if 1 < gap_size <= 3:
                    u = (x, y1)
                    v = (x, y2)
                    if v not in graph[u]:
                        d = dijkstra_dist(graph, u, v)
                        if d > gap_size + 5:
                            print(f"Auto-healing vertical gap: {u} <-> {v} (size {gap_size}, dist {d})")
                            graph[u].add(v)
                            graph[v].add(u)
                            
        return {f"{u[0]},{u[1]}": [list(v) for v in vs] for u, vs in graph.items()}

    maze_graphs = {
        1: merge_levels([0, 1]),
        2: merge_levels([2, 3]),
        3: merge_levels([4, 5]),
        4: merge_levels([6, 7]),
    }
    
    # Manual Patch: Connect top-left corridor at Y=26 (connecting X from 34 to 42) in Maze 3
    for x in range(34, 42):
        u_str = f"{x},26"
        v_str = f"{x+1},26"
        if u_str not in maze_graphs[3]:
            maze_graphs[3][u_str] = []
        if v_str not in maze_graphs[3]:
            maze_graphs[3][v_str] = []
        if [x+1, 26] not in maze_graphs[3][u_str]:
            maze_graphs[3][u_str].append([x+1, 26])
        if [x, 26] not in maze_graphs[3][v_str]:
            maze_graphs[3][v_str].append([x, 26])
        
    # Interpolate all four mazes to fill intermediate pixels along corridors
    interpolated_graphs = {}
    for m_id in [1, 2, 3, 4]:
        interpolated_graphs[m_id] = interpolate_graph(maze_graphs[m_id])
        
    # Save the interpolated map to a dedicated JSON file as requested
    interpolated_json_path = "/Users/Shared/西洋棋代理人/rl_starter_12/scratch/data/complete_mazes_interpolated.json"
    with open(interpolated_json_path, "w") as f:
        json.dump({f"maze_{m_id}": g for m_id, g in interpolated_graphs.items()}, f, indent=2)
    print(f"Saved interpolated graphs to {interpolated_json_path}")
    
    # Overwrite maze_graphs to use the interpolated version for model compilation
    maze_graphs = interpolated_graphs

    maze_blocks = []
    for m_id in [1, 2, 3, 4]:
        graph_dict = maze_graphs[m_id]
        b64_str = compress_graph(graph_dict)
        
        # Chunk the base64 string
        chunk_size = 76
        formatted_chunks = []
        for i in range(0, len(b64_str), chunk_size):
            chunk = b64_str[i:i+chunk_size]
            formatted_chunks.append(f'    "{chunk}"')
            
        maze_blocks.append(f"MAZE_{m_id}_BASE64 = (\n" + "\n".join(formatted_chunks) + "\n)")
        
    all_maze_base64_block = "\n\n".join(maze_blocks)
    
    model_template = """\"\"\"
✅ The ONLY file you need to change to swap algorithms or network architecture.
Both train.py and agent.py import from here — change once, sync everywhere.
\"\"\"

from stable_baselines3 import PPO
import numpy as np
import base64
import zlib
import heapq
from collections import defaultdict

# ═══ Option D Hierarchical Configuration ═════════════════════════
ALGORITHM     = PPO           # SB3 algorithm class
POLICY        = "MlpPolicy"   # Use MLP policy on top of strategic features
POLICY_KWARGS = dict(          # Smaller architecture for macro-actions
    net_arch=dict(pi=[128, 128], vf=[128, 128])
)
SAVE_PATH     = "model"        # SB3 appends .zip
# ══════════════════════════════════════════════════════════════════

# Pre-built base64 encoded compressed graphs for Ms. Pacman Mazes 1-4
__BASE64__

def get_maze_id(level):
    \"\"\"Map 0-indexed RAM level to maze ID 1-4 (2 levels per maze, cycles every 8).\"\"\"
    return (level // 2) % 4 + 1

def load_prebuilt_graph(b64_str):
    \"\"\"Decompress base64 graph representation into adjacency set representation.\"\"\"
    graph = defaultdict(set)
    if not b64_str:
        return graph
    compressed = base64.b64decode(b64_str.encode("utf-8"))
    decompressed = zlib.decompress(compressed)
    
    idx = 0
    while idx < len(decompressed):
        x = decompressed[idx]
        y = decompressed[idx+1]
        n_count = decompressed[idx+2]
        idx += 3
        
        node = (x, y)
        for _ in range(n_count):
            nx = decompressed[idx]
            ny = decompressed[idx+1]
            idx += 2
            graph[node].add((nx, ny))
            
    return graph

def is_in_house(x, y):
    \"\"\"Check if Pacman or a ghost is inside the central ghost house.\"\"\"
    return (75 <= x <= 101) and (72 <= y <= 88)

def get_neighbor_by_action(graph, px, py, action):
    \"\"\"Get the coordinates of the neighbor node in the graph if taking a cardinal action.\"\"\"
    for nx, ny in graph[(px, py)]:
        # Warp-around checks
        if action == 3: # LEFT
            if px > 140 and nx < 25:
                return (nx, ny)
            if nx < px - 2 and abs(ny - py) < 5:
                return (nx, ny)
        elif action == 2: # RIGHT
            if px < 25 and nx > 140:
                return (nx, ny)
            if nx > px + 2 and abs(ny - py) < 5:
                return (nx, ny)
        elif action == 1: # UP
            if ny < py - 2 and abs(nx - px) < 5:
                return (nx, ny)
        elif action == 4: # DOWN
            if ny > py + 2 and abs(nx - px) < 5:
                return (nx, ny)
    return None

def get_neighbor_fallback(px, py, action):
    \"\"\"Estimate neighbor coordinate when it's not yet recorded in the graph.\"\"\"
    if action == 1: return (px, py - 3) # UP
    if action == 2: return (px + 3, py) # RIGHT
    if action == 3: return (px - 3, py) # LEFT
    if action == 4: return (px, py + 3) # DOWN
    return None

def get_action_to_neighbor(px, py, nx, ny):
    \"\"\"Find the action (1-4) that moves Pacman from (px, py) to neighbor (nx, ny).\"\"\"
    # Warp checks
    if px > 140 and nx < 25:
        return 3 # LEFT
    if px < 25 and nx > 140:
        return 2 # RIGHT
        
    # Cardinal checks
    if nx < px - 2 and abs(ny - py) < 5:
        return 3 # LEFT
    if nx > px + 2 and abs(ny - py) < 5:
        return 2 # RIGHT
    if ny < py - 2 and abs(nx - px) < 5:
        return 1 # UP
    if ny > py + 2 and abs(nx - px) < 5:
        return 4 # DOWN
    return 0

def get_ghost_valid_moves(graph, gx, gy, prev_gx, prev_gy):
    \"\"\"Get valid ghost moves excluding 180-degree reversal if heading is known.\"\"\"
    neighbors = graph[(gx, gy)]
    if prev_gx is None or prev_gy is None:
        return neighbors
    dx = gx - prev_gx
    dy = gy - prev_gy
    if dx == 0 and dy == 0:
        return neighbors
    valid = set()
    for nx, ny in neighbors:
        # Avoid reversal
        if (dx > 0 and nx < gx - 2) or (dx < 0 and nx > gx + 2) or (dy > 0 and ny < gy - 2) or (dy < 0 and ny > gy + 2):
            continue
        valid.add((nx, ny))
    return valid if valid else neighbors

def dijkstra_distance_map(graph, start, max_dist=None):
    \"\"\"Compute shortest path distance in physical pixels from start to all reachable nodes.\"\"\"
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
            if weight > 20: # Warp tunnel threshold
                weight = 4.0
            nd = d + weight
            if neighbor not in dist_map or nd < dist_map[neighbor]:
                dist_map[neighbor] = nd
                heapq.heappush(queue, (nd, neighbor))
    return dist_map

def get_dist_from_map(dist_map, target, start_pos):
    \"\"\"Look up Dijkstra distance from map, fallback to Manhattan distance.\"\"\"
    target = (int(target[0]), int(target[1]))
    if target in dist_map:
        return float(dist_map[target])
    return float(abs(start_pos[0] - target[0]) + abs(start_pos[1] - target[1]))

def dijkstra_distance(graph, start, target, max_dist=None):
    \"\"\"Calculate shortest path distance in pixels, fallback to Manhattan.\"\"\"
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
    \"\"\"
    Compute shortest path distance and first-step neighbor node using Dijkstra (pixel weights).
    Returns: { node: (distance, first_step_neighbor) }
    \"\"\"
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
    \"\"\"Find the closest target in the set of targets using precomputed paths_map.\"\"\"
    if not targets:
        return None, 9999.0, None
    reachable_targets = [t for t in targets if t in paths_map]
    if reachable_targets:
        closest = min(reachable_targets, key=lambda t: paths_map[t][0])
        dist, first_step = paths_map[closest]
        return closest, float(dist), first_step
    else:
        # Fallback to Manhattan distance
        best_t = min(targets, key=lambda t: abs(start_pos[0]-t[0]) + abs(start_pos[1]-t[1]))
        dist = float(abs(start_pos[0]-best_t[0]) + abs(start_pos[1]-best_t[1]))
        return best_t, dist, None

def init_pellets_and_energizers(graph, maze_id):
    \"\"\"Initialize pellets and energizer coordinates based on the loaded maze graph.\"\"\"
    remaining_energizers = {(18, 14), (18, 146), (158, 14), (158, 146)}
    remaining_pellets = set()
    for node in graph:
        x, y = node[0], node[1]
        in_house = (75 <= x <= 101) and (72 <= y <= 88)
        in_tunnel = (72 <= y <= 88) and (x < 25 or x > 140)
        if not in_house and not in_tunnel:
            remaining_pellets.add(node)
    return remaining_pellets, remaining_energizers

def update_dynamic_graph_and_targets(px, py, prev_p, level, graph, remaining_pellets, remaining_energizers, visited_nodes):
    \"\"\"Dynamically update connectivity graph and track eaten pellets/energizers.\"\"\"
    # Learn graph connectivity dynamically (just in case)
    new_nodes_discovered = []
    if prev_p is not None:
        ppx, ppy = int(prev_p[0]), int(prev_p[1])
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
                
    # Maze 2+ dynamic pellet discovery
    if level >= 2:
        for node in new_nodes_discovered:
            x, y = node[0], node[1]
            in_house = (75 <= x <= 101) and (72 <= y <= 88)
            in_tunnel = (72 <= y <= 88) and (x < 25 or x > 140)
            if not in_house and not in_tunnel and node not in visited_nodes:
                remaining_pellets.add(node)
                
    visited_nodes.add((px, py))
    
    # Auto-connect warp tunnels dynamically
    for node in list(graph.keys()):
        if node[0] <= 20: # left entrance
            for rx in [158, 157, 156]:
                if (rx, node[1]) in graph:
                    graph[node].add((rx, node[1]))
                    graph[(rx, node[1])].add(node)
                    
    # Remove nodes close to Pacman from target sets
    for node in list(remaining_pellets):
        if abs(px - node[0]) + abs(py - node[1]) <= 3:
            remaining_pellets.discard(node)
            
    for node in list(remaining_energizers):
        if abs(px - node[0]) + abs(py - node[1]) <= 5:
            remaining_energizers.discard(node)

def extract_strategic_features(obs, graph, prev_p, remaining_pellets, remaining_energizers, visited_nodes, prev_ghosts_pos):
    \"\"\"Extract a highly strategic 34-dimensional feature vector for macro actions.\"\"\"
    px, py = int(obs[10]), int(obs[16])
    level = int(obs[123]) >> 4
    
    update_dynamic_graph_and_targets(px, py, prev_p, level, graph, remaining_pellets, remaining_energizers, visited_nodes)
    
    # Precompute distance maps
    pacman_paths = dijkstra_from_pacman(graph, (px, py))
    
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
        
    ghost_dist_maps = [dijkstra_distance_map(graph, g) for g in ghosts_pos]
    
    features = []
    
    # 1, 2: Normalized Pacman position
    features.append(px / 160.0)
    features.append(py / 160.0)
    
    # 3-6: Normalized ghost distances
    ghost_dists = []
    for i, g_pos in enumerate(ghosts_pos):
        d = get_dist_from_map(ghost_dist_maps[i], (px, py), g_pos)
        ghost_dists.append(d)
        features.append(min(d / 150.0, 1.0)) # Scaled by physical screen width
        
    # 7-14: Normalized ghost relative directions
    for i, g_pos in enumerate(ghosts_pos):
        dx = g_pos[0] - px
        dy = g_pos[1] - py
        dist = abs(dx) + abs(dy)
        if dist > 0:
            features.append(dx / dist)
            features.append(dy / dist)
        else:
            features.append(0.0)
            features.append(0.0)
            
    # 15: Distance to closest active non-blue ghost
    min_non_blue_dist = 9999.0
    for i, d in enumerate(ghost_dists):
        if not is_blue[i] and not ghosts_in_house[i]:
            if d < min_non_blue_dist:
                min_non_blue_dist = d
    features.append(min(min_non_blue_dist / 150.0, 1.0))
    
    # 16: Blue timer
    features.append(blue_timer / 255.0)
    
    # 17: Closest remaining pellet distance
    _, pellet_dist, _ = dijkstra_closest_target(pacman_paths, remaining_pellets, (px, py))
    features.append(min(pellet_dist / 150.0, 1.0))
    
    # 18: Closest remaining energizer distance
    _, energizer_dist, _ = dijkstra_closest_target(pacman_paths, remaining_energizers, (px, py))
    features.append(min(energizer_dist / 150.0, 1.0))
    
    # 19: Remaining energizers ratio
    features.append(len(remaining_energizers) / 4.0)
    
    # 20: Remaining pellets ratio
    features.append(min(len(remaining_pellets) / 1645.0, 1.0))
    
    # 21: Lives
    lives = int(obs[123]) & 0x0F
    features.append(lives / 5.0)
    
    # 22: Level
    features.append(level / 10.0)
    
    # 23-26: Direction safety (UP, RIGHT, LEFT, DOWN)
    for a in [1, 2, 3, 4]:
        neighbor = get_neighbor_by_action(graph, px, py, a)
        if neighbor is not None:
            min_g_d = 9999.0
            for i, g_pos in enumerate(ghosts_pos):
                if not is_blue[i] and not ghosts_in_house[i]:
                    d = get_dist_from_map(ghost_dist_maps[i], neighbor, g_pos)
                    if d < min_g_d:
                        min_g_d = d
            features.append(min(min_g_d / 150.0, 1.0))
        else:
            features.append(0.0)
            
    # 27: Is in dead end
    features.append(float(len(graph[(px, py)]) <= 1))
    
    # 28-31: Ghosts in house
    for in_h in ghosts_in_house:
        features.append(float(in_h))
        
    # 32: Pacman in house
    features.append(float(is_in_house(px, py)))
    
    # 33: Closest blue ghost distance
    min_blue_dist = 9999.0
    for i, d in enumerate(ghost_dists):
        if is_blue[i]:
            if d < min_blue_dist:
                min_blue_dist = d
    features.append(min(min_blue_dist / 150.0, 1.0))
    
    # 34: Number of active blue ghosts
    num_blue = sum(1 for b in is_blue if b)
    features.append(num_blue / 4.0)
    
    return np.array(features, dtype=np.float32), (px, py)

OPPOSITE_ACTIONS = {1: 4, 2: 3, 3: 2, 4: 1}

def heuristic_execute(strategy_id, obs, graph, remaining_pellets, remaining_energizers, prev_action=0):
    \"\"\"Translate high level strategy to cardinal action (1-4) or fallback (0).\"\"\"
    px, py = int(obs[10]), int(obs[16])
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
    
    def action_to_targets(targets):
        if not targets:
            return 0
        _, _, next_node = dijkstra_closest_target(pacman_paths, targets, (px, py))
        if next_node is not None:
            return get_action_to_neighbor(px, py, next_node[0], next_node[1])
        return 0

    if strategy_id == 0:  # Eat Pellet
        return action_to_targets(remaining_pellets)
        
    elif strategy_id == 1:  # Eat Energizer
        act = action_to_targets(remaining_energizers)
        if act != 0:
            return act
        return action_to_targets(remaining_pellets)
        
    elif strategy_id == 2:  # Escape (with direction momentum)
        best_a = 0
        max_safety = -9999.0
        ghost_dist_maps = [dijkstra_distance_map(graph, g) for g in ghosts_pos]
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
                # Direction momentum bonus (expressed in equivalent pixels)
                if prev_action > 0:
                    if a == prev_action:
                        score += 5.0
                    elif a == OPPOSITE_ACTIONS.get(prev_action):
                        score -= 5.0
                if score > max_safety:
                    max_safety = score
                    best_a = a
        if best_a != 0:
            return best_a
        return action_to_targets(remaining_pellets)
        
    elif strategy_id == 3:  # Chase Blue (with timing guard)
        blue_ghosts = {ghosts_pos[i] for i in range(4) if is_blue[i]}
        if blue_ghosts:
            closest_bg, dist, next_node = dijkstra_closest_target(pacman_paths, blue_ghosts, (px, py))
            # Speed safety timer guard: blue_timer > dist_in_pixels * 1.25
            if closest_bg is not None and blue_timer > dist * 1.25:
                if next_node is not None:
                    return get_action_to_neighbor(px, py, next_node[0], next_node[1])
        return action_to_targets(remaining_pellets)
        
    elif strategy_id == 4:  # Wait/Lure
        closest_e, dist, next_node = dijkstra_closest_target(pacman_paths, remaining_energizers, (px, py))
        if closest_e is not None:
            if dist > 15.0: # pixel distance > 15
                if next_node is not None:
                    return get_action_to_neighbor(px, py, next_node[0], next_node[1])
            else:
                # Close to energizer
                min_ghost_dist = 9999.0
                ghost_dist_maps = [dijkstra_distance_map(graph, g) for g in ghosts_pos]
                for i, g_pos in enumerate(ghosts_pos):
                    if not is_blue[i] and not ghosts_in_house[i]:
                        d = get_dist_from_map(ghost_dist_maps[i], (px, py), g_pos)
                        if d < min_ghost_dist:
                            min_ghost_dist = d
                if min_ghost_dist <= 30.0: # ghost within 30 pixels
                    if next_node is not None:
                        return get_action_to_neighbor(px, py, next_node[0], next_node[1])
                else:
                    # Patrol/Wait: move away from energizer
                    for neighbor in graph[(px, py)]:
                        if neighbor != closest_e:
                            return get_action_to_neighbor(px, py, neighbor[0], neighbor[1])
                    if next_node is not None:
                        return get_action_to_neighbor(px, py, next_node[0], next_node[1])
        return action_to_targets(remaining_pellets)

    return 0

def check_action_safety(graph, px, py, action, ghosts_pos, prev_ghosts_pos, is_blue, ghosts_in_house):
    \"\"\"Lookahead 3-step Safety Filter with Ghost Momentum prediction and Safety Margin (Pixel distance).\"\"\"
    P1 = get_neighbor_by_action(graph, px, py, action)
    active_ghost_indices = [i for i in range(4) if not is_blue[i] and not ghosts_in_house[i]]
    if not active_ghost_indices:
        return True
        
    # Manhattan safety fallback
    if P1 is None:
        P1_est = get_neighbor_fallback(px, py, action)
        if P1_est is None:
            return False
        for i in active_ghost_indices:
            g = ghosts_pos[i]
            if abs(P1_est[0] - g[0]) + abs(P1_est[1] - g[1]) <= 12.0:
                return False
        return True
        
    SAFETY_MARGIN = 12.0 # minimum buffer in pixels
    
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

    # Search for any safe path of length 3 (P1 -> P2 -> P3)
    for P2 in graph[P1]:
        if is_node_safe(P2, 2):
            for P3 in graph[P2]:
                if is_node_safe(P3, 3):
                    return True
                    
    return False
"""
    model_content = model_template.replace("__BASE64__", all_maze_base64_block)
    
    with open(model_path, "w") as f:
        f.write(model_content)
    print("Wrote model.py successfully!")

if __name__ == "__main__":
    generate()
