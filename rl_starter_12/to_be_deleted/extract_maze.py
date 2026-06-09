"""
Extract the Ms. Pac-Man maze tile map by running the game and recording
all positions Pac-Man visits, building a connectivity graph.

Also verifies RAM[119] as "dots eaten" counter.
"""
import ale_py
import gymnasium as gym
import numpy as np
from collections import defaultdict
import json
import time

gym.register_envs(ale_py)

def run_exploration(num_episodes=50, max_steps=5000):
    """Run many episodes with semi-random movement to explore the maze."""
    env = gym.make("ALE/MsPacman-v5", obs_type="ram", render_mode=None)
    
    # Track all unique positions and their neighbors
    all_positions = set()
    graph = defaultdict(set)
    prev_pos = None
    
    # Also track dots eaten counter
    dots_eaten_log = []
    
    for ep in range(num_episodes):
        obs, info = env.reset()
        prev_pos = None
        ep_positions = set()
        
        for step in range(max_steps):
            px, py = int(obs[10]), int(obs[16])
            dots_eaten = int(obs[119])  # RAM[119] = dots eaten (from Data Crystal)
            
            # Record position
            all_positions.add((px, py))
            ep_positions.add((px, py))
            
            # Build connectivity graph
            if prev_pos is not None:
                ppx, ppy = prev_pos
                if (ppx, ppy) != (px, py):
                    dx = abs(px - ppx)
                    dy = abs(py - ppy)
                    # Check for warp tunnel
                    is_warp = (ppy == py) and ((ppx < 25 and px > 140) or (ppx > 140 and px < 25))
                    if (dx + dy) <= 15 or is_warp:
                        graph[(ppx, ppy)].add((px, py))
                        graph[(px, py)].add((ppx, ppy))
            
            prev_pos = (px, py)
            
            # Log dots eaten at reward events
            if step < 3 or (step > 0 and dots_eaten > 0):
                pass  # we'll log summary
            
            # Semi-intelligent exploration: prefer directions we haven't been
            # Use a mix of strategies to cover more of the maze
            if step % 100 < 20:
                action = 1  # UP for a while
            elif step % 100 < 40:
                action = 2  # RIGHT
            elif step % 100 < 60:
                action = 4  # DOWN
            elif step % 100 < 80:
                action = 3  # LEFT
            else:
                action = np.random.randint(1, 5)  # random cardinal
            
            obs, reward, terminated, truncated, info = env.step(action)
            
            if reward > 0 and len(dots_eaten_log) < 30:
                new_dots = int(obs[119])
                dots_eaten_log.append({
                    'ep': ep, 'step': step,
                    'reward': float(reward),
                    'dots_before': dots_eaten,
                    'dots_after': new_dots,
                    'pos': (px, py)
                })
            
            if terminated or truncated:
                break
        
        if (ep + 1) % 10 == 0:
            print(f"Episode {ep+1}/{num_episodes}: {len(all_positions)} unique positions, {len(graph)} graph nodes")
    
    env.close()
    return all_positions, graph, dots_eaten_log


def analyze_positions(positions):
    """Analyze the distribution of positions to find tile grid parameters."""
    xs = sorted(set(p[0] for p in positions))
    ys = sorted(set(p[1] for p in positions))
    
    print(f"\n=== Position Analysis ===")
    print(f"Total unique positions: {len(positions)}")
    print(f"Unique X values ({len(xs)}): {xs}")
    print(f"Unique Y values ({len(ys)}): {ys}")
    
    # Find X gaps (corridors vs walls)
    print(f"\n--- X value gaps ---")
    for i in range(1, len(xs)):
        gap = xs[i] - xs[i-1]
        if gap > 3:
            print(f"  Gap at X={xs[i-1]}→{xs[i]} (size {gap})")
    
    # Find Y gaps
    print(f"\n--- Y value gaps ---")
    for i in range(1, len(ys)):
        gap = ys[i] - ys[i-1]
        if gap > 3:
            print(f"  Gap at Y={ys[i-1]}→{ys[i]} (size {gap})")


def analyze_graph(graph):
    """Analyze the connectivity graph."""
    print(f"\n=== Graph Analysis ===")
    print(f"Total nodes: {len(graph)}")
    
    # Find junction nodes (3+ neighbors) and dead ends (1 neighbor)
    junctions = []
    dead_ends = []
    corridors = []
    
    for node, neighbors in graph.items():
        n = len(neighbors)
        if n >= 3:
            junctions.append((node, n))
        elif n == 1:
            dead_ends.append(node)
        else:
            corridors.append(node)
    
    print(f"Junctions (3+ neighbors): {len(junctions)}")
    print(f"Dead ends (1 neighbor): {len(dead_ends)}")
    print(f"Corridors (2 neighbors): {len(corridors)}")
    
    if junctions:
        print(f"\nFirst 20 junctions:")
        for node, n_count in sorted(junctions)[:20]:
            print(f"  ({node[0]:3d}, {node[1]:3d}) -> {n_count} neighbors: {sorted(graph[node])}")
    
    if dead_ends:
        print(f"\nDead ends:")
        for node in sorted(dead_ends)[:20]:
            print(f"  ({node[0]:3d}, {node[1]:3d}) -> neighbor: {list(graph[node])}")


