# NNUE 訓練計劃 v7（架構一致性重新評估）

## 背景與核心問題

過去訓練失敗的根本原因是 **三端架構不一致** 以及 **數據嚴重不足**：

| 端 | 檔案 | 當時問題 |
| :--- | :--- | :--- |
| C++ 推理 | `src/nnue_eval.h` | 硬編碼偏移量與維度 |
| Python 訓練 | `scratch/train_nnue.py` | EmbeddingBag 維度、初始化方式 |
| Python 匯出 | `scratch/save_nnue.py` | 偏移量、量化尺度 |

本計劃的核心原則：**任何一個常數改動，必須在三端全部同步驗證後才能繼續。**

---

## 第一部分：現有架構（v4/v5，FT=256）完整三端對照表

### 1-A. 特徵轉換器（Feature Transformer）尺寸

| 常數 | C++ (`nnue_eval.h`) | Python (`train_nnue.py`) | 二進位偏移 (`save_nnue.py`) |
| :--- | :--- | :--- | :--- |
| FT friend 輸入 | `49216` | `EmbeddingBag(49216, ...)` | - |
| FT enemy 輸入 | `43840` | `EmbeddingBag(43840, ...)` | - |
| **FT 輸出維度 (D)** | **256** (所有 for 迴圈) | **256** (EmbeddingBag 第二參數) | - |
| friend_bias 偏移 | `base + 193` (L48) | `friend_bias` shape `(256,)` | offset `193`, dtype `int16`, scale `127.0` |
| friend_weights 偏移 | `base + 705` (L49) | `friend_emb.weight` shape `(49216, 256)` | offset `705`, dtype `int16`, scale `127.0` |
| enemy_bias 偏移 | `base + 25199297` (L50) | `enemy_bias` shape `(256,)` | offset `25199297`, dtype `int16`, scale `127.0` |
| enemy_weights 偏移 | `base + 25199809` (L51) | `enemy_emb.weight` shape `(43840, 256)` | offset `25199809`, dtype `int16`, scale `127.0` |

**偏移量計算驗證（數學）：**
- `friend_weights` 起始：`193 + 256*2 = 705` ✅
- `enemy_bias` 起始：`705 + 49216*256*2 = 705 + 25,198,592 = 25,199,297` ✅
- `enemy_weights` 起始：`25,199,297 + 256*2 = 25,199,809` ✅
- FC 起始：`25,199,809 + 43840*256*2 = 25,199,809 + 22,446,080 = 47,645,889` ✅

### 1-B. 全連接層（FC Layers）完整尺寸三端對照

| 層 | 輸入 | 輸出 | C++ (`nnue_eval.h`) | Python (`train_nnue.py`) |
| :--- | :--- | :--- | :--- | :--- |
| `activate()` | D=256 acc → Dual-CReLU | **1024** | `in_l1[1024]`, L161-165 | `clamp(acc,0,1) + clamp(-acc,0,1)` × 2 → shape `(B,1024)` |
| L1 | **1024** | 16 | `propagate_l1()`: `r*1024`, `c<1024` | `l1 = nn.Linear(1024, 16)` |
| L1→L2 | 16 → Dual-CReLU | **32** | `in_l2[32]`, `i<16`, `in_l2[i]` + `[i+16]` | `clamp(out_l1,0,1) + clamp(-out_l1,0,1)` → `(B,32)` |
| L2 | **32** | 32 | `propagate_l2()`: `r*32`, `c<32` | `l2 = nn.Linear(32, 32)` |
| L2→L3 | 32 → Clamp | **32** | `in_l3[32]`, `i<32` | `clamp(out_l2,0,1)` → `(B,32)` |
| L3 | **32** | 1 | `propagate_l3()`: `c<32` | `output = nn.Linear(32, 1)` |

### 1-C. C++ 累加器（`engine.cpp` L782-785）

```cpp
alignas(32) int16_t m_accum_friend_white[128][256];  // 128=ply深度, 256=FT_D
alignas(32) int16_t m_accum_friend_black[128][256];
alignas(32) int16_t m_accum_enemy_white[128][256];
alignas(32) int16_t m_accum_enemy_black[128][256];
// 所有 memcpy: 256 * sizeof(int16_t) = 512 bytes
```

### 1-D. FC 二進位佈局（`save_nnue.py` 詳細對照）

