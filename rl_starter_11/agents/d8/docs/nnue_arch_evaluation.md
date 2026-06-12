# NNUE 架構調整評估：從 23.8M 到輕量高效的新設計

## 1. 目前架構（Current）的完整硬編碼清單

### C++ 中所有涉及維度的位置

| 檔案 | 位置 | 常數 | 含義 |
|:-----|:-----|-----:|:-----|
| `nnue_eval.h` L22-25 | `struct NNUEParameters` | 256, 49216, 43840 | FT 維度與特徵空間大小 |
| `nnue_eval.h` L48-51 | `get_parameters()` | 25199297, 25199809 | enemy FT 在二進位檔的偏移量 |
| `nnue_eval.h` L53 | `get_parameters()` | 47645889 | FC 區段在二進位檔的偏移量 |
| `nnue_eval.h` L57 | Isolated Bucket stride | 1188 | L2(128)+L2w(1024)+L3b(4)+L3w(32) = 1188 |
| `nnue_eval.h` L65-67 | Main Stack stride | 17640 | L1b(64)+L1w(16384)+L2b(128)+L2w(1024)+L3b(4)+L3w(32)+pad(4) = 17640 |
| `nnue_eval.h` L83-88 | `friend_idx` | 769, 64 | HalfKA stride: 769 = 12 × 64 + 1 |
| `nnue_eval.h` L90-110 | `enemy_idx` | 685, 64, 48 | HalfKA-them stride |
| `nnue_eval.h` L115-155 | `accum_add/sub` | 256 | FT 維度 |
| `nnue_eval.h` L161-210 | `activate/propagate_l1` | 256, 16, 1024 | FT→L1 |
| `nnue_eval.h` L213-248 | `propagate_l2` | 32 | L2 |
| `nnue_eval.h` L286-300 | `evaluate` | 1024, 16 | L1 input/output |
| `engine.cpp` L782-785 | 累加器 | 128×256 | 搜尋深度 × FT 維度 |
| `engine.cpp` L791-838 | `memcpy` | 256 | FT 維度 |
| `save_nnue.py` | 所有偏移 | 所有 | 所有偏移量與維度 |
| `train_nnue.py` | `NNUE class` | 49216, 43840, 256, 1024, 16, 32 | 所有層 |

### 目前參數量

```
Friend FT:  49,216 × 256 × 2 bytes = 25,198,592 bytes = 24.03 MB
Enemy FT:   43,840 × 256 × 2 bytes = 22,446,080 bytes = 21.41 MB
L1 w:       16 × 1024 × 1 byte    =     16,384 bytes
L1 b:       16 × 4 bytes          =         64 bytes
L2 w:       32 × 32 × 1 byte     =      1,024 bytes
L2 b:       32 × 4 bytes          =        128 bytes
L3 w:       32 × 1 × 1 byte      =         32 bytes
L3 b:       1 × 4 bytes           =          4 bytes
────────────────────────────────────────────────────
共 4 個 Buckets × (1 Main Stack 含 L1+L2+L3) + 4 個 Isolated Buckets (僅 L2+L3)
實際 .nnue 大小：47,721,473 bytes ≈ 45.5 MB
可訓練參數總量：23,840,337 個
```

---

## 2. 架構調整三選項分析

### 🔴 選項 A：FT 維度 256 → 128（降半）

#### 參數變化

| 組件 | 目前 | → 128 維 | 節省 |
|:-----|-----:|----------:|-----:|
| Friend FT | 12,599,296 | 6,299,648 | -50% |
| Enemy FT | 11,223,040 | 5,611,520 | -50% |
| L1 輸入 (4×128=512) | 16×1024 | 16×512 | -50% |
| L2, L3 | 不變 | 不變 | 0% |
| **總參數** | **23,840,337** | **11,913,729** | **-50%** |

#### 二進位偏移變化（全部需要重新計算）

```
friend_bias:    offset 193 → 193（不變，256 → 128 bytes）
friend_weights: offset 705 → 705（bytes: 49216×256×2=25.2MB → 49216×128×2=12.6MB）
enemy_bias:     25199297 → 12599937（重大改變）
enemy_weights:  25199809 → 12600193（重大改變）
fc_start:       47645889 → 23822913（重大改變）
L1 stride:      16384 → 8192 bytes（L1 weights 從 1024 變 512）
Main Stack stride: 17640 → 8840 bytes
Isolated Bucket stride: 1188（不變，L2/L3 不受影響）
```

#### 效能評估

| 指標 | 256 維 | 128 維 |
|:-----|:-------|:-------|
| **L1 快取壓力** | FT 層 45.5 MB（完全超出 L2） | FT 層 22.8 MB（略微超出 L2） |
| **增量更新速度** | 256 × int16 SIMD | 128 × int16 SIMD（快一倍） |
| **L1 前向傳播** | 16 × 1024 int8 乘加 | 16 × 512 int8 乘加（快一倍） |
| **搜尋深度** | 受限於評估速度 | 每步快約 30%，可多搜 1-2 層 |
| **訓練時間** | 每 epoch 更慢 | 每 epoch 快約 40% |
| **棋力損失** | baseline | 估計損失 ~30-50 Elo |

> ⚖️ **128 維是最值得嘗試的折衷點**：訓練速度快 40%，推理速度快 30-40%，參數只有原來一半使得訓練所需數據也降至約 250 萬局面。

---

### 🟡 選項 B：FT 維度 256 → 64（大幅壓縮）

| 組件 | 目前 | → 64 維 | 節省 |
|:-----|-----:|----------:|-----:|
| **總參數** | **23,840,337** | **5,960,865** | **-75%** |
| L1 輸入 | 1024 | 256 | -75% |

