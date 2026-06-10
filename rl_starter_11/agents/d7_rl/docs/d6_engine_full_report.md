# D6-CPP 引擎技術報告

### 現有演算法全覽 × NNUE + RL 微調下一步計畫

**版本**：2026-06-08
**引擎原始碼**：[engine.cpp](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp)（1592 行，62 KB）
**Python 介面**：[agent.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/agent.py)（194 行）

---

## 第一部分：現有引擎演算法完整說明

---

### 1.1 整體架構

```
PettingZoo 觀察值 (8×8×111 Numpy Array)
          │
          ▼
  [Python 端 agent.py]
  ┌─────────────────────────────────────┐
  │  ① Syzygy 殘局庫探測 (≤5子)         │
  └─────────────────────────────────────┘
          │ 若無殘局庫命中
          ▼
  [C++ 引擎 chess_engine_d6_han.so]
  ┌─────────────────────────────────────┐
  │  ② FEN 還原（observation → Board） │
  │  ③ Polyglot 開局書查詢             │
  │  ④ Iterative Deepening + Alpha-Beta │
  │     ├─ NMP（空步剪枝）              │
  │     ├─ PVS（主要變化搜尋）          │
  │     ├─ LMR（晚移動降深）            │
  │     ├─ Futility Pruning            │
  │     └─ Quiescence Search（靜態搜尋）│
  └─────────────────────────────────────┘
          │
          ▼
    PettingZoo Action Index (0~4671)
```

---

### 1.2 棋盤表示與觀察值解析

#### 1.2.1 觀察值格式

PettingZoo Chess 環境提供 `(8, 8, 111)` 形狀的 `int8` 陣列，關鍵通道：

| 通道索引      | 內容                     |
| ------------- | ------------------------ |
| `[0]`       | 白方 Kingside Castle 權  |
| `[1]`       | 白方 Queenside Castle 權 |
| `[2]`       | 黑方 Kingside Castle 權  |
| `[3]`       | 黑方 Queenside Castle 權 |
| `[7]`       | 白方兵（含過路兵標記）   |
| `[8]~[12]`  | 白方馬、象、車、后、王   |
| `[13]`      | 黑方兵（含過路兵標記）   |
| `[14]~[18]` | 黑方馬、象、車、后、王   |

> **重要**：觀察值永遠以「己方為白方」的相對視角呈現。

#### 1.2.2 FEN 還原 `rebuild_fen_from_observation()`

C++ 端的 [`rebuild_fen_from_observation()`](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L434-L530) 將 observation 轉換成 FEN 字串，供 `chess-lib` 的 `Board` 物件使用。

特殊處理：

- **過路兵（En Passant）**：若 `obs[7][col][7] == 1`，代表有過路兵在第 3 列（白方視角），ep square 設為 `col3`
- **白棋底線兵過濾**：`if (p == 'P' && r == 7) continue;`（防止觀察值邊緣 bug）

#### 1.2.3 座標系轉換 `relative_to_absolute()`

由於觀察值以己方為白，當實際是黑方時，[`relative_to_absolute()`](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L535-L619) 做垂直鏡射：

```cpp
// 棋子位置鏡射：sq ^ 56 (垂直翻轉，a1↔a8)
int abs_sq = sq ^ 56;
// 顏色翻轉：白→黑，黑→白
Color new_color = (color == Color::WHITE) ? Color::BLACK : Color::WHITE;
```

此函數專門用於開局書查詢——讓黑方可以用「白方語言」查詢 Polyglot 開局書。**搜尋引擎本身全程在相對棋盤（己方為白）上工作，無需再次轉換。**

---

### 1.3 動作編碼：73 平面 PettingZoo 格式

`動作索引 = (col * 8 + row) * 73 + plane`，共 4672 個可能動作。

73 個平面的分配：

| 平面索引  | 類型             | 說明                                    |
| --------- | ---------------- | --------------------------------------- |
| `0~55`  | 皇后移動         | 8 方向 × 7 格（含直線+斜線）           |
| `56~63` | 馬的移動         | 8 種 L 形跳法                           |
| `64~72` | 兵升變（低升變） | 3 方向 × 3 種棋子（馬/象/車），共 9 種 |

升后為「皇后移動到底線」，不需要額外平面。易位走法的 `to_sq` 需映射到實際落子格（G 或 C 列），不用車的初始位置。

---

### 1.4 三層查詢優先架構

#### 優先層 1：Syzygy 殘局庫（Python 端）

