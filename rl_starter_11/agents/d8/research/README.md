# 研究與探索數據目錄 (`research/`)

本目錄包含了 `d8` 代理人在開發與逆向工程階段所進行的各項探索、架構解密、數值驗證與原始/已處理數據集。

---

## 📂 子目錄結構與用途說明

### 1. 數據目錄 (`data/`)
* **`raw/`**: 存放從網絡上下載的高水平大師棋譜（包括 `Kasparov.pgn`、`Carlsen.pgn`、`Fischer.pgn`、`Anand.pgn`、`Karpov.pgn`），作為 FEN 提取的原始數據源。
* **`processed/`**: 
  * `dataset.txt`: 利用 Stockfish 評估標籤後的中局局面數據集（約 12 萬行，格式為 `FEN,score`）。
  * `preprocessed_dataset.pt`: 經由特徵提取、轉換為 PyTorch Tensor 後的二進位序列化數據集快取檔。

### 2. 架構反向搜尋 (`search/`)
本目錄腳本在逆向原始 `nn.nnue.orig` 權重結構時，用於搜尋各個線性層的尺寸界限、分桶對齊偏移以及 Hash 值位置。
* **`brute_force_dims.py` & `search_layout.py`**: 暴力搜索神經元維度與特徵層分佈。
* **`find_boundaries.py` & `find_l1_alignment.py`**: 尋找 L1 權重的對齊邊界與 Stride 長度。
* **`compute_fc_hash.py` & `find_hash_in_file.py`**: 用於搜尋與驗證權重結構內包含的架構特徵 Hash（如 `0x5f2348b8` 等）。

### 3. 權重與偏置傾倒工具 (`dump/`)
用於將二進位 `nn.nnue` 內部特定偏移量的權重與偏置以十進位或十六進位形式打印出來，便於與 Python 對齊。
* **`dump_stack_details.py` & `dump_offset_details.py`**: 傾倒 Main Stack 與 Isolated Bucket 的權重與偏置偏移細節。
* **`print_all_biases.py` & `print_l2_biases.py`**: 讀取並輸出各層的偏置值。
* **`print_weights_friend.py` & `print_weights_for_each_piece.py`**: 依棋子類型傾倒並分析 FT 權重的大小趨勢。

### 4. 層結構深度探查 (`inspect/`)
用於深入剖析二進位權重的記憶體連續性，診斷指針讀取偏差。
* **`parse_nnue.py` & `parse_nnue_layers.py`**: 逐步解析 `nn.nnue` 檔案，印出其邏輯段落資訊。
* **`debug_forward_pass.py`**: 提供單步追蹤前向傳播數值的除錯環境。

### 5. 數學與佈局驗證 (`verify/`)
在實作 C++ 引擎前，在 Python 端用以驗證自研的 Feature Transformer 與線性層前向傳播的正確性，確保指針讀取與分桶邏輯無誤。
* **`verify_forward_pass_correct.py` & `verify_forward_pass_starting.py`**: 比對起始局面在不同激活方式下的前向傳播輸出。
* **`verify_exact_layout.py` & `verify_final_layout.py`**: 確認所建立的位元組 Stride（例如 17640 與 1188）能完全契合檔案大小。

### 6. 參考資料 (`ref/`)
存放標準 NNUE 架構（如 HalfKA、HalfKP）的官方或標準參考實現，用於開發時查閱特徵索引映射算法。
* **`halfka_ref.py` & `halfkp_ref.py`**: 標準 HalfKA/HalfKP 特徵映射算法參考。
* **`serialize_ref.py`**: 標準序列化/反序列化邏輯參考。
