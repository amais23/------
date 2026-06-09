# Ms. Pac-Man 方案 D：十全大補系統優化實作計劃

本計劃結合了原先解決的 **7 大系統防禦優化** 與新加入的 **3 大核心決策優化**，打造一個 100% 穩定、無死角、高得分上限的 Ms. Pac-Man 冠軍代理人。

---

## 🎯 核心優化項目總覽

### 1. 動作遮罩重罰 (Action Masking Penalty) `[NEW]`
* **問題**：安全過濾器在底層強行覆蓋 PPO 策略（例如把 吃豆 改為 逃跑），會讓 PPO 產生「選吃豆也能活」的錯誤反饋，污染策略梯度。
* **對策**：一旦 PPO 的宏觀策略被安全過濾器沒收並覆蓋，**立即施加重罰（`reward -= 20.0`）**。
* **效果**：PPO 會主動避免選擇危險的策略，讓決策與底層執行完全同調，加快訓練收斂。

### 2. 鬼魂慣性動量預測 (Ghost Momentum Prediction) `[NEW]`
* **問題**：原先假設鬼魂在未來 3 步可以任意折返，導致安全過濾器的模擬範圍過大（悲觀鎖），引發發抖死鎖。
* **對策**：利用鬼魂「正常情況下不能轉 180 度回頭」的慣性，追蹤每隻鬼的前一幀座標估算前進方向，**在模擬中排除折返路徑**。
* **效果**：大幅釋放可通行的安全路徑，讓小精靈流暢穿梭於鬼魂縫隙。