當棋盤子力 ≤ 5 枚時，Python 端的 [`_probe_syzygy()`](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/agent.py#L136-L173) 觸發：

```python
wdl = -_TABLEBASE.probe_wdl(board)   # Win/Draw/Lose 值
dtz = -_TABLEBASE.probe_dtz(board)   # Distance-to-Zero（半步計數）

score = wdl * 10_000_000
if wdl > 0:   score -= abs(dtz)  # 勝：選 DTZ 最小（最快獲勝）
elif wdl < 0: score += abs(dtz)  # 負：選 DTZ 最大（拖延最久）
```

Syzygy 庫位於 `/tmp/syzygy` 或 `./syzygy` 目錄，若不存在則跳過。

#### 優先層 2：Polyglot 開局書

[`probe_book()`](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L894-L949) 使用加權隨機選取：

```cpp
// 查詢匹配：用 Polyglot Hash 做二分搜尋（書庫已排序）
auto it = std::lower_bound(m_book_entries.begin(), m_book_entries.end(), poly_key, ...);

// 加權隨機（weight 越高的走法越常被選）
int r = m_rng() % total_weight;
```

Polyglot Hash（781 個 Random Array）完全自行實作，不依賴外部函式庫。黑方的書庫走法需要二次轉換：`from_sq ^ 56` 做座標鏡射。

#### 優先層 3：Alpha-Beta 搜尋

若前兩層均未命中，進入全力搜尋。

---

### 1.5 搜尋演算法詳解

#### 1.5.1 Iterative Deepening（反覆加深）

```
深度 1 → 深度 2 → 深度 3 → ... → 深度 64（或超時）
```

- 超時處理：每 4096 個節點檢查一次計時，超時拋出 `std::runtime_error("timeout")`
- 超時後返回**最後一次完整完成的深度**的最佳走法
- `search_best_move()` 接收 Board 的**值拷貝**，避免超時導致 unmakeMove 未執行而汙染外部棋盤

#### 1.5.2 Aspiration Windows（期望窗口）

從深度 3 開始，用上一次搜尋分數估計本次搜尋範圍：

```cpp
int delta = 50;                       // 初始窗口 ±50 厘兵
alpha = last_score - delta;
beta  = last_score + delta;

// 若 fail-low 或 fail-high，擴大 delta 重搜
if (score <= alpha) { alpha = -INF; delta *= 2; }
if (score >= beta)  { beta  = +INF; delta *= 2; }
if (delta > 2000)   { alpha = -INF; beta = +INF; } // 放棄窗口，全搜
```

#### 1.5.3 Null Move Pruning（空步剪枝，NMP）

在非將軍局面且棋盤有主力子的情況下，讓對方多走一步做零窗口搜尋：

```cpp
int R = (depth >= 6) ? 3 : 2;   // 降深幅度：淺層 2，深層 3
board.makeNullMove();            // 跳過己方走法
int null_score = -alpha_beta(board, depth - 1 - R, -beta, -beta + 1, ...);
board.unmakeNullMove();
if (null_score >= beta) return beta;  // 即使對方多走一步我方仍佔優 → 剪枝
```

**保護條件**：不在將軍中 + `has_major_pieces()`（避免殘局 Zugzwang 誤判）。

#### 1.5.4 PVS（Principal Variation Search，主要變化搜尋）

對 PV 走法用全窗口，其餘走法先用零窗口確認是否值得全搜：

```cpp
if (i == 0) {
    // PV 走法：全窗口搜尋
    score = -alpha_beta(board, new_depth, -beta, -alpha, ...);
} else {
    // 非 PV 走法：先零窗口（省計算量）
    score = -alpha_beta(board, new_depth, -(alpha+1), -alpha, ...);
    if (score > alpha && score < beta) {
        // 超出預期，可能是更好的走法，再全窗口驗證
        score = -alpha_beta(board, new_depth, -beta, -alpha, ...);
    }
}
```

#### 1.5.5 LMR（Late Move Reduction，晚移動降深）

對排序靠後的安靜走法自動降低搜尋深度：

```cpp
// 觸發條件：深度 ≥ 3 + 排序位置 ≥ 4（i>=3）+ 安靜走法 + 非將軍
if (new_depth >= 3 && i >= 3 && is_quiet && !gives_check && !in_check) {
    // 對數降深公式（與 Stockfish 類似）
    int reduction = 1 + int(log(new_depth) * log(i + 1) / 2.0);
    reduction = std::min(reduction, new_depth - 1);  // 至少搜 1 層
  
    // 零窗口降深搜尋
    score = -alpha_beta(board, new_depth - reduction, -(alpha+1), -alpha, ...);
    if (score > alpha) {
        // 超出預期，重新全深搜尋（re-search）
        score = -alpha_beta(board, new_depth, -beta, -alpha, ...);
    }
}
```

#### 1.5.6 Futility Pruning（無效剪枝）

在 depth == 1 的節點，如果靜態評估 + 150 仍小於 alpha，跳過所有安靜走法：

```cpp
bool skip_quiet = (depth == 1 && !in_check && static_eval + 150 < alpha);
if (skip_quiet && is_quiet) continue;
```

150 是「一步安靜走法所能帶來的最大價值上界」估算值。

#### 1.5.7 Check Extension（將軍延伸）

當走法讓對方陷入將軍，且已用的延伸次數 < 3：

```cpp
int ext = (gives_check && extensions < 3) ? 1 : 0;
int new_depth = depth - 1 + ext;   // 延伸 1 層
```

最多允許 3 層延伸，防止搜尋爆炸。

---

### 1.6 移動排序（Move Ordering）

搜尋效率高度依賴移動排序，排序優先級由高到低：

| 優先級 | 走法類型                        | 分數                                |
| ------ | ------------------------------- | ----------------------------------- |
| 1      | **轉置表走法（TT Move）** | 1,000,000                           |
| 2      | **升變走法**              | 15,000 + 棋子價值                   |
| 3      | **吃子走法（MVV-LVA）**   | 10,000 + 被吃子價值 - 攻擊子價值/10 |
| 4      | **Killer 走法 1**         | 9,000                               |
| 5      | **Killer 走法 2**         | 8,000                               |
| 6      | **History 走法**          | ≤ 7,000（歷史分數）                |
| 7      | **其餘安靜走法**          | 0                                   |

**MVV-LVA**（Most Valuable Victim / Least Valuable Attacker）：優先選「用小子吃大子」，分母/10 降低差棄子的優先級。

**Killer Heuristic**：每個深度存 2 個「最近一次引起 beta cutoff 的安靜走法」，下次優先嘗試。

**History Heuristic**：記錄每個 `[顏色][from][to]` 走法引起的 cutoff 加權次數（`+= depth²`），每次開始搜尋前對所有值減半（`/= 2`）避免歷史分數無限膨脹。

---

### 1.7 靜態搜尋（Quiescence Search）

在葉節點繼續搜尋吃子走法，避免「水平線效應」（在一個吃子剛發生的局面停止搜尋）：

```cpp
int quiescence(Board& board, int alpha, int beta, int qdepth) {
    // Stand-pat：假設可以選擇「不吃」，靜態評估為下界
    int stand_pat = evaluate(board, 0);
    if (stand_pat >= beta) return beta;           // Beta 截斷
    if (stand_pat > alpha) alpha = stand_pat;     // 更新 alpha
  
    // 只搜尋吃子走法（+ MVV-LVA 排序）
    Movelist captures;
    movegen::legalmoves<movegen::MoveGenType::CAPTURE>(captures, board);
  
    for (const auto& move : scored_captures) {
        // Delta Pruning：即使吃了最有價值的子 + 200，仍不夠 alpha → 跳過
        if (stand_pat + victim_val + 200 < alpha &&
            move.typeOf() != Move::PROMOTION) continue;
      
        board.makeMove(move);
        int score = -quiescence(board, -beta, -alpha, qdepth + 1);
        board.unmakeMove(move);
        // ... alpha/beta 更新
    }
    // 最大靜搜深度：qdepth > 4 直接返回靜態評估
}
```

---

### 1.8 轉置表（Transposition Table，TT）

```
大小：4M 條目（1 << 22），約 80MB
替換策略：Always-Replace（深度 >= 現有才覆蓋）
```

每個條目 14 bytes：

```cpp
struct TTEntry {
    uint64_t key;    // Zobrist Hash（8 bytes）
    int32_t score;   // 分數（4 bytes）
    Move best_move;  // 最佳走法（2 bytes）
    int8_t depth;    // 搜尋深度（1 byte）
    TTFlag flag;     // EXACT / ALPHA / BETA（1 byte）
};
```

**三種 flag 使用場景**：

- `TT_EXACT`：精確值，可直接使用（PV 節點）
- `TT_ALPHA`：上界（fail-low 節點），score <= alpha，用於更新 alpha
- `TT_BETA`：下界（fail-high 節點），score >= beta，用於剪枝

> **注意**：`search_best_move()` 每次呼叫時**清空整個 TT**，避免上一局殘留資料干擾。

---

### 1.9 評估函數（Hand-Crafted Evaluation，HCE）

[`evaluate()`](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L994-L1133) 返回以「當前走棋方為正」的分數（負分表示對方佔優）。

#### 1.9.1 棋子基礎價值

| 棋子         | 兵  | 馬  | 象  | 車  | 后  | 王    |
| ------------ | --- | --- | --- | --- | --- | ----- |
| 價值（厘兵） | 100 | 320 | 330 | 500 | 900 | 20000 |

象（330）略重於馬（320），因此在開放局面象更有優勢。

#### 1.9.2 棋子位置表（PST）+ Tapered Eval（漸變評估）

根據遊戲階段（開中殘局）在中局 PST 和殘局 PST 之間線性插值：

```cpp
// 計算遊戲階段（最大值 24）
int phase = N_count + B_count + R_count*2 + Q_count*4;
phase = std::min(phase, 24);

// 漸變評估
int val_mg = piece_val + PST_midgame[sq ^ 56];  // sq^56：白方視角 PST 座標
int val_eg = piece_val + PST_endgame[sq ^ 56];
score += (val_mg * phase + val_eg * (24 - phase)) / 24;
```

王有獨立的中局 PST（鼓勵躲在側翼 g1/c1）和殘局 PST（鼓勵走向中央，中央格 +40）。

#### 1.9.3 其他評估項目

| 項目              | 白方            | 黑方            | 說明                       |
| ----------------- | --------------- | --------------- | -------------------------- |
| 主教對            | +50             | -50             | 兩個主教同時存在           |
| 王易位獎勵        | +30（g1/c1/b1） | -30（g8/c8/b8） | 王在易位位置               |
| 車在開放/半開放列 | +20/車          | -20/車          | 己方兵不在同列             |
| 通過兵            | +10×rank       | -10×(7-rank)   | 前方無對方兵阻擋（含側列） |
| 疊兵懲罰          | -10×(數量-1)   | +10×(數量-1)   | 同列多個兵                 |
| 孤兵懲罰          | -15/兵          | +15/兵          | 相鄰列無友方兵             |

**目前缺少的重要評估**（NNUE 可補足）：

- ❌ 王的安全（對方攻擊子指向王區域的數量）
- ❌ 棋子活動力（棋子可移動的格子數）
- ❌ 棋子協調（相互支援、覆蓋關鍵格）
- ❌ 開放列控制（縱深位置的重要性）

---

### 1.10 時間管理

根據棋局階段（子力數）動態分配搜尋時間：

| 階段值 | 時間限制 | 對應局面                      |
| ------ | -------- | ----------------------------- |
| ≥ 8   | 1.0 秒   | 開局 / 中局（有足夠子力）     |
| ≥ 4   | 0.5 秒   | 殘局前期                      |
| < 4    | 0.2 秒   | 極少子力（Syzygy 通常已覆蓋） |

---

### 1.11 重複局面偵測

使用 `std::vector<uint64_t>` 的線性掃描（比 hash map 在小數組上更快）：

```cpp
for (auto h : search_history) {
    if (h == key) {
        rep_count++;
        if (rep_count >= 2) return 0;  // 第三次重複 → 視為和局
    }
}
```

`m_game_history`（跨局遊戲層級）與 `search_history`（搜尋內部）分開管理，搜尋時合併使用，完成後分別更新。

---

### 1.12 部署機制（Magic Zip / ELF Loader）

沙箱環境限制：`/tmp` 掛載 `noexec`，`/app/arena` 唯讀。

解決方案：將 Linux ELF `.so` 直接複製成 `model.zip`（ZIP 格式從尾端讀 header，ELF 從頭部讀，兩者互不干擾）：

```bash
# pack.sh 的核心邏輯
cp chess_engine_d6_han.cpython-310-x86_64-linux-gnu.so model.zip
# model.zip 既是合法 ELF 動態函式庫，也是合法 ZIP 壓縮檔！
```

載入順序（[agent.py:36-58](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/agent.py#L36-L58)）：

1. 嘗試直接 `import chess_engine_d6_han`（本地開發環境）
2. 若失敗，用 `importlib.machinery.ExtensionFileLoader` 對 `model.zip` 做 `dlopen()` 直接載入

編譯需要兩次：macOS（開發用）+ Docker manylinux2014（部署用，Python 3.10）。

---

## 第二部分：NNUE + RL 微調下一步計畫

---

### 2.1 為什麼要做 NNUE？

現有 HCE 的極限：

| 評估能力                | HCE（現有）           | NNUE（目標）              |
| ----------------------- | --------------------- | ------------------------- |
| 材料計算                | ✅                    | ✅                        |
| 棋子位置（PST）         | ✅ 粗略               | ✅ 精確學習               |
| 兵型結構                | ✅ 基礎 3 項          | ✅ 複雜結構全部           |
| 王的安全                | ⚠️ 只有 castle 獎勵 | ✅ 完整攻擊評估           |
| 棋子協調                | ❌                    | ✅ 自動學習               |
| 棋子活動力              | ❌                    | ✅ 自動學習               |
| **預期 Elo 提升** | —                    | **+100 ~ +250 Elo** |

---

### 2.2 NNUE 架構選擇

推薦使用 Stockfish **HalfKP_256x2-32-32** 架構（小而快）：

```
輸入特徵（HalfKP）：
  特徵 = 己方王的位置（64 格）× 所有棋子的（棋子類型×2色，5種棋子不含王）× 64 格
  = 64 × 640 = 40960 維稀疏輸入

網路結構：
  [40960 稀疏] ─→ FC 256 ─→ ClippedReLU(0, 127)   ← 兩方視角各算一次
  兩方特徵拼接：[256 + 256 = 512]
             ─→ FC 32  ─→ ClippedReLU(0, 127)
             ─→ FC 32  ─→ ClippedReLU(0, 127)
             ─→ FC 1   ─→ 評估分數（厘兵）

量化：int8/int16 儲存，推論時使用整數運算（無浮點），速度極快。
推論時間：CPU 約 1~3 µs/節點（SIMD 加速後）
```

---

### 2.3 完整管線設計

```
┌──────────────────────────────────────────────────────────────┐
│                Phase 1：NNUE 整合（0.5~1 天）                   │
│  下載 Stockfish .nnue 權重                                   │
│  → C++ 實作 NNUE 推論模組（nnue_eval.h）                     │
│  → 替換 engine.cpp 的 evaluate() 呼叫                        │
│  → xxd -i 將權重編入 .h，隨 .so 一起打包                     │
│  → A/B 測試確認 Elo 提升                                     │
└──────────────────────────────────────────────────────────────┘
            │ 確認提升後繼續
            ▼
┌──────────────────────────────────────────────────────────────┐
│                Phase 2：資料生成（1 天）                    │
│  本地高速自我對弈（每步 50~200ms）                            │
│  → 生成 FEN + 靜態評估 + 最終對局結果（W/D/L）               │
│  → 目標：100 萬 ~ 1000 萬局面                                │
└──────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────┐
│                Phase 3：RL 微調（持續迭代）                   │
│  用 nnue-pytorch 載入預訓練權重                               │
│  → 混合損失：監督損失 + RL 損失（漸進調整 lambda）             │
│  → 量化（float → int8/int16）→ 匯出 .nnue                   │
│  → 重新打包部署 → 線上 A/B 測試 → 觀察 Elo 曲線              │
└──────────────────────────────────────────────────────────────┘
```

---

### 2.4 Phase 1 詳細實作：NNUE 推論整合

#### Step 1-1：下載 NNUE 權重

```bash
# Stockfish 官方小型網路（推論速度快，約 20 MB）
wget https://tests.stockfishchess.org/api/nn/nn-5af11540bbfe.nnue -O nn.nnue
ls -lh nn.nnue   # 預期：~20 MB
```

#### Step 1-2：C++ 端 NNUE 推論模組（`nnue_eval.h`）

以下為精簡版實作，展示核心原理：

```cpp
// nnue_eval.h — NNUE 推論模組（簡化的 HalfKP_256x2-32-32）
#pragma once
#include <cstdint>
#include <array>
#include <algorithm>
#include "chess.hpp"
using namespace chess;

static constexpr int HALFKP_SIZE = 40960;  // 64 * 640
static constexpr int L1_SIZE     = 256;
static constexpr int L2_SIZE     = 32;
static constexpr int L3_SIZE     = 32;

struct NNUENetwork {
    // 特徵轉換層（Feature Transformer）
    int16_t ft_weights[HALFKP_SIZE * L1_SIZE];   // 40960 × 256
    int16_t ft_biases[L1_SIZE];                  // 256
    // FC 層
    int8_t  l1_weights[(L1_SIZE * 2) * L2_SIZE];
    int32_t l1_biases[L2_SIZE];
    int8_t  l2_weights[L2_SIZE * L3_SIZE];
    int32_t l2_biases[L3_SIZE];
    int8_t  l3_weights[L3_SIZE];
    int32_t l3_bias;
};

// HalfKP 特徵索引計算
// king_sq：己方王的格子（0~63）
// piece_sq：棋子的格子（0~63）
// piece_type：0=P, 1=N, 2=B, 3=R, 4=Q（不含王）
// is_opp：0=己方棋子, 1=對方棋子
inline int halfkp_index(int king_sq, int piece_sq, int piece_type, int is_opp) {
    int piece_idx = piece_type * 2 + is_opp;  // 0~9
    return king_sq * 640 + piece_idx * 64 + piece_sq;
}

// ClippedReLU（量化激活函數）
inline uint8_t crelu(int32_t x) {
    return static_cast<uint8_t>(std::max(0, std::min(127, x)));
}

// 從棋盤全量計算累加器（非增量版，簡單可靠）
void compute_accumulator(
    const Board& board, const NNUENetwork& net,
    std::array<int16_t, L1_SIZE>& w_acc,
    std::array<int16_t, L1_SIZE>& b_acc)
{
    // 初始化為偏置
    for (int i = 0; i < L1_SIZE; i++) {
        w_acc[i] = net.ft_biases[i];
        b_acc[i] = net.ft_biases[i];
    }

    int wksq = board.kingSq(Color::WHITE).index();
    int bksq = board.kingSq(Color::BLACK).index() ^ 56;  // 黑方視角鏡射

    for (int pt = 0; pt < 5; pt++) {
        PieceType piece_type = static_cast<PieceType::underlying>(pt);
        for (Color c : {Color::WHITE, Color::BLACK}) {
            Bitboard bb = board.pieces(piece_type, c);
            while (bb) {
                int sq = bb.pop().index();
                // 白方視角
                int wi = halfkp_index(wksq, sq,      pt, (c == Color::BLACK) ? 1 : 0);
                // 黑方視角（棋子位置也需鏡射）
                int bi = halfkp_index(bksq, sq ^ 56, pt, (c == Color::WHITE) ? 1 : 0);

                for (int j = 0; j < L1_SIZE; j++) {
                    w_acc[j] += net.ft_weights[wi * L1_SIZE + j];
                    b_acc[j] += net.ft_weights[bi * L1_SIZE + j];
                }
            }
        }
    }
}

// NNUE 前向傳播，返回厘兵分數（當前走棋方視角）
int nnue_evaluate(const Board& board, const NNUENetwork& net) {
    std::array<int16_t, L1_SIZE> w_acc, b_acc;
    compute_accumulator(board, net, w_acc, b_acc);

    bool stm_white = (board.sideToMove() == Color::WHITE);
    auto& stm_acc = stm_white ? w_acc : b_acc;
    auto& opp_acc = stm_white ? b_acc : w_acc;

    // L1 輸入：ClippedReLU 後拼接（512 維）
    std::array<uint8_t, L1_SIZE * 2> l1_in;
    for (int i = 0; i < L1_SIZE; i++) {
        l1_in[i]          = crelu(stm_acc[i]);
        l1_in[i+L1_SIZE]  = crelu(opp_acc[i]);
    }

    // L1 → L2
    std::array<int32_t, L2_SIZE> l2;
    for (int j = 0; j < L2_SIZE; j++) {
        l2[j] = net.l1_biases[j];
        for (int i = 0; i < L1_SIZE*2; i++)
            l2[j] += (int32_t)l1_in[i] * net.l1_weights[i*L2_SIZE+j];
    }

    // L2 → L3
    std::array<uint8_t, L2_SIZE> l2_out;
    for (int j = 0; j < L2_SIZE; j++) l2_out[j] = crelu(l2[j] >> 6);

    std::array<int32_t, L3_SIZE> l3;
    for (int j = 0; j < L3_SIZE; j++) {
        l3[j] = net.l2_biases[j];
        for (int i = 0; i < L2_SIZE; i++)
            l3[j] += (int32_t)l2_out[i] * net.l2_weights[i*L3_SIZE+j];
    }

    // L3 → 輸出
    std::array<uint8_t, L3_SIZE> l3_out;
    for (int j = 0; j < L3_SIZE; j++) l3_out[j] = crelu(l3[j] >> 6);

    int32_t out = net.l3_bias;
    for (int i = 0; i < L3_SIZE; i++) out += (int32_t)l3_out[i] * net.l3_weights[i];

    // Stockfish 縮放：輸出 / 16（量化縮放因子）→ 厘兵
    return out / 16;
}

// 從記憶體中的 .nnue binary 資料載入網路
bool load_nnue_from_memory(const uint8_t* data, size_t size, NNUENetwork& net) {
    // Stockfish .nnue 格式：
    // [4 bytes] version
    // [4 bytes] hash
    // [4 bytes] description length
    // [N bytes] description string
    // [FT weights + biases]
    // [FC weights + biases]
    const uint8_t* ptr = data;
    ptr += 4 + 4;  // skip version + hash
    uint32_t desc_len = *(uint32_t*)ptr; ptr += 4 + desc_len;  // skip description

    // Feature Transformer
    std::memcpy(net.ft_biases,  ptr, L1_SIZE * sizeof(int16_t));
    ptr += L1_SIZE * sizeof(int16_t);
    std::memcpy(net.ft_weights, ptr, HALFKP_SIZE * L1_SIZE * sizeof(int16_t));
    ptr += HALFKP_SIZE * L1_SIZE * sizeof(int16_t);

    // FC Layers（格式依序：biases → weights）
    std::memcpy(net.l1_biases,  ptr, L2_SIZE * sizeof(int32_t)); ptr += L2_SIZE * 4;
    std::memcpy(net.l1_weights, ptr, L1_SIZE*2*L2_SIZE);         ptr += L1_SIZE*2*L2_SIZE;
    std::memcpy(net.l2_biases,  ptr, L3_SIZE * sizeof(int32_t)); ptr += L3_SIZE * 4;
    std::memcpy(net.l2_weights, ptr, L2_SIZE*L3_SIZE);           ptr += L2_SIZE*L3_SIZE;
    std::memcpy(&net.l3_bias,   ptr, sizeof(int32_t));           ptr += 4;
    std::memcpy(net.l3_weights, ptr, L3_SIZE);
    return true;
}
```

#### Step 1-3：在 engine.cpp 整合 NNUE

```cpp
// engine.cpp 頂部加入
#include "nnue_eval.h"
#include "nnue_weights.h"   // 由 xxd -i nn.nnue > nnue_weights.h 生成

// SearchEngine class 內新增兩個成員：
NNUENetwork m_nnue_net;
bool m_nnue_loaded = false;

// init() 函數中載入：
void init(const std::string& book_path) {
    // ...原有初始化代碼（書庫載入、TT 清空等）不動...

    // 新增：載入 NNUE 權重（從編入 header 的 binary 資料）
    if (load_nnue_from_memory(nn_nnue, nn_nnue_len, m_nnue_net)) {
        m_nnue_loaded = true;
        std::cerr << "✅ NNUE loaded: " << nn_nnue_len << " bytes\n";
    }
}

// 修改 evaluate()：NNUE 優先，HCE 作為 fallback
int evaluate(const Board& board, int depth) {
    // 終局判斷不變
    auto [reason, result] = board.isGameOver();
    if (reason != GameResultReason::NONE) {
        if (result == GameResult::LOSE) return -999999 - depth;
        return 0;
    }

    if (m_nnue_loaded) {
        // board 已是相對棋盤（己方恆為白），NNUE 在此基礎上直接計算
        // 無需額外座標轉換
        return nnue_evaluate(board, m_nnue_net);
    }

    // HCE fallback（原有代碼保持不動，改名為 evaluate_hce）
    return evaluate_hce(board, depth);
}
```

#### Step 1-4：打包 NNUE 權重進 .so

```bash
# 1. 將 .nnue binary 轉成 C++ header（陣列形式）
xxd -i nn.nnue > nnue_weights.h
# 輸出長這樣：
#   unsigned char nn_nnue[] = { 0x4e, 0x4e, 0x55, 0x45, ... };
#   unsigned int nn_nnue_len = 20495908;

# 2. 修改 setup.py 確認 include 路徑（deps/ 目錄下）
# 3. 重新編譯（.so 大小增加 ~20 MB）
./pack.sh
# 確認大小
ls -lh model.zip   # 預期：原有 ~2MB + NNUE ~20MB = ~22MB
```

#### Step 1-5：驗證正確性

```python
# test_nnue_eval.py
import sys; sys.path.insert(0, '.')
import chess_engine_d6_han as eng
import numpy as np

engine = eng.SearchEngine()
engine.init("")

# 初始局面的評估應接近 0（Stockfish 初始局面評估約 +18，即白方微弱先手優勢）
# 建立一個初始局面的 observation
obs = np.zeros((8, 8, 111), dtype=np.int8)
# ... 填入初始棋盤（白方視角）
mask = np.ones(4672, dtype=np.int8)

action = engine.solve(obs, mask, -1)
print(f"Initial position action: {action} (should be a valid opening move)")

# 測試評估一致性：對稱局面（翻轉後評估分數應相反）
print("NNUE integration test passed!")
```

---

### 2.5 Phase 2 詳細實作：本地自我對弈資料生成

#### Step 2-1：為何不直接用線上 matchmaker 的資料？

| 資料來源                          | 每天局數                   | 達到 100 萬局面所需時間 |
| --------------------------------- | -------------------------- | ----------------------- |
| 線上 matchmaker                   | ~300 局/天 ≈ ~900 局面/天 | **3 年** ❌       |
| **本地自我對弈（50ms/步）** | ~2,000,000 局面/天         | **12 小時** ✅    |

線上對弈仍有價值：作為「目標領域適配」資料（反映真實對手風格），但量不夠。

#### Step 2-2：自我對弈程式設計

在 `engine.cpp` 中暴露一個額外接口供自我對弈使用：

```cpp
// 在 SearchEngine class 新增
int get_static_eval(const Board& board) {
    return evaluate(board, 0);
}

void set_time_limit_ms(int ms) {
    m_time_limit = ms / 1000.0;
}
```

自我對弈主程式：

```python
# selfplay.py — Python 版本自我對弈（利用現有 .so）
import chess_engine_d6_han as eng
import numpy as np
import struct
import sys
from pathlib import Path

def board_to_obs(board):
    """將 python-chess Board 轉為 PettingZoo 格式 observation（簡化版）"""
    import chess
    obs = np.zeros((8, 8, 111), dtype=np.int8)
    # ... （參考 agent.py 的 _rebuild_relative 逆向）
    return obs

def run_selfplay(num_games: int, time_limit_ms: int, output_path: str):
    """
    執行自我對弈並寫出 .bin 訓練資料。
    格式：每條記錄 = FEN(null終止) + int16評估 + int8結果
    """
    import chess
    engine = eng.SearchEngine()
    engine.init("")

    records = []
    total = 0

    for game_num in range(num_games):
        board = chess.Board()
        game_records = []  # 本局所有記錄

        for ply in range(300):
            if board.is_game_over():
                break

            obs = board_to_obs(board)
            mask = np.zeros(4672, dtype=np.int8)
            # 填入合法動作 mask...

            # 引擎選擇動作
            action = engine.solve(obs, mask, -1)
            eval_score = engine.get_static_eval_from_obs(obs)

            game_records.append({
                'fen': board.fen(),
                'eval': max(-32000, min(32000, eval_score)),  # clamp
                'result': 0  # 稍後填
            })

            # 執行動作
            move = action_to_move(board, action)
            board.push(move)

        # 確定對局結果
        result = board.result()
        result_val = 1 if result == '1-0' else (-1 if result == '0-1' else 0)

        for rec in game_records:
            rec['result'] = result_val
            records.append(rec)

        total += len(game_records)
        if game_num % 100 == 0:
            print(f"[{game_num}/{num_games}] positions={total}", flush=True)

    # 寫出 .bin 格式
    with open(output_path, 'wb') as f:
        for rec in records:
            fen_bytes = rec['fen'].encode() + b'\x00'
            f.write(fen_bytes)
            f.write(struct.pack('<h', rec['eval']))  # int16 little-endian
            f.write(struct.pack('b',  rec['result']))  # int8

    print(f"Done. Wrote {total} positions to {output_path}")

if __name__ == '__main__':
    num_games   = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    time_ms     = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    output_path = sys.argv[3]     if len(sys.argv) > 3 else 'training.bin'
    run_selfplay(num_games, time_ms, output_path)
```

執行（背景持續生成）：

```bash
# 在 d6_cpp 目錄中執行
python selfplay.py 50000 50 training_v1.bin &
echo "PID: $!"

# 監控進度
tail -f /dev/null & while true; do
    echo "$(date): $(wc -c < training_v1.bin) bytes"
    sleep 60
done
```

---

### 2.6 Phase 3 詳細實作：RL 微調

#### Step 3-1：環境安裝

```bash
# 克隆 Stockfish 官方訓練框架
git clone https://github.com/official-stockfish/nnue-pytorch.git
cd nnue-pytorch

# 安裝依賴
pip install torch torchvision numpy tqdm

# 驗證 CUDA（Mac M1/M2 用 MPS）
python -c "
import torch
print('CUDA:', torch.cuda.is_available())
print('MPS (Apple Silicon):', torch.backends.mps.is_available())
"
```

#### Step 3-2：損失函數設計

```python
# mixed_loss.py
import torch
import torch.nn as nn

def eval_to_wdl(eval_cp: torch.Tensor, scale: float = 400.0) -> torch.Tensor:
    """厘兵評估值轉勝率（WDL，0~1）"""
    return torch.sigmoid(eval_cp.float() / scale)

class MixedNNUELoss(nn.Module):
    """
    混合損失 = (1 - λ) × L_supervised + λ × L_rl

    L_supervised：讓 NNUE 評估值接近靜態引擎評估（保留知識）
    L_rl：       讓 NNUE 評估值接近對局最終勝率（針對勝負優化）

    lambda 建議從 0 漸進增加到 0.5，
    讓模型先在監督損失下穩定，再逐漸向 RL 信號靠近。
    """
    def __init__(self, lambda_rl: float = 0.0):
        super().__init__()
        self.lambda_rl = lambda_rl

    def forward(self, pred_cp, target_cp, game_result):
        """
        pred_cp:     模型預測分數（厘兵，當前走棋方視角），shape (B,)
        target_cp:   靜態評估目標（厘兵），shape (B,)
        game_result: 對局結果，1=白贏 0=和 -1=黑贏，shape (B,)
                     注意：需要根據「誰在走棋」把結果轉到當前走棋方視角
        """
        pred_wdl   = eval_to_wdl(pred_cp)
        target_wdl = eval_to_wdl(target_cp)
        result_wdl = (game_result.float() + 1.0) / 2.0  # [-1,1] → [0,1]

        # MSE 損失（也可改用 cross-entropy）
        L_sup = torch.mean((pred_wdl - target_wdl).pow(2))
        L_rl  = torch.mean((pred_wdl - result_wdl).pow(2))

        total = (1.0 - self.lambda_rl) * L_sup + self.lambda_rl * L_rl
        return total, float(L_sup), float(L_rl)
```

#### Step 3-3：微調訓練腳本

```python
# finetune.py
import torch
from pathlib import Path
from tqdm import tqdm
from mixed_loss import MixedNNUELoss

# Lambda 調度表（每 2 個 epoch 增加一次 RL 比例）
LAMBDA_SCHEDULE = [0.0, 0.0, 0.1, 0.1, 0.2, 0.2, 0.3, 0.3, 0.4, 0.5]

def finetune(
    pretrained_path: str,
    data_path: str,
    output_path: str,
    epochs: int = 10,
    lr: float = 1e-4,          # 微調用低學習率（防止遺忘）
    batch_size: int = 8192,
):
    device = torch.device(
        'cuda' if torch.cuda.is_available() else
        'mps'  if torch.backends.mps.is_available() else 'cpu'
    )
    print(f"Device: {device}")

    # 載入 nnue-pytorch 的模型（需根據 nnue-pytorch 版本調整）
    from serialize import NNUEReader, NNUEWriter
    from model import NNUE
    reader = NNUEReader(open(pretrained_path, 'rb'), NNUE)
    model = reader.model.to(device)
    print(f"Model loaded from: {pretrained_path}")

    # 資料集（nnue-pytorch 提供 DataLoader）
    from dataset import SparseBatchDataset
    dataset = SparseBatchDataset(data_path, batch_size)
    loader  = torch.utils.data.DataLoader(dataset, batch_size=None, num_workers=2)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_loss = float('inf')

    for epoch in range(epochs):
        lambda_rl = LAMBDA_SCHEDULE[min(epoch, len(LAMBDA_SCHEDULE)-1)]
        criterion = MixedNNUELoss(lambda_rl=lambda_rl)
        model.train()

        epoch_loss = 0.0
        n_batches = 0

        for batch in tqdm(loader, desc=f"Epoch {epoch+1}/{epochs} λ={lambda_rl:.1f}"):
            # batch 包含：features(sparse), eval_targets, results
            features, targets, results = batch
            features = features.to(device)
            targets  = targets.to(device).float()
            results  = results.to(device).float()

            optimizer.zero_grad()
            predictions = model(features)

            loss, L_sup, L_rl = criterion(predictions, targets, results)
            loss.backward()

            # 梯度裁剪防止 fine-tune 震盪
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            epoch_loss += float(loss)
            n_batches += 1

        scheduler.step()
        avg_loss = epoch_loss / max(n_batches, 1)
        lr_cur = scheduler.get_last_lr()[0]
        print(f"  Loss={avg_loss:.6f} | L_sup={L_sup:.4f} | L_rl={L_rl:.4f} | LR={lr_cur:.2e}")

        # 每個 epoch 都保存一個 checkpoint
        ckpt_path = output_path.replace('.nnue', f'_ep{epoch+1}.nnue')
        with open(ckpt_path, 'wb') as f:
            writer = NNUEWriter(f)
            writer.write(model)
        print(f"  Saved: {ckpt_path}")

        if avg_loss < best_loss:
            best_loss = avg_loss
            with open(output_path, 'wb') as f:
                writer = NNUEWriter(f)
                writer.write(model)
            print(f"  ★ New best! Saved to: {output_path}")

    print(f"\nFine-tuning complete. Best model: {output_path}")

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--pretrained', default='nn.nnue')
    p.add_argument('--data',       default='training.bin')
    p.add_argument('--output',     default='finetuned.nnue')
    p.add_argument('--epochs',     type=int,   default=10)
    p.add_argument('--lr',         type=float, default=1e-4)
    args = p.parse_args()

    finetune(args.pretrained, args.data, args.output, args.epochs, args.lr)
```

#### Step 3-4：部署新 NNUE 並測試

```bash
# 1. 將微調後的 .nnue 轉成 C++ header
xxd -i finetuned.nnue > nnue_weights.h

# 2. 重新編譯（本地 macOS + Docker Linux）
./pack.sh

# 3. 本地正確性驗證
python test_timeout_fix.py    # 現有測試套件

# 4. 上傳新版本到 ML Arena（替換 model.zip）
# 可用 scp / curl / 平台 web UI 上傳

# 5. 監控 Elo 曲線
caffeinate -dims .venv/bin/python matchmaker_rl_11/matchmaker.py
```

---

### 2.7 迭代計畫與評估指標

| 週次          | 任務                                | 成功標準                               |
| ------------- | ----------------------------------- | -------------------------------------- |
| 第 1 小時     | 整合 Stockfish 現成 NNUE（nn.nnue） | 初始局面評估 ≈ 0~30，速度 < 3µs/節點 |
| 第 2 小時     | A/B 測試 NNUE vs HCE                | NNUE 版本線上 Elo 提升 ≥ +50          |
| 第 3~24 小時  | 本地自我對弈生成 100 萬局面         | training.bin ≥ 300 MB                 |
| 第 25~26 小時 | 第一輪 RL 微調（λ 從 0.1 開始）    | 微調版 Elo 再提升 ≥ +20               |
| 第 27~28 小時 | 分析失敗局面，增加開局多樣性        | 弱點（如複雜殘局）改善                 |
| 持續          | 每週一次微調迭代                    | 每小時 Elo 穩定成長 ≥ +10            |

---

### 2.8 風險矩陣

| 風險                                                | 可能性 | 影響 | 緩解策略                                               |
| --------------------------------------------------- | ------ | ---- | ------------------------------------------------------ |
| NNUE 推論速度慢（>3µs/節點）導致搜尋深度下降       | 中     | 高   | 改用 HalfKP_128 更小架構；或加 SIMD 優化               |
| HalfKP 特徵計算有 bug（評估值離奇）                 | 中     | 高   | 用已知局面（初始局面評估 ≈ 0）做單元測試              |
| RL 微調導致 catastrophic forgetting（棋力大幅下降） | 低     | 高   | λ 始終 ≤ 0.5；監督損失不消失；保存所有 checkpoint    |
| 自我對弈資料同質性太高（模式單一，過擬合特定開局）  | 中     | 中   | 加入隨機開局 FEN（Book 之外的隨機走法）多樣化          |
| .nnue 格式解析錯誤（版本不符）                      | 低     | 高   | 驗證 magic number（前 4 bytes = 'NNUE'）；測試多個版本 |
| 量化誤差（float → int8 精度損失導致評估抖動）      | 低     | 中   | 改用 int16 或使用 quantization-aware training          |

---

*如需立即開始 Phase 1 的 NNUE 整合，可用 `/goal` 命令啟動完整實作流程。*
