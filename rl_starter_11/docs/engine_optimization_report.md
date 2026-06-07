# D6 C++ 西洋棋引擎 — Bug 與優化空間報告

> **檔案**：[engine.cpp](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp)
> **日期**：2026-06-07
> **引擎架構**：SearchEngine 類別（實例化模式），Alpha-Beta + NegaMax + Iterative Deepening

---

## 目錄

1. [Bug（正確性問題）](#1-bug正確性問題)
2. [搜尋優化（高優先）](#2-搜尋優化高優先)
3. [評估函數優化（中優先）](#3-評估函數優化中優先)
4. [資料結構與效能（中優先）](#4-資料結構與效能中優先)
5. [低優先改善](#5-低優先改善)
6. [不建議修改的部分](#6-不建議修改的部分)
7. [優化優先順序總覽](#7-優化優先順序總覽)

---

## 1. Bug（正確性問題）

### 🔴 BUG-1：`is_quiet` 在 `makeMove` 之後判斷

**位置**：[第 1250–1252 行](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L1250-L1252)

```cpp
board.makeMove(move);  // ← 已走棋，被吃的子已從棋盤移除
bool is_quiet = !board.isCapture(move) && move.typeOf() != Move::PROMOTION;
```

**問題**：`board.isCapture(move)` 需要查詢目標格是否有對方棋子。在 `makeMove` 之後，被吃的子已經消失，`isCapture` 可能永遠回傳 `false`，導致：
- **所有吃子走法都被誤判為安靜走法 (quiet move)**
- Killer Move 和 History Heuristic 被吃子走法污染
- LMR 對吃子走法做了不當的縮減搜尋

**影響**：中高。雖然搜尋仍能運作，但走法排序品質和剪枝效率被持續劣化。

**修正方式**：將 `is_quiet` 的判斷移到 `makeMove` 之前。

```cpp
bool is_capture = board.isCapture(move);  // ← makeMove 之前判斷
board.makeMove(move);
bool is_quiet = !is_capture && move.typeOf() != Move::PROMOTION;
```

**有效性評估**：★★★★☆ — 修正後 Killer/History 不再被吃子污染，LMR 不再對吃子做過度縮減。這是 **最容易修、風險最低** 的改動。

---

### 🔴 BUG-2：`fallback_random` 的位元遮罩取模偏差

**位置**：[第 749 行](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L749)

```cpp
return legals[rand() & (legals.size() - 1)]; // Fast random
```

**問題**：`rand() & (size - 1)` 只有在 `size` 是 2 的冪次時等價於 `rand() % size`。當 `size` 不是 2 的冪次時（大多數情況），`& (size-1)` 會產生不均勻的分佈，且可能遺漏某些索引值。例如 `size=5` 時，`& 4` 的結果只能是 `0` 或 `4`，永遠不會選到索引 `1, 2, 3`。

**影響**：低。`fallback_random` 只在搜尋完全失敗時使用，實際觸發率極低。

**修正方式**：

```cpp
return legals[rand() % legals.size()];
```

**有效性評估**：★★☆☆☆ — 修正簡單但影響場景極少。

---

### 🟡 BUG-3：NMP (Null Move Pruning) 的視窗參數

**位置**：[第 1232–1233 行](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L1232-L1233)

```cpp
int null_score = -alpha_beta(board, depth - 1 - R, -beta, -alpha,
                             extensions, search_history);
```

**問題**：標準 NMP 只需要做一個 zero-window 搜尋 (`-beta, -beta+1`)，但目前用的是完整的 `(-beta, -alpha)` 視窗，多花了不必要的搜尋時間。

**影響**：中低。搜尋仍然正確，但 NMP 本應是「快速確認對方能否超過 beta」的廉價搜尋，使用完整視窗削弱了這個優勢。

**修正方式**：

```cpp
int null_score = -alpha_beta(board, depth - 1 - R, -beta, -beta + 1,
                             extensions, search_history);
```

**有效性評估**：★★★☆☆ — 可以略微加速搜尋，無正確性風險。

---

## 2. 搜尋優化（高優先）

### 🟢 OPT-1：Aspiration Windows（搜尋視窗縮窄）

**位置**：[search_best_move，第 1366–1367 行](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L1366-L1367)

```cpp
int score = -alpha_beta(board, depth - 1, -9999999, 9999999, 0, search_history);
```

**問題**：每一層迭代加深都使用完整的 `(-9999999, 9999999)` 視窗。Aspiration Windows 在 depth ≥ 2 時以前一層的分數 ± delta（如 ±50）為視窗搜尋，窗外失敗時重新搜尋。

**預期效益**：典型情況下可 **減少 20–40% 的搜尋節點**，讓同樣的時間能搜更深 1–2 層。

**風險**：低。窗口失敗時有 fallback 機制保證正確性。

**實作複雜度**：中。需要在迭代循環中追蹤前一輪分數，並加入重搜邏輯。

**有效性評估**：★★★★★ — 這是性價比最高的搜尋優化，幾乎所有正式引擎都使用。

---

### 🟢 OPT-2：Futility Pruning（無用走法剪枝）

**現況**：完全沒有實作。

**原理**：在接近葉節點（depth=1 或 2）時，如果靜態評估 + 一個合理的走法增益仍然低於 alpha，則跳過安靜走法的搜尋。

```
if (depth == 1 && !in_check && static_eval + FUTILITY_MARGIN < alpha) {
    skip quiet moves;
}
```

**預期效益**：在接近葉節點時 **剪掉 30–60% 的安靜走法**。

**風險**：低。只對安靜走法生效，吃子和升變不受影響。

**實作複雜度**：低。只需在 alpha_beta 迴圈中加入一個條件判斷。

**有效性評估**：★★★★☆ — 實作簡單，效益明確。

---

### 🟢 OPT-3：Principal Variation Search (PVS)

**現況**：目前 LMR 有用到 zero-window，但非 PV 走法沒有。

**原理**：第一個走法用完整窗口搜尋，之後的走法先用 zero-window `(-alpha-1, -alpha)` 搜尋，如果超出窗口才用完整窗口重搜。

**預期效益**：如果走法排序品質好（TT + MVV-LVA + Killer 已有不錯基礎），**可以減少 10–20% 的搜尋節點**。

**風險**：低。

**實作複雜度**：低。在 `alpha_beta` 的主迴圈中，對 `i > 0` 的走法先做 zero-window 搜尋。

**有效性評估**：★★★★☆

---

### 🟢 OPT-4：改善 LMR 的觸發條件

**位置**：[第 1262 行](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L1262)

```cpp
if (new_depth >= 3 && i >= 3 && is_quiet && !gives_check && !in_check)
```

**現況**：`i >= 3` 表示前 3 個走法都不會被 LMR 縮減。但配合 BUG-1 修正後，吃子會被正確排除，可以考慮將閾值降到 `i >= 2`。

**此外缺少的 LMR 相關優化**：
- **History-based LMR reduction**：根據 history 分數動態調整縮減量，history 分數低的走法多縮減。
- **Improving flag**：如果目前評估比兩步前更好（improving），少縮減；更差則多縮減。

**有效性評估**：★★★☆☆ — 邊際效益，但累積起來有意義。

---

## 3. 評估函數優化（中優先）

### 🟡 OPT-5：缺少兵結構評估

**缺少項目**：

| 項目 | 說明 | 建議分數 |
|---|---|---|
| **孤立兵 (Isolated Pawn)** | 相鄰列沒有己方兵保護 | -15 每個 |
| **雙疊兵 (Doubled Pawn)** | 同一列有 2 個以上己方兵 | -10 每組 |
| **落後兵 (Backward Pawn)** | 無法被相鄰兵保護且前方被阻 | -10 每個 |

**實作複雜度**：低。使用 bitboard 操作即可判斷。

**有效性評估**：★★★★☆ — 兵結構是中盤局面判斷的核心。目前只有通路兵評估，缺少弱兵懲罰導致引擎可能走出有結構缺陷的局面。

---

### 🟡 OPT-6：缺少王的安全評估

**現況**：只有粗略的「國王是否已經入堡」獎勵（±30 分），沒有基於攻擊計數的王安全評估。

**缺少的項目**：
- 國王周圍的攻擊者計數
- 國王前方的兵盾（Pawn Shield）
- 半開放文件對國王的威脅

**實作複雜度**：中高。需要計算攻擊表、遮罩等。

**有效性評估**：★★★☆☆ — 重要但實作成本較高。在時間有限的競賽中，可能不值得投入。

---

### 🟡 OPT-7：缺少棋子機動性 (Mobility) 評估

**現況**：沒有計算棋子的可走格數。一個被困住的象和一個在中央的象分數完全一樣（僅靠 PST 區分位置，不評估實際可走格）。

**實作方式**：對每個棋子計算合法移動數，乘以小系數加入分數。

**實作複雜度**：中。需要對每個棋子產生攻擊遮罩。

**有效性評估**：★★★☆☆ — 對中盤局面判斷有幫助，但計算成本會讓 evaluate 變慢，影響搜尋深度。需要權衡。

---

## 4. 資料結構與效能（中優先）

### 🟡 OPT-8：`unordered_map` 的重複局面偵測效率低

**位置**：[第 1192 行、1243 行、1300 行](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L1192)

```cpp
std::unordered_map<uint64_t, int> &search_history
```

每個節點都要做 `search_history.count(key)` + `search_history[key]++`，`unordered_map` 的常數開銷大（hash bucket、pointer chasing、cache miss）。

**替代方案**：

```cpp
// 方案 A：固定大小的計數陣列（推薦）
static uint8_t rep_table[1 << 16];  // 64KB
int idx = key & 0xFFFF;
if (rep_table[idx] >= 2) return 0;
rep_table[idx]++;
// ... 搜尋 ...
rep_table[idx]--;
```

會有少量 hash 衝突（誤判重複），但在實際棋局中影響極小。

**方案 B**：使用 `std::array` 做 stack-based 的歷史追蹤。

**有效性評估**：★★★☆☆ — `unordered_map` 的開銷在搜尋深層累積明顯。但改動涉及整個搜尋流程的參數傳遞，有一定風險。

---

### 🟡 OPT-9：`search_history` 的複製開銷

**位置**：[第 1424 行](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L1424)

```cpp
auto search_history = m_game_history;  // 深拷貝整個 map
```

每次呼叫 `solve` 都會深拷貝 `m_game_history`。如果遊戲進行了 40 步，map 裡有 ~40 個 entry，拷貝成本雖不大但可以避免。

**替代方案**：直接傳引用 `m_game_history`，搜尋結束後再清理搜尋中新增的 entry。

**有效性評估**：★★☆☆☆ — 微小優化。

---

### 🟡 OPT-10：走法排序中的 `std::vector` 和 `std::sort` 開銷

**位置**：[order_moves，第 957–996 行](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L957-L996)

每個節點都建立一個 `std::vector<std::pair<int, Move>>` 並完整排序。可以改為：
- 使用 `Movelist` 內部的固定大小陣列直接排序，避免 heap allocation
- 或使用 **partial sort / selection** — 因為大多數情況下 beta cutoff 發生在前幾個走法，不需要完整排序

**有效性評估**：★★★☆☆ — 每個節點都觸發，累積起來有意義。

---

## 5. 低優先改善

### OPT-11：時間管理過於粗糙

**位置**：[第 1340–1345 行](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L1340-L1345)

```cpp
if (phase >= 8)  m_time_limit = 1.0;
else if (phase >= 4) m_time_limit = 0.5;
else m_time_limit = 0.2;
```

三段式固定時間，沒有考慮：
- 伺服器剩餘時間
- 走法數量（複雜度）
- 是否已經搜到穩定分數（分數變化小可以提前結束）
- 是否只有一個合法走法（forced move，不用搜尋）

**有效性評估**：★★☆☆☆ — 需要伺服器提供時間資訊才能完整實作。

---

### OPT-12：SEE (Static Exchange Evaluation)

在走法排序中，使用 SEE 過濾「虧本的吃子」（如用后吃對方兵但被吃回）。目前 MVV-LVA 會把這類吃子排在前面，浪費搜尋時間。

**有效性評估**：★★★☆☆ — 改善吃子排序品質，但實作複雜度高。

---

### OPT-13：Counter Move Heuristic

記錄「對方走了 X 之後，最常成功的回應是 Y」。比 Killer Move 更細緻。

**有效性評估**：★★☆☆☆ — 邊際改善，實作成本中等。

---

### OPT-14：Two-Tier TT（雙層置換表）

**位置**：[tt_store，第 784–790 行](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L784-L790)

目前使用 always-replace（除非深度更深），可能覆蓋重要的深層結果。雙層 TT 保留一層「最深」和一層「最新」。

**有效性評估**：★★☆☆☆ — 改善 TT 命中率，但在目前搜尋深度下邊際效益不大。

---

## 6. 不建議修改的部分

### ❎ Contempt Factor（鄙視值）

前面分析過，`return 0` 在重複局面時透過搜尋分數比較已經隱含了「佔優拒絕和局、劣勢接受和局」的效果。加入 Contempt 的風險大於收益。

### ❎ 評估函數中的 `isGameOver` 呼叫

在 `evaluate()` 的開頭和 `quiescence()` 的開頭都呼叫了 `board.isGameOver()`。雖然有些引擎會把這個提前到搜尋層面避免重複呼叫，但在目前的架構下，改動會增加程式碼複雜度且可能引入邊界 bug。

---

## 7. 優化優先順序總覽

| 排名 | 項目 | 類型 | 難度 | 風險 | 預期效益 |
|:---:|---|---|:---:|:---:|---|
| **1** | BUG-1：`is_quiet` 判斷時機 | Bug 修正 | 極低 | 極低 | Killer/History/LMR 全面修正 |
| **2** | OPT-1：Aspiration Windows | 搜尋 | 中 | 低 | 節省 20–40% 節點 |
| **3** | OPT-2：Futility Pruning | 搜尋 | 低 | 低 | 葉節點剪掉 30–60% quiet |
| **4** | OPT-3：PVS | 搜尋 | 低 | 低 | 節省 10–20% 節點 |
| **5** | OPT-5：兵結構評估 | 評估 | 低 | 低 | 改善中盤局面判斷 |
| **6** | BUG-3：NMP zero-window | Bug | 極低 | 極低 | 微小加速 |
| **7** | BUG-2：fallback_random 取模 | Bug | 極低 | 極低 | 極少觸發但應修正 |
| **8** | OPT-8：替換 unordered_map | 效能 | 中 | 中 | 減少搜尋常數開銷 |
| **9** | OPT-10：走法排序避免 heap alloc | 效能 | 中 | 低 | 減少每節點開銷 |
| **10** | OPT-6：王安全評估 | 評估 | 高 | 中 | 改善攻防判斷 |

> **建議**：先修 BUG-1（一行修改），再依序實作 OPT-1 → OPT-2 → OPT-3。這四項改動合起來可以讓引擎在相同時間內多搜 1–3 層深度，是最大的競爭力提升。
