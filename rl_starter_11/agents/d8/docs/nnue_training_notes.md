# D8 Agent - NNUE 訓練與優化筆記 (v4)

本文件詳細記錄 `d8` 代理人在 NNUE 從頭訓練過程中的技術發現、數據集設計、超參數選擇與驗證標準。

---

## 1. 根本問題診斷

在首輪從頭訓練的 NNUE 模型中，我們發現了嚴重的**開局物質評估倒置**問題：
* **現象**：移除黑方 d7 兵（白大優）時，Raw 評估值從 `4341` 降至 `1800`；移除白方 d2 兵（白大劣）時，評估值為 `2240`，比前者還高。
* **原因**：
  1. **特徵未經訓練**：原始訓練集 `dataset.txt` 僅包含中局（第 16-80 步）的局面。此時雙方國王多已易位，導致對應「國王在 e1/e8 且兵/馬在初始位置」的特徵在訓練中從未被激活或更新。
  2. **隨機權重噪聲**：Embedding 層隨機初始化（如 Kaiming 初始化，標準差為 `0.06`）。在評估起始局面及其突變時，這些未訓練特徵的隨機權重就成了主要的評估分量。移去一個棋子相當於移去一個隨機向量，其結果完全是隨機且非單調的。

---

## 2. 解決方案設計 (v4)

### A. 調整 FT Embedding 初始化
將 `friend_emb.weight` 和 `enemy_emb.weight` 的初始化方式調整為極小的正態分佈：
* **初始化參數**：`nn.init.normal_(weight, mean=0.0, std=1e-4)`
* **設計意圖**：將未經訓練特徵的權重無限逼近於 0。這樣一來，任何沒在訓練集出現過的特徵在 Forward 時均貢獻 0，消除隨機噪聲，確保基礎子力的單調性不受干擾。

### B. 引入開局突變合成數據
在 `train_nnue.py` 中新增 `generate_synthetic_early_game_mutations(num_samples=50000)`：
1. **生成方式**：
   - 從標準起始局面開始，隨機走 0 到 8 步。
   - 隨機移去 0 到 5 個棋子（國王除外）。
   - 隨機決定輪到哪一方走子 (Side to move)。
2. **標籤計算**：
   - 以標準子力價值計算精確的相對分數（Pawn=1, Knight/Bishop=3, Rook=5, Queen=9）。
   - WDL 相對分數格式：若白棋佔優且輪到白棋走子，則為正分；若輪到黑棋走子，則為負分。
3. **效果**：強制 Embedding 層學習開局階段（國王在 e1/e8 附近時）所有起點兵、馬、象、車的正確物質分數。

---

## 3. 訓練超參數

| 參數 | 數值 | 說明 |
| :--- | :--- | :--- |
| **數據集大小** | 269,825 局面 | 包含：120k 中局實戰 + 100k 合成端局 + 50k 合成開局突變 |
| **FT 初始化** | `normal(0.0, 1e-4)` | 消除未激活特徵的隨機權重噪聲 |
| **優化器** | Adam | 學習率 lr = 1e-3，權重衰減 weight_decay = 1e-4 |
| **損失函數** | Huber Loss (delta=1.0) | 對極端異常值更具魯棒性 |
| **訓練設備** | MPS | 於 M4 晶片上使用 Metal 進行硬體加速 |
| **Epochs** | 20 | 均衡泛化與訓練時間 |

---

## 4. 評估單調性測試基準 (Monotonicity Benchmark FENs)

在每次訓練完畢、量化導出後，必須使用 [scratch/test_new_nnue.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/test_new_nnue.py) 對以下局面進行直連 raw score 評估測試：

### A. 開局兵/馬突變測試
1. **Start** (起始局面): `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`
2. **Up Pawn (d7)** (黑欠 d7 兵，白優): `rnbqkbnr/ppp1pppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`
3. **Down Pawn (d2)** (白欠 d2 兵，白劣): `rnbqkbnr/pppppppp/8/8/8/8/PPP1PPPP/RNBQKBNR w KQkq - 0 1`
4. **Up Knight (g8)** (黑欠 g8 馬，白優): `rnbqkb1r/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`
5. **Down Knight (g1)** (白欠 g1 馬，白劣): `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKB1R w KQkq - 0 1`
6. **Up Queen (d8)** (黑欠 d8 后，白優): `rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`
7. **Down Queen (d1)** (白欠 d1 后，白劣): `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1`

* **預期單調性**：
  - `Up Queen (d8) > Up Knight (g8) > Up Pawn (d7) > Start > Down Pawn (d2) > Down Knight (g1) > Down Queen (d1)`

### B. 端局測試
1. **K+Q vs K** (白后): `k7/8/8/8/8/8/8/K1Q5 w - - 0 1`
2. **K+R vs K** (白車): `k7/8/8/8/8/8/8/K1R5 w - - 0 1`
3. **KvK** (均勢國王): `k7/8/8/8/8/8/8/K7 w - - 0 1`
4. **K vs K+R** (黑車，輪黑走): `k7/8/8/8/8/8/8/K1R5 b - - 0 1`

* **預期單調性**：
  - `K+Q vs K > K+R vs K > KvK > K vs K+R`
