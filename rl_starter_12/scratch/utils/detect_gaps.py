import json
import heapq
from collections import defaultdict

def detect_gaps():
    json_path = "/Users/Shared/西洋棋代理人/rl_starter_12/scratch/data/complete_levels.json"
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

    for m_id, graph in maze_graphs.items():
        print(f"\n=== Maze {m_id} Gap Detection ===")
        if len(graph) == 0:
            print("No nodes found.")
            continue
            
        nodes = list(graph.keys())
        
        # Group by Y to check horizontal lines
        y_groups = defaultdict(list)
        for x, y in nodes:
            y_groups[y].append(x)
            
        horiz_gaps = []
        for y, x_list in y_groups.items():
            x_list.sort()
            for i in range(len(x_list) - 1):
                x1, x2 = x_list[i], x_list[i+1]
                gap_size = x2 - x1
                if 1 < gap_size <= 5:
                    u = (x1, y)
                    v = (x2, y)
                    # Check if they are already connected
                    if v not in graph[u]:
                        d = dijkstra_dist(graph, u, v)
                        # If shortest path is long or inf, it's a real gap in the corridor
                        if d > gap_size:
                            horiz_gaps.append((u, v, gap_size, d))
                            
        # Group by X to check vertical lines
        x_groups = defaultdict(list)
        for x, y in nodes:
            x_groups[x].append(y)
            
        vert_gaps = []
        for x, y_list in x_groups.items():
            y_list.sort()
            for i in range(len(y_list) - 1):
                y1, y2 = y_list[i], y_list[i+1]
                gap_size = y2 - y1
                if 1 < gap_size <= 5:
                    u = (x, y1)
                    v = (x, y2)
                    if v not in graph[u]:
                        d = dijkstra_dist(graph, u, v)
                        if d > gap_size:
                            vert_gaps.append((u, v, gap_size, d))

        print(f"Detected {len(horiz_gaps)} Horizontal Gaps and {len(vert_gaps)} Vertical Gaps.")
        
        if horiz_gaps:
            print("Horizontal Gaps:")
            for u, v, sz, d in horiz_gaps[:10]:
                print(f"  {u} -> {v} (size: {sz}, graph dist: {d})")
            if len(horiz_gaps) > 10:
                print("  ...")
                
        if vert_gaps:
            print("Vertical Gaps:")
            for u, v, sz, d in vert_gaps[:10]:
                print(f"  {u} -> {v} (size: {sz}, graph dist: {d})")
            if len(vert_gaps) > 10:
                print("  ...")

if __name__ == "__main__":
    detect_gaps()