def quantize_to_tiles(positions, graph):
    """Try to find a tile-level quantization that groups nearby pixel positions."""
    xs = sorted(set(p[0] for p in positions))
    ys = sorted(set(p[1] for p in positions))
    
    # Group X values into clusters (positions within 3 pixels are same tile column)
    x_clusters = []
    curr_cluster = [xs[0]]
    for i in range(1, len(xs)):
        if xs[i] - xs[i-1] <= 2:
            curr_cluster.append(xs[i])
        else:
            x_clusters.append(curr_cluster)
            curr_cluster = [xs[i]]
    x_clusters.append(curr_cluster)
    
    # Group Y values
    y_clusters = []
    curr_cluster = [ys[0]]
    for i in range(1, len(ys)):
        if ys[i] - ys[i-1] <= 2:
            curr_cluster.append(ys[i])
        else:
            y_clusters.append(curr_cluster)
            curr_cluster = [ys[i]]
    y_clusters.append(curr_cluster)
    
    print(f"\n=== Tile Quantization ===")
    print(f"X clusters ({len(x_clusters)}):")
    for i, c in enumerate(x_clusters):
        center = sum(c) / len(c)
        print(f"  Col {i:2d}: pixels {c[0]:3d}-{c[-1]:3d} (center={center:.1f}, width={c[-1]-c[0]+1})")
    
    print(f"\nY clusters ({len(y_clusters)}):")
    for i, c in enumerate(y_clusters):
        center = sum(c) / len(c)
        print(f"  Row {i:2d}: pixels {c[0]:3d}-{c[-1]:3d} (center={center:.1f}, height={c[-1]-c[0]+1})")
    
    # Build pixel-to-tile mapping
    x_to_col = {}
    for col_idx, cluster in enumerate(x_clusters):
        for x in cluster:
            x_to_col[x] = col_idx
    
    y_to_row = {}
    for row_idx, cluster in enumerate(y_clusters):
        for y in cluster:
            y_to_row[y] = row_idx
    
    # Build tile-level graph
    tile_graph = defaultdict(set)
    for (px, py), neighbors in graph.items():
        if px in x_to_col and py in y_to_row:
            tile = (x_to_col[px], y_to_row[py])
            for (nx, ny) in neighbors:
                if nx in x_to_col and ny in y_to_row:
                    ntile = (x_to_col[nx], y_to_row[ny])
                    if tile != ntile:
                        tile_graph[tile].add(ntile)
    
    print(f"\n=== Tile-Level Graph ===")
    print(f"Total tile nodes: {len(tile_graph)}")
    
    # Print tile adjacency
    for tile in sorted(tile_graph.keys()):
        neighbors = sorted(tile_graph[tile])
        print(f"  Tile ({tile[0]:2d},{tile[1]:2d}) -> {neighbors}")
    
    return x_clusters, y_clusters, tile_graph


if __name__ == "__main__":
    print("Starting maze extraction (50 episodes)...")
    start = time.time()
    positions, graph, dots_log = run_exploration(num_episodes=50, max_steps=5000)
    elapsed = time.time() - start
    print(f"\nExploration took {elapsed:.1f}s")
    
    # Dots eaten verification
    print(f"\n=== Dots Eaten (RAM[119]) Verification ===")
    for entry in dots_log[:20]:
        print(f"  Ep{entry['ep']} Step{entry['step']:4d}: reward={entry['reward']:6.1f} "
              f"dots {entry['dots_before']}->{entry['dots_after']} at {entry['pos']}")
    
    analyze_positions(positions)
    analyze_graph(graph)
    x_clusters, y_clusters, tile_graph = quantize_to_tiles(positions, graph)
    
    # Save results
    result = {
        'x_clusters': [list(c) for c in x_clusters],
        'y_clusters': [list(c) for c in y_clusters],
        'tile_graph': {f"{k[0]},{k[1]}": [list(v) for v in sorted(vs)] 
                       for k, vs in tile_graph.items()},
        'num_positions': len(positions),
        'num_graph_nodes': len(graph),
        'num_tile_nodes': len(tile_graph),
    }
    
    import os
    out_path = os.path.join(os.path.dirname(__file__), "maze_data.json")
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved maze data to {out_path}")
