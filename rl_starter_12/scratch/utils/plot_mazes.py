import json
import os
from collections import defaultdict
import matplotlib.pyplot as plt

def plot_mazes():
    json_path = "/Users/Shared/西洋棋代理人/rl_starter_12/scratch/data/complete_levels.json"
    artifact_dir = "/Users/sandbox1/.gemini/antigravity-ide/brain/4562e9f3-dc9b-41a5-87c7-0ead8fa390b9"
    
    with open(json_path, "r") as f:
        level_data = json.load(f)
        
    def merge_levels(levels):
        merged = defaultdict(set)
        for lvl in levels:
            key = f"level_{lvl}"
            g = level_data.get(key, {})
            for k, neighbors in g.items():
                node = tuple(map(int, k.split(",")))
                for n in neighbors:
                    merged[node].add(tuple(n))
                    merged[tuple(n)].add(node)
        return merged

    maze_graphs = {
        1: merge_levels([0, 1]),
        2: merge_levels([2, 3]),
        3: merge_levels([4, 5]),
        4: merge_levels([6, 7]),
    }

    # Manual Patch: Connect top-left corridor at Y=26 (connecting X from 34 to 42) in Maze 3
    for x in range(34, 42):
        u = (x, 26)
        v = (x+1, 26)
        maze_graphs[3][u].add(v)
        maze_graphs[3][v].add(u)

    # Define the color scheme (dark mode premium look)
    bg_color = "#0B0C10"
    node_color = "#66FCF1"
    edge_color = "#1F2833"
    healed_color = "#FF4C29"

    for m_id, graph in maze_graphs.items():
        if len(graph) == 0:
            print(f"Maze {m_id} has no nodes, skipping plot.")
            continue
            
        fig, ax = plt.subplots(figsize=(8, 9), facecolor=bg_color)
        ax.set_facecolor(bg_color)
        
        # Collect all pixel-level interpolated nodes along edges
        interpolated_nodes = set()
        for u, neighbors in graph.items():
            interpolated_nodes.add(u)
            for v in neighbors:
                dist = abs(u[0] - v[0]) + abs(u[1] - v[1])
                if dist > 30: # likely warp tunnel
                    continue
                # Linear interpolation
                dx = v[0] - u[0]
                dy = v[1] - u[1]
                steps = max(abs(dx), abs(dy))
                if steps > 0:
                    for s in range(steps + 1):
                        t = s / steps
                        rx = int(round(u[0] + t * dx))
                        ry = int(round(u[1] + t * dy))
                        interpolated_nodes.add((rx, ry))
        
        # Plot edges
        drawn_edges = set()
        for u, neighbors in graph.items():
            for v in neighbors:
                # Warp tunnel edges could be very long (across the screen), avoid drawing lines across
                dist = abs(u[0] - v[0]) + abs(u[1] - v[1])
                if dist > 30: # likely warp tunnel
                    continue
                    
                edge_key = tuple(sorted([u, v]))
                if edge_key not in drawn_edges:
                    ax.plot([u[0], v[0]], [u[1], v[1]], color=edge_color, alpha=0.6, linewidth=1.5, zorder=1)
                    drawn_edges.add(edge_key)
                    
        # Plot fully interpolated nodes
        xs = [n[0] for n in interpolated_nodes]
        ys = [n[1] for n in interpolated_nodes]
        ax.scatter(xs, ys, color=node_color, s=5, zorder=2, label="Corridor Node")
        
        # Highlight auto-healed edges for Maze 3 specifically
        if m_id == 3:
            u_healed = (34, 155)
            v_healed = (34, 158)
            # Draw a thick line for the healed edge
            ax.plot([u_healed[0], v_healed[0]], [u_healed[1], v_healed[1]], color=healed_color, linewidth=3.5, zorder=3, label="Auto-healed Link")
            # Highlight the two nodes in red
            ax.scatter([u_healed[0], v_healed[0]], [u_healed[1], v_healed[1]], color=healed_color, s=40, zorder=4)
            ax.legend(loc="upper right", facecolor=bg_color, edgecolor=node_color, labelcolor="white")

        # Invert Y axis because pixel coordinates go from top (0) to bottom
        ax.invert_yaxis()
        
        ax.set_title(f"Ms. Pac-Man Maze {m_id} Graph Map (Nodes: {len(graph)})", color="white", fontsize=14, pad=15)
        ax.set_xlabel("X coordinate (pixels)", color="white")
        ax.set_ylabel("Y coordinate (pixels)", color="white")
        
        # Style tick marks and grid
        ax.tick_params(colors="white")
        ax.spines['bottom'].set_color('#45A29E')
        ax.spines['top'].set_color('#45A29E')
        ax.spines['left'].set_color('#45A29E')
        ax.spines['right'].set_color('#45A29E')
        ax.grid(color='#1F2833', linestyle='--', linewidth=0.5, alpha=0.5)
        
        plt.tight_layout()
        save_path = os.path.join(artifact_dir, f"maze_{m_id}.png")
        plt.savefig(save_path, facecolor=bg_color, dpi=150)
        plt.close()
        print(f"Saved Maze {m_id} plot to {save_path}")

if __name__ == "__main__":
    plot_mazes()
