# 數據、訓練與臨時調試工具目錄 (`scratch/`)

本目錄包含數據準備、模型訓練、二進位量化以及研究期間使用的各種探查、調試腳本。

---

## 📂 腳本分類與檔案說明

### 1. 數據與訓練核心流
* **[download_data.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/download_data.py)**:
  * 從網絡上下載高品質棋譜（`lichess_elite_*.pgn`）至 `research/data/raw/` 目錄。
* **[label_data.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/label_data.py)**:
  * 從 PGN 中提取中局候選 FEN，並利用 ThreadPool 並行調用本地 Stockfish 進行評估標籤，生成 `dataset.txt`。
* **[train_nnue.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/train_nnue.py)**:
  * 使用 PyTorch 載入標籤數據，合成 10 萬個端局局面與 5 萬個開局突變局面，採用 MPS 硬體加速訓練，並保存 `trained_model.pt`。
* **[save_nnue.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/save_nnue.py)**:
  * 載入 PyTorch 的 `.pt` 浮點模型，對其各層參數乘上對應的量化尺度（FT=127, L1=64, L2=64, L3=75.6），四捨五入轉換後序列化寫入 `nn.nnue` 量化二進位權重檔。

### 2. 評估與搜尋驗證
* **[test_new_nnue.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/test_new_nnue.py)**:
  * 加載編譯好的 C++ 引擎並輸出各個單兵/單馬等突變局面的 Raw NNUE 分數，用於快速確認單調性（Monotonicity）是否成立。
* **[test_d8_search.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/test_d8_search.py)**:
  * 繞過開局庫，測試搜尋引擎連續走子時的搜尋性能、節點評估（NPS）與分數合理性，是搜尋引擎整合測試工具。
* **[test_d8_agent.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/test_d8_agent.py)**:
  * 測試 `agent.py` 是否能正確與外部大環境 API 調用進行交互。

### 3. 量化調優與架構研究
* **[check_arch_A_div.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/check_arch_A_div.py)**: 測試並尋找在 `Architecture A` 下最合適的量化除數。
* **[check_monotonicity_options.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/check_monotonicity_options.py)**: 測試不同的 Feature Mapping 配置下是否能實現單調性。
* **[check_orig_monotonicity.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/check_orig_monotonicity.py)**: 用於測量原版權重文件本身的評估值單調表現。
* **[train_nnue_transfer.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/train_nnue_transfer.py)**: 在確定放棄之前，嘗試利用 Stockfish 的 embedding 特徵進行 Transfer Learning 的腳本。

### 4. 特徵與權重深度探查 (Inspect Utilities)
* **[inspect_biases.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/inspect_biases.py)**, **[check_biases_arch_A.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/check_biases_arch_A.py)**, **[check_biases_arch_B.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/check_biases_arch_B.py)**, **[check_biases_32_512.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/check_biases_32_512.py)**: 檢查二進位二級與三級 bias 結構的偏移與大小。
* **[inspect_features.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/inspect_features.py)**: 印出輸入特徵的數值與稀疏分佈。
* **[inspect_l2_l3.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/inspect_l2_l3.py)**: 解析 L2 與 L3 層的權重值範圍。
* **[inspect_pt_dataset.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/inspect_pt_dataset.py)**: 查看 preprocessed_dataset.pt 中被轉換特徵長度與 WDL 標籤。
* **[inspect_weights_by_piece.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/inspect_weights_by_piece.py)**: 依棋子類型分析權重，檢查神經網絡的子力敏感傾向。
* **[find_piece_ordering.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/find_piece_ordering.py)** & **[find_piece_ordering_A.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/find_piece_ordering_A.py)**: 窮舉特徵排序映射，尋找適配 C++ 的特徵 stride 規律。
* **[find_divergence.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/find_divergence.py)**: 用於精確定位 Python 與 C++ 實作中累加器更新不一致點的 debug 腳本。

### 5. 其他輔助調試
* **[analyze_tournament.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/analyze_tournament.py)**: 分析錦標賽日誌與結果的腳本。
* **[check_pawn_exposures.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/check_pawn_exposures.py)**: 針對開局兵特徵在特定暴露底下的權重表現分析。
* **[debug_search_ply10.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/debug_search_ply10.py)**: 單步深入搜尋細節調試。
* **[test_pytorch_predictions.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/test_pytorch_predictions.py)** & **[test_final_arch_A.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/test_final_arch_A.py)** & **[test_sf_score.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/test_sf_score.py)**: 浮點模型與直接預測值測試。
* **[test_material_values.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/test_material_values.py)** & **[test_knight_capture.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/test_knight_capture.py)**: 分別用於測試吃子情境下的物質子力改變響應。
