# NNUE 訓練計劃（v6：HalfKA-128 輕量架構）

## 背景

根據 [nnue_arch_evaluation.md](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/docs/nnue_arch_evaluation.md) 與 [nnue_v4_feasibility_analysis.md](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/docs/nnue_v4_feasibility_analysis.md) 的深度分析，決定對 NNUE 架構進行以下調整：

**核心變更：FT 嵌入維度 256 → 128**

| 指標 | v5 (256維) | v6 (128維) | 差異 |
| :--- | :--- | :--- | :--- |
| 總參數量 | 23.8M | **11.9M** | -50% |
| FT 記憶體 | 45.5 MB | **22.8 MB** | -50% |
| 最低訓練數據 | 500 萬 | **250 萬** | -50% |
| 數據標記生成時間 | ~1.85 小時 (5M) | **~56 分鐘 (2.5M)** | -50% |
| 推理速度 | baseline | **+30%** | 搜尋更深 |
| 訓練時間 | ~60 分鐘 | **~35 分鐘** | -42% |
| 估計棋力損失 | - | ~30-50 Elo（可接受） | |

---

## Phase 0：大規模數據生成（更新）

### [NEW] [download_more_data.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/download_more_data.py) 與 [label_data.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/label_data.py)

利用 35 位大師級棋手的 PGN 對局（約 8-10 萬場對局，掃描約 700 萬步），提取 **Quiet Positions** 並使用本地 Stockfish 進行 8 核心並行標記。

**數據提取與標記規格**：
- **Quiet Position 篩選**：限制在第 16 到 80 步之間、無將軍、且前一步棋不是吃子（Capture）或升變（Promotion）的局面（佔總步數約 49.46%）。
- **標記引擎**：Stockfish 5ms/d10 限制搜尋評估。
- **分數限制**：`-2000 ≤ score ≤ 2000`（排除大勝大敗或強制殺局面，過濾率約 0.1%）。
- **保存格式**：`FEN,score`。
- **目標數據量**：
  - 若採用 **128維** 結構：**250 萬 (2.5M)** 個 unique quiet 局面。
  - 若採用 **256維** 結構：**500 萬 (5.0M)** 個 unique quiet 局面。

**實測標記速度與預計時間**：
- 實測速度為 **748.94 PPS (Positions Per Second)** (Apple M4 實體 8 Workers)。
- 250 萬數據生成時間：**~56 分鐘**。
- 500 萬數據生成時間：**~1.85 小時**。

---

## Phase 1：C++ 架構調整（FT 256 → 128）

### [MODIFY] [src/nnue_eval.h](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/src/nnue_eval.h)

定義新常數並修改所有涉及維度的位置：

```cpp
FT_DIM = 128 (was 256)
L1_IN  = 512 (was 1024 = 4 × FT_DIM)
```

關鍵偏移量更新（新的二進位佈局）：

| 資料段 | 舊偏移 | 新偏移 | 大小 |
| :--- | ---: | ---: | ---: |
| friend_ft_bias | 193 | 193 | 256 bytes → **256 bytes** (128×2) |
| friend_ft_weights | 705 | **449** | 25,198,592 → **12,599,296** bytes |
| enemy_ft_bias | 25,199,297 | **12,599,745** | 256 bytes → 256 bytes |
| enemy_ft_weights | 25,199,809 | **12,600,001** | 22,446,080 → **11,223,040** bytes |
| FC section start | 47,645,889 | **23,823,041** | - |
| Isolated Bucket stride | 1,188 | **1,188**（不變，L2/L3 無關）| per bucket |
| Main Stack stride | 17,640 | **8,840** | (L1b:64 + L1w:8,192 + L2b:128 + L2w:1,024 + L3b:4 + L3w:32 + pad) |

需修改的函式：
- `accum_add()` / `accum_sub()`：`256` → `128` 個元素
- `activate()`：`for (int i = 0; i < 256; ...)` → `128`
- `propagate_l1()`：`in[1024]` → `in[512]`、`w_row = weights + r * 1024` → `r * 512`、`for (int c = 0; c < 1024; ...)` → `512`

### [MODIFY] [src/engine.cpp](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/src/engine.cpp)

累加器維度更新：

```cpp
// 改前
alignas(32) int16_t m_accum_friend_white[128][256];
alignas(32) int16_t m_accum_friend_black[128][256];
alignas(32) int16_t m_accum_enemy_white[128][256];
alignas(32) int16_t m_accum_enemy_black[128][256];

// 改後
alignas(32) int16_t m_accum_friend_white[128][128];
alignas(32) int16_t m_accum_friend_black[128][128];
alignas(32) int16_t m_accum_enemy_white[128][128];
alignas(32) int16_t m_accum_enemy_black[128][128];
```