### 3. 硬編碼 4 張迷宮地圖 (Hardcode All 4 Mazes) `[NEW]`
* **問題**：動態地圖收集在進入新關卡（Maze 2+）時有空白期，曼哈頓退路不如 100% 完美的 BFS 尋路。
* **對策**：
  * **Phase A**：部署具備曼哈頓退路的 Agent。
  * **Phase B**：運行 [collect_all_mazes.py](file:///Users/Shared/西洋棋代理人/rl_starter_12/scratch/collect_all_mazes.py) 進行地圖自動採集，累積所有 4 張圖的鄰接表。
  * **Phase C**：將所有 4 張圖以 zlib + base64 寫死在 [model.py](file:///Users/Shared/西洋棋代理人/rl_starter_12/model.py)。
* **效果**：小精靈進入任何一關都有 perfect BFS 全局尋路，消滅開局陣痛。

### 4. 跨回合地圖累積與分立存儲 (self.graphs) `[PREV]`
* **對策**：使用 `self.graphs = {1: defaultdict(set), 2: ...}`，不再每次過關都清空地圖，讓小精靈在訓練過程中逐漸累積完整地圖資訊。

### 5. 曼哈頓安全退路 (Manhattan Fallback) `[PREV]`
* **對策**：若 Pac-Man 走到地圖尚未探索的區域，安全過濾器與路徑規劃自動切換為基於座標偏移的曼哈頓距離估算，防止卡死。

### 6. 前進動量機制 (Direction Momentum) `[PREV]`
* **對策**：在逃跑策略（Strategy 2）中，相同於 `prev_action` 的方向給予 `+1.0` 加分，相反折返方向給予 `-1.0` 扣分。
* **效果**：消除小精靈在十字路口的原地來回發抖。

### 7. 避鬼警告懲罰下調 (Scaled Proximity Warnings) `[PREV]`
* **對策**：將靠近危險鬼魂的警告懲罰下調為 `-1.0` (距離 $\le 8$) 與 `-3.0` (距離 $\le 4$)。
* **效果**：提供避鬼導向，但不會壓過追擊藍鬼（$+100$）與吃豆（$+10$）的宏觀意願。

### 8. 藍鬼回復安全閥門 (Scared Ghost Timer Guard) `[PREV]`
* **對策**：僅在 `blue_timer > dist * 4`（時間充足）時才執行追擊藍鬼，若時間不夠則自動降級回吃豆或逃跑，防止藍鬼在中途復原反殺。

### 9. 傳送門自動連通 (Warp Tunnel Auto-Connection) `[PREV]`
* **對策**：在動態更新圖中，一旦偵測到水平對稱的最左端與最右端點已記錄，自動在圖中建立雙向連通邊，使小精靈開局就明白傳送門的存在。

### 10. 安全裕度緩衝黏性動作 (SAFETY_MARGIN Buffer) `[PREV]`
* **對策**：安全過濾器預判距離門檻全面提升 `1` 步（$t=1,2,3$ 距離門檻改為 $2,3,4$）。
* **效果**：提供物理緩衝，抵消 MsPacman-v5 25% 黏性動作（動作重複）帶來的轉彎延遲。

### 11. 生命扣減強制重設 `prev_p` (Death Reset logic) `[PREV]`
* **對策**：當額外生命（`lives`）減少時，強制將 `prev_p` 設為 `None`，防止跳變座標將死亡點與重生點錯誤相連。

---

## 🛠️ 修改規格說明

### 1. 修改 [model.py](file:///Users/Shared/西洋棋代理人/rl_starter_12/model.py)

#### 慣性限制移動分支
```python
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
```

#### 3-step Lookahead（結合慣性與安全裕度）
```python
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
            if abs(P1_est[0] - g[0]) + abs(P1_est[1] - g[1]) <= 8:
                return False
        return True
        
    ghost_dist_maps = [bfs_distance_map(graph, g) for g in ghosts_pos]
    
    SAFETY_MARGIN = 1
    # Check t=1 safety at P1
    for i in active_ghost_indices:
        g = ghosts_pos[i]
        d1 = get_dist_from_map(ghost_dist_maps[i], P1, g)
        if d1 <= (1 + SAFETY_MARGIN):
            return False
            
    # Check t=2, t=3 safety
    def is_node_safe(node, t):
        for i in active_ghost_indices:
            g = ghosts_pos[i]
            d = get_dist_from_map(ghost_dist_maps[i], node, g)
            if d <= (t + SAFETY_MARGIN):
                return False
        return True

    for P2 in graph[P1]:
        if is_node_safe(P2, 2):
            for P3 in graph[P2]:
                if is_node_safe(P3, 3):
                    return True
    return False
```

#### `heuristic_execute` (追擊安全閥門 + 逃跑動量)
```python
OPPOSITE_ACTIONS = {1: 4, 2: 3, 3: 2, 4: 1}

def heuristic_execute(strategy_id, obs, graph, remaining_pellets, remaining_energizers, prev_action=0):
    px, py = int(obs[10]), int(obs[16])
    blue_timer = int(obs[116])
    ...
    if strategy_id == 3:  # Chase Blue
        blue_ghosts = {ghosts_pos[i] for i in range(4) if is_blue[i]}
        if blue_ghosts:
            closest_bg, dist, next_node = bfs_closest_target(pacman_paths, blue_ghosts, (px, py))
            # 剩餘時間安全閥門
            if closest_bg is not None and blue_timer > dist * 4:
                if next_node is not None:
                    return get_action_to_neighbor(px, py, next_node[0], next_node[1])
        return action_to_targets(remaining_pellets)
        
    elif strategy_id == 2:  # Escape
        best_a = 0
        max_safety = -999.0
        ghost_dist_maps = [bfs_distance_map(graph, g) for g in ghosts_pos]
        for a in [1, 2, 3, 4]:
            neighbor = get_neighbor_by_action(graph, px, py, a)
            if neighbor is not None:
                min_g_dist = 999.0
                for i, g_pos in enumerate(ghosts_pos):
                    if not is_blue[i] and not ghosts_in_house[i]:
                        d = get_dist_from_map(ghost_dist_maps[i], neighbor, g_pos)
                        if d < min_g_dist:
                            min_g_dist = d
                score = min_g_dist
                if prev_action > 0:
                    if a == prev_action:
                        score += 1.0  # 前進加分
                    elif a == OPPOSITE_ACTIONS.get(prev_action):
                        score -= 1.0  # 折返處罰
                if score > max_safety:
                    max_safety = score
                    best_a = a
        ...
```

---

### 2. 修改 [train.py](file:///Users/Shared/西洋棋代理人/rl_starter_12/train.py)
* **動作遮罩重罰**：在執行覆蓋時給予 `reward -= 20.0`。
* **分立地圖管理與生命值扣減清空** `prev_p`。
* 追蹤鬼魂前一幀 `prev_ghosts_pos` 並傳遞給 `check_action_safety`。

---

### 3. 修改 [agent.py](file:///Users/Shared/西洋棋代理人/rl_starter_12/agent.py)
* 使用分立地圖存儲與追蹤 `self.prev_ghosts_pos`、`self.last_action`。
* 偵測 `lives` 減少並重置 `prev_p`。