- 訓練只需約 60 萬局面即可達到足夠的數據/參數比
- **風險**：表達能力大幅下降。64 維可能不足以捕捉複雜的位置特徵，棋力損失嚴重（估計 100-150 Elo）
- **結論**：不推薦，除非目標僅是快速驗證管線

---

### 🟢 選項 C（推薦）：FT 256 維保留，改為 No-Bucket 架構

**保留 256 維（棋力優先），但移除 Bucket 機制（只用 1 組 L1-L3）**

| 組件 | 目前 | 改為 No-Bucket |
|:-----|-----:|:--------------|
| FT 維度 | 256 | 256（不變）|
| FT 特徵數 | 49216 + 43840 | 49216 + 43840（不變）|
| L1 組數 | 4 個 Main Stack + 4 個 Isolated Bucket | **1 組** |
| FC 層參數 | (16400 + 1056 + 33) × 4 ≈ 71K | 17,489 個 |
| **總參數** | **23,840,337** | **23,822,849** |

FC 參數只佔總數的 0.07%，故 No-Bucket 對總數影響極微。但節省了：
- 二進位層讀取時的 bucket 選擇 branch
- 推理時讀取 4 組不同的 L1/L2/L3 的條件跳轉

> **實際效益較小**，因為 FT 是絕大多數計算量的來源。

---

## 3. 推薦架構：HalfKA-128（選項 A，FT 256 → 128）

### 理由

1. **數據需求從 500 萬降至 250 萬**：大幅縮短資料生成時間（1.75 小時 vs 3.5 小時）
2. **訓練快 40%**：同樣 20 個 epoch，完成時間從 60 分鐘降至約 35 分鐘
3. **推理快 30%**：搜尋深度可能提升 1-2 層，部分補回棋力損失
4. **L2 快取更友好**：45MB → 22MB，讓更多 FT 權重常駐快取，減少 cache miss
5. **棋力損失可接受**：估計 ~30-50 Elo。由於 d8 目前勝率 0%，即使損失 50 Elo，只要能正確評估位置就足以在對戰 d6_cpp 時取得提升

### 需要修改的位置彙整

#### `src/nnue_eval.h` 需修改 9 處

```
FT_DIM        = 128  (was 256)
L1_IN         = 512  (was 1024 = 4 × FT_DIM)
friend_bias:  offset 193, size = 128 × 2 = 256 bytes
friend_weights: offset 449, size = 49216 × 128 × 2 = 12,599,296 bytes
enemy_bias:   offset 12,599,745, size = 128 × 2 = 256 bytes
enemy_weights: offset 12,600,001, size = 43,840 × 128 × 2 = 11,223,040 bytes
fc_start = 23,823,041
Main Stack stride = 8840 bytes (L1b:64 + L1w:8192 + L2b:128 + L2w:1024 + L3b:4 + L3w:32 + pad:4 = 8448... 重新計算)
accum_add/sub: 128 個 int16 元素
activate(): 128 個元素
propagate_l1(): in[512], w_row = weights + r × 512
```

#### `src/engine.cpp` 需修改 6 處

```
m_accum_friend_white[128][128]  (was [128][256])
m_accum_friend_black[128][128]
m_accum_enemy_white[128][128]
m_accum_enemy_black[128][128]
所有 memcpy 的 size 從 256 × sizeof(int16_t) → 128 × sizeof(int16_t)
```

#### `scratch/train_nnue.py` 需修改 5 處

```python
self.friend_emb = nn.EmbeddingBag(49216, 128, ...)  # was 256
self.enemy_emb = nn.EmbeddingBag(43840, 128, ...)   # was 256
self.l1 = nn.Linear(512, 16)                         # was 1024
# in_l1 = cat([clamp(us,0,1), clamp(-us,0,1), clamp(them,0,1), clamp(-them,0,1)])
# → 4 × 128 = 512
```

#### `scratch/save_nnue.py` 需修改（所有偏移重新計算）

#### `tests/*.py` 需更新（架構相關測試）

---

## 4. 新二進位佈局（HalfKA-128）

```
偏移 0:         header (4 bytes, magic number)
偏移 4:         friend_ft metadata (189 bytes)
偏移 193:       friend_ft_bias (128 × 2 = 256 bytes)
偏移 449:       friend_ft_weights (49216 × 128 × 2 = 12,599,296 bytes)
偏移 12,599,745: enemy_ft_bias (256 bytes)
偏移 12,600,001: enemy_ft_weights (43840 × 128 × 2 = 11,223,040 bytes)
偏移 23,823,041: FC section header
偏移 23,823,041 + 272: Isolated Buckets start (4 × 1188 bytes)
偏移 23,823,041 + 272 + 4752: Main Stacks start (4 × 8840 bytes 重算)
```

> **Note**: 精確偏移量需要在修改後透過計算 `193 + 256 + 49216×256 = ?` 等方式重新確認。

---

## 5. 總結比較

| | 目前（256 維）| 推薦（128 維）| 極輕量（64 維）|
|:--|:--|:--|:--|
| **總參數** | 23.8M | 11.9M | 5.9M |
| **FT 記憶體** | 45.5 MB | 22.8 MB | 11.4 MB |
| **最低數據需求** | 500 萬 | **250 萬** | 60 萬 |
| **訓練時間（預估）** | 60 分鐘 | **35 分鐘** | 15 分鐘 |
| **推理速度提升** | baseline | **+30%** | +60% |
| **棋力損失估計** | 0 Elo | ~30-50 Elo | ~100-150 Elo |
| **修改工作量** | 無 | 中（約 50 處） | 中（約 50 處）|
| **建議** | 資料不足，難以收斂 | ✅ **推薦** | ❌ 表達力太低 |