所有 `memcpy` 的 size：`256 * sizeof(int16_t)` → `128 * sizeof(int16_t)`

---

## Phase 2：Python 訓練架構調整

### [MODIFY] [scratch/train_nnue.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/train_nnue.py)

```python
# 架構更改
self.friend_emb = nn.EmbeddingBag(49216, 128, mode="sum")  # was 256
self.enemy_emb  = nn.EmbeddingBag(43840, 128, mode="sum")  # was 256
self.l1 = nn.Linear(512, 16)   # was 1024 (512 = 4 × 128)
# L2, L3 不變

# 初始化更改（FT: 極小方差，FC: Kaiming）
nn.init.normal_(self.friend_emb.weight, mean=0.0, std=1e-4)
nn.init.normal_(self.enemy_emb.weight,  mean=0.0, std=1e-4)
nn.init.kaiming_uniform_(self.l1.weight, a=0.2)
nn.init.kaiming_uniform_(self.l2.weight, a=0.2)
nn.init.kaiming_uniform_(self.output.weight, a=0.2)
```

**數據混合**（250 萬自我對弈 + 10 萬端局合成 + 5 萬開局突變 = **265 萬局面**）

**訓練超參數**：

| 參數 | 值 |
| :--- | :--- |
| Optimizer | Adam(lr=1e-3, weight_decay=1e-4) |
| LR Schedule | CosineAnnealingLR(T_max=20) |
| Loss | HuberLoss(delta=1.0) |
| Batch size | 4096 |
| Epochs | 20（Early Stopping patience=5）|
| Device | MPS (Apple Silicon M4) |

---

## Phase 3：量化導出與重新編譯

### [MODIFY] [scratch/save_nnue.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/save_nnue.py)

更新所有偏移量以匹配 128 維的新二進位佈局：

| 資料段 | 新偏移 | 量化尺度 | dtype |
| :--- | ---: | :--- | :--- |
| friend_bias | 193 | 127.0 | int16 |
| friend_weights | 449 | 127.0 | int16 |
| enemy_bias | 12,599,745 | 127.0 | int16 |
| enemy_weights | 12,600,001 | 127.0 | int16 |
| L1 biases (×4 stacks) | 23,823,041+272+4752+4 | 8128.0 | int32 |
| L1 weights (×4 stacks) | +68 | 64.0 | int8 |
| L2 biases | +8264 | 8128.0 | int32 |
| L2 weights | +8392 | 64.0 | int8 |
| L3 bias | +9416 | 9600.0 | int32 |
| L3 weights | +9420 | 9600/127 | int8 |

### 重新編譯

```bash
cd rl_starter_11/agents/d8
./build.sh
```

### 更新 C++ offset

修改 `engine.cpp` L1151 的起始局面 raw score offset（從 `4341` 改為新模型的實際值）。

---

## Phase 4：驗證

### 自動測試

**單調性驗證**（`scratch/test_new_nnue.py`）：

| 組合 | 預期關係 |
| :--- | :--- |
| Up Queen > Up Knight > Up Pawn > Start | 降子優勢單調 |
| Start > Down Pawn > Down Knight > Down Queen | 缺子劣勢單調 |
| K+Q vs K > K+R vs K > KvK > K vs K+R | 端局物質單調 |

**搜尋健全性**（`scratch/test_d8_search.py`）：
- 10 步搜尋不崩潰
- NPS ≥ 500,000（128 維應比 256 維快）

### 比賽驗證

`agents/tournament_d8.py`：20 局 vs `d6_cpp`

| 目標 | 評估 |
| :--- | :--- |
| ≥ 4 勝（20%） | 最低可接受 |
| ≥ 8 勝（40%） | 預期目標 |
| ≥ 12 勝（60%） | 優秀 |

---

## User Review Required

> [!IMPORTANT]
> **架構修改（Phase 1）涉及 C++ 和 Python 兩端共約 50 處硬編碼數字的同步更改**，這是整個計劃中風險最高的部分。執行前需要：
> 1. 備份現有的 `nn.nnue`（已有 `nn.nnue.orig`）
> 2. 確認新二進位佈局 of 偏移量計算正確
> 3. 重新執行 `tests/test_incremental_vs_recompute.py` 確保增量邏輯仍正確

> [!WARNING]
> **是否繼續使用 256 維（v5 方案），改為只先生成 500 萬數據？**  
> 如果架構改動風險讓您不安，可以選擇維持 256 維，此時僅需標記 500 萬數據，而不需要修改任何 C++ 的維度程式碼。128 維則是更有推理效率與訓練效率的選擇，但需要更多 C++ 修改工作。
