import json
from collections import defaultdict, deque

def analyze_connectivity():
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
                    merged[tuple(n)].add(node) # ensure bidirectional
        return merged

    maze_graphs = {
        1: merge_levels([0, 1]),
        2: merge_levels([2, 3]),
        3: merge_levels([4, 5]),
        4: merge_levels([6, 7]),
    }

    for m_id, graph in maze_graphs.items():
        print(f"\n=== Maze {m_id} Analysis ===")
        total_nodes = len(graph)
        print(f"Total Nodes: {total_nodes}")
        if total_nodes == 0:
            print("No nodes found.")
            continue
            
        # 1. Degree distribution
        deg_counts = defaultdict(int)
        deg_1_nodes = []
        deg_0_nodes = []
        for u, neighbors in graph.items():
            deg = len(neighbors)
            deg_counts[deg] += 1
            if deg == 1:
                deg_1_nodes.append(u)
            elif deg == 0:
                deg_0_nodes.append(u)
                
        print("Degree distribution:")
        for deg in sorted(deg_counts.keys()):
            print(f"  Degree {deg}: {deg_counts[deg]} nodes")
            
        # 2. Connected components
        visited = set()
        components = []
        
        for node in graph:
            if node not in visited:
                comp = []
                queue = deque([node])
                visited.add(node)
                while queue:
                    curr = queue.popleft()
                    comp.append(curr)
                    for nxt in graph[curr]:
                        if nxt not in visited:
                            visited.add(nxt)
                            queue.append(nxt)
                components.append(comp)
                
        components.sort(key=len, reverse=True)
        print(f"Number of Connected Components: {len(components)}")
        print(f"Component sizes: {[len(c) for c in components[:10]]}")
        
        # Detail smaller components (often disconnected single pixels or small loops)
        if len(components) > 1:
            print("Smaller components details:")
            for idx, comp in enumerate(components[1:], start=2):
                if len(comp) <= 10:
                    print(f"  Component {idx} (size {len(comp)}): {comp}")
                else:
                    print(f"  Component {idx} (size {len(comp)}): first 10 nodes: {comp[:10]}")

if __name__ == "__main__":
    analyze_connectivity()
