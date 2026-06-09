import json
import os

def visualize():
    json_path = "/Users/Shared/西洋棋代理人/rl_starter_12/scratch/data/complete_levels.json"
    artifact_path = "/Users/sandbox1/.gemini/antigravity-ide/brain/4562e9f3-dc9b-41a5-87c7-0ead8fa390b9/maze_visualization.md"
    
    if not os.path.exists(json_path):
        print("complete_levels.json not found!")
        return

    with open(json_path, "r") as f:
        level_data = json.load(f)
        
    def merge_levels(levels):
        merged = set()
        for lvl in levels:
            key = f"level_{lvl}"
            g = level_data.get(key, {})
            for k in g.keys():
                x, y = map(int, k.split(","))
                merged.add((x, y))
        return merged

    maze_graphs = {
        1: merge_levels([0, 1]),
        2: merge_levels([2, 3]),
        3: merge_levels([4, 5]),
        4: merge_levels([6, 7]),
    }

    # Manual Patch: Add top-left corridor at Y=26 (connecting X from 34 to 42) in Maze 3
    for x in range(34, 42):
        maze_graphs[3].add((x, 26))
        maze_graphs[3].add((x+1, 26))

    md_content = ["# Ms. Pac-Man 4 大迷宮地圖 ASCII 可視化驗證\\n"]
    md_content.append("此文件將合併後的 4 張 Ms. Pac-Man 迷宮節點座標投影至網格上。您可以直觀檢查通路是否連貫、是否有斷路或跳過像素的問題。\\n")

    for m_id in [1, 2, 3, 4]:
        nodes = maze_graphs[m_id]
        if not nodes:
            md_content.append(f"## 迷宮 {m_id}\\n\\n無節點資料。\\n")
            continue
            
        xs = [n[0] for n in nodes]
        ys = [n[1] for n in nodes]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # MS Pacman physical coordinate ranges: group by bin_size to align ASCII display
        bin_w = 3
        bin_h = 3
        
        grid_w = (max_x - min_x) // bin_w + 2
        grid_h = (max_y - min_y) // bin_h + 2
        
        grid = [[" " for _ in range(grid_w)] for _ in range(grid_h)]
        
        for x, y in nodes:
            gx = (x - min_x) // bin_w
            gy = (y - min_y) // bin_h
            if 0 <= gx < grid_w and 0 <= gy < grid_h:
                grid[gy][gx] = "#"
                
        # Build ASCII string
        ascii_lines = []
        for r in grid:
            ascii_lines.append("".join(r))
            
        md_content.append(f"## 迷宮 {m_id} (Nodes: {len(nodes)}, Range: X:[{min_x}, {max_x}] Y:[{min_y}, {max_y}])\\n")
        md_content.append("```text\\n" + "\\n".join(ascii_lines) + "\\n```\\n\\n")

    with open(artifact_path, "w") as f:
        f.write("\\n".join(md_content).replace("\\n", "\n"))
    print(f"Visualization written to {artifact_path}")

if __name__ == "__main__":
    visualize()