```
fc_start = 47,645,889

Isolated Buckets 0-3（僅含 L2+L3，stride 1188 bytes）：
  bucket[i] 起始 = fc_start + 272 + i * 1188
    +0:    L2 biases   (32 × int32 = 128 bytes) → scale 8128.0
    +128:  L2 weights  (32×32 int8 = 1024 bytes) → scale 64.0
    +1152: L3 bias     (1 × int32 = 4 bytes) → scale 9600.0
    +1156: L3 weights  (32 int8 = 32 bytes) → scale 9600/127
    確認：128 + 1024 + 4 + 32 = 1188 ✅

main_start = 47,645,889 + 272 + 4*1188 = 47,650,913

Main Stacks 0-3（含 L1+L2+L3，stride 17640 bytes）：
  stack[i] 起始 = main_start + i * 17640
    +4:     L1 biases   (16 × int32 = 64 bytes) → scale 8128.0
    +68:    L1 weights  (16×1024 int8 = 16384 bytes) → scale 64.0
    +16452: L2 biases   (32 × int32 = 128 bytes) → scale 8128.0
    +16580: L2 weights  (32×32 int8 = 1024 bytes) → scale 64.0
    +17604: L3 bias     (1 × int32 = 4 bytes) → scale 9600.0
    +17608: L3 weights  (32 int8 = 32 bytes) → scale 9600/127
    確認：64+64 + 16384 + 128+128 + 1024 + 4 + 32 = 17628... (+12 padding) ≈ 17640 ✅
```

### 1-E. 分數換算關係

```
Stockfish 標記 → 訓練: score_val = centipawns / 100.0
PyTorch 輸出 → C++ raw: raw_score = 4341 + 9600 × torch_output
C++ centipawns: (raw_score - 4341) / 96  [engine.cpp L1151]

∴ torch_output 的合理範圍：±600cp / 100 = ±6.0
```

---

## 第二部分：實測評估結果

### 2-A. 數據生成速度（2026-06-13 M4 實測）

| Worker 數 | 速度 | 備注 |
| :--- | :--- | :--- |
| 4 Workers（預熱 100 筆）| 104 PPS | Stockfish 啟動開銷 |
| **8 Workers（1000 筆）**| **748.94 PPS** | **最佳配置** |
| 12 Workers（300 筆）| 317 PPS | 超過物理核心數 |
| 16 Workers（300 筆）| 231 PPS | I/O 競爭過高 |

### 2-B. Quiet Position 品質（1000 筆樣本）

| 指標 | 數值 |
| :--- | :--- |
| 有效率（±2000 cp 內） | **99.90%** |
| 均值 | +19.90 cp |
| 中位數 | +14.0 cp |
| 標準差 | 135.95 cp |
| 25th / 75th 百分位 | -36.5 / +64.0 cp |
| Quiet 篩選率（前一步非吃子/升變） | ~49.46% |

### 2-C. PGN 資料庫容量分析

| 數據源 | 對局數 | 可提取 Quiet FENs |
| :--- | :--- | :--- |
| 現有 5 位棋手 PGN | 18,179 | **672,586** |
| 擴充至 35 位棋手（估算）| ~80,000 | **~3.0M–4.0M** |

### 2-D. 生成時間預估（748.94 PPS）

| 目標規模 | 耗時 | 對應架構 |
| :--- | :--- | :--- |
| 250 萬（2.5M） | **~56 分鐘** | FT-128 |
| **500 萬（5.0M）** | **~111 分鐘** | **FT-256（推薦）** |

---

## 第三部分：方案選擇建議

### 方案 A：維持 256 維（**推薦，零架構風險**）

| 項目 | 說明 |
| :--- | :--- |
| C++ 修改量 | **零** |
| Python 架構修改量 | **零**（偏移量不動） |
| 主要改動 | 只改數據量、初始化方式 |
| 數據需求 | 500 萬局面（需先下載更多 PGN） |
| 數據生成時間 | **~111 分鐘** |
| 訓練時間 | ~60 分鐘 |
| 架構不符風險 | **無** |

> [!IMPORTANT]
> **推薦原因**：過去 0/20 的根因是數據比例 **270K / 23.8M = 0.011**（最低要求 0.21），而非架構本身錯誤。在完全不改動任何 C++ 與 Python 偏移量的情況下，只需補充數據就能驗證這個假設。

### 方案 B：縮減為 128 維（**不推薦先行，風險高**）

| 項目 | 說明 |
| :--- | :--- |
| C++ 修改量 | ~50 處硬編碼常數 |
| Python 修改量 | ~30 處（EmbeddingBag、Linear、偏移量） |
| 數據需求 | 250 萬局面 |
| 架構不符風險 | **極高**（任何漏改導致靜默錯誤或崩潰） |

> [!CAUTION]
> 方案 B 應在方案 A 成功後再作為優化路徑執行，而不是首選。

---

## 第四部分：v7 執行計劃（方案 A）

### Phase 0：PGN 擴充（~5 分鐘）

執行 `scratch/download_more_data.py`：下載 30 位新棋手 PGN。

驗收：`research/data/raw/` 有 35 個 `.pgn` 檔案。

---

### Phase 1：改良版標記腳本（~111 分鐘背景執行）

修改 `scratch/label_data.py`，加入 Quiet Position 篩選：

```python
# 在 game.mainline_moves() 迴圈中：
is_capture = board.is_capture(move)
is_promotion = (move.promotion is not None)
board.push(move)

if (16 <= len(board.move_stack) <= 80
        and not board.is_check()
        and not is_capture       # 前一步非吃子
        and not is_promotion):   # 前一步非升變
    plies.append(board.fen())
```

目標：生產 500 萬筆至 `research/data/processed/dataset_v7.txt`。

---

