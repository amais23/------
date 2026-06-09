import gymnasium as gym
from model import load_prebuilt_graph, MAZE_1_BASE64, align_coordinates_to_graph, dijkstra_closest_target

print("Loading prebuilt graph for Maze 1...")
graph = load_prebuilt_graph(MAZE_1_BASE64)

# 1. 測試 KeyError 邊界對齊
print("\n--- Test 1: Coordinate Alignment ---")
test_coords = [
    (999, 999),   # 極度滑出
    (0, 0),       # 零點
    (-10, 80),    # 負座標
    (77, 73),     # 略微滑出鬼屋
]
for x, y in test_coords:
    aligned = align_coordinates_to_graph(graph, x, y)
    print(f"Raw: ({x}, {y}) -> Aligned: {aligned} (Is in graph: {aligned in graph})")
    assert aligned in graph, f"Aligned node {aligned} must be in graph"

# 2. 測試 dijkstra_closest_target NoneType 解構防禦
print("\n--- Test 2: Dijkstra Closest Target Fallback ---")
# 假設起點是 (18, 14)，但 target 集合在不可達的位置或者完全不在地圖中
start_pos = (18, 14)
# 假想沒有可達的路徑
paths_map = {start_pos: (0.0, start_pos)}
targets = {(158, 146)} # 地圖另一端

# 當使用 graph 參數時，應當 fallback 到曼哈頓距離，並尋找一個跟 (158, 146) 距離最短的鄰居作為首步 fallback
closest_t, dist, next_node = dijkstra_closest_target(paths_map, targets, start_pos, graph=graph)
print(f"Target unreachable via paths_map. Fallback output:")
print(f"Closest Target: {closest_t}")
print(f"Distance: {dist}")
print(f"Next Node: {next_node}")
assert next_node is not None, "next_node must not be None when graph is provided"
assert next_node in graph[start_pos], "next_node must be a neighbor of start_pos"

print("\nAll defensive checks passed successfully!")