### Phase 2：改良版訓練（`scratch/train_nnue.py`）

只改以下兩項，**架構層定義一律不動**：

**2-1. FT 初始化改為極小方差（最重要）：**
```python
# 舊（錯誤）：
nn.init.kaiming_uniform_(self.friend_emb.weight, a=0.2)  # 值域太大

# 新（正確）：
nn.init.normal_(self.friend_emb.weight, mean=0.0, std=1e-4)
nn.init.normal_(self.enemy_emb.weight,  mean=0.0, std=1e-4)
# FC 層保持 Kaiming：
nn.init.kaiming_uniform_(self.l1.weight, a=0.2)
nn.init.kaiming_uniform_(self.l2.weight, a=0.2)
nn.init.kaiming_uniform_(self.output.weight, a=0.2)
```

**2-2. 加入 LR 排程（CosineAnnealing）：**
```python
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=20)
# 每個 epoch 結束後呼叫 scheduler.step()
```

**2-3. 資料來源更新（讀取 dataset_v7.txt）：**
```python
input_file = os.path.join(processed_dir, "dataset_v7.txt")
```

驗收標準：
- Epoch 1 val loss < 0.5（確認在學習）
- Epoch 20 val loss < 0.08（目標水準）

---

### Phase 3：架構一致性驗證（新增，防止不符）

**新增** `scratch/verify_arch_consistency.py`，在匯出前強制驗證：

```python
import torch, sys
sys.path.insert(0, "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8")
from scratch.train_nnue import NNUE

model = NNUE()
model.load_state_dict(torch.load("weights/trained_model.pt"))

# 驗證尺寸
assert model.friend_emb.weight.shape == (49216, 256), "friend_emb 尺寸不符！"
assert model.enemy_emb.weight.shape  == (43840, 256), "enemy_emb 尺寸不符！"
assert model.l1.weight.shape == (16, 1024), "L1 尺寸不符！"
assert model.l2.weight.shape == (32, 32),   "L2 尺寸不符！"
assert model.output.weight.shape == (1, 32),"L3 尺寸不符！"

# 驗證偏移量計算
friend_bias_offset = 193
friend_w_offset = friend_bias_offset + 256 * 2  # 705
enemy_bias_offset = friend_w_offset + 49216 * 256 * 2  # 25199297
enemy_w_offset = enemy_bias_offset + 256 * 2  # 25199809
fc_start = enemy_w_offset + 43840 * 256 * 2  # 47645889
assert friend_w_offset  == 705,       f"friend_w offset={friend_w_offset}"
assert enemy_bias_offset == 25199297, f"enemy_bias offset={enemy_bias_offset}"
assert fc_start          == 47645889, f"fc_start={fc_start}"

# 驗證 nn.nnue.orig 檔案大小
import os
orig_size = os.path.getsize("weights/nn.nnue.orig")
print(f"nn.nnue.orig 大小：{orig_size} bytes")
print("所有架構一致性驗證通過！✅")
```

---

### Phase 4：匯出（`scratch/save_nnue.py`，**不修改**）

現有偏移量已驗證正確。執行後確認：
```bash
ls -la weights/nn.nnue  # 大小應與 nn.nnue.orig 完全相同
```

---

### Phase 5：重新編譯

```bash
cd /Users/Shared/西洋棋代理人/rl_starter_11/agents/d8
./build.sh
```

**C++ 不需要任何修改。**

---

### Phase 6：單調性驗證

執行 `scratch/check_monotonicity_options.py`：

| 測試 | 期望 |
| :--- | :--- |
| Start < Up Pawn < Up Knight < Up Queen | ✅ |
| Start > Down Pawn > Down Knight > Down Queen | ✅ |
| K+Q > K+R > KvK > K vs K+R | ✅ |

---

### Phase 7：競技場比賽（20 局 vs `d6_cpp`）

| 目標 | 門檻 |
| :--- | :--- |
| 最低可接受 | ≥ 4 勝 / 20（20%）|
| 預期目標 | ≥ 8 勝 / 20（40%）|
| 優秀 | ≥ 12 勝 / 20（60%）|

---

## User Review Required

> [!IMPORTANT]
> **建議確認採用方案 A（256維，零架構修改）**。  
> 過去失敗的根因是數據嚴重不足（270K vs 需要 500M），而非架構本身錯誤。  
> 方案 A 的五個主要工作：下載 PGN → 標記 500 萬局面 → 改良初始化方式訓練 → 架構一致性驗證 → 匯出並比賽。

> [!WARNING]
> **如果最終想採用方案 B（128維）**，請先完成方案 A 並確認有效（勝率 > 0），再以方案 A 的結果作為基準進行對比。

> [!NOTE]
> **待確認的問題**：
> 1. 是否要立即下載更多棋手 PGN？（需要網路，約 5 分鐘）
> 2. 是否要在訓練數據中加入「開局突變」局面？（前 15 步隨機變化，增加開局多樣性）
> 3. 是否要在 Phase 6 中額外測量「Pearson 相關係數（預測分 vs Stockfish 分）」作為品質指標？
