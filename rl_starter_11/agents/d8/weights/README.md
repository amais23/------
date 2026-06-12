# 權重目錄 (`weights/`)

本目錄用於存放 `d8` 引擎訓練與運行所需的模型權重文件。

---

## 📄 檔案說明

### 1. [nn.nnue](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/weights/nn.nnue)
* **用途**：序列化量化二進位權重檔。
* **格式**：符合 `Architecture A` 的 Stockfish-like 二進位佈局。包含 16 位有符號整型（`int16_t`）的 Feature Transformer 權重、8 位有符號整型（`int8_t`）的線性層權重，以及 32 位有符號整型（`int32_t`）的偏置項。
* **加載**：C++ 搜尋引擎在編譯期會透過 `src/weights.S` 匯編包裝直接將此檔案內嵌至編譯後的動態鏈接庫（`chess_engine_d8_han.so`）中。

### 2. [nn.nnue.orig](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/weights/nn.nnue.orig)
* **用途**：原始權重備份。
* **說明**：在初次進行從頭訓練前，為防丟失而對原版（與我們 C++ 架構不匹配的 Stockfish 預訓練權重）所做的備份，僅作為歷史留存參考。

### 3. [trained_model.pt](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/weights/trained_model.pt)
* **用途**：PyTorch 浮點模型存檔。
* **格式**：包含網絡狀態字典（`state_dict`）的 PyTorch Checkpoint 文件。
* **導出**：由 `scratch/train_nnue.py` 訓練輸出，隨後由 `scratch/save_nnue.py` 加載並量化導出為二進位的 `nn.nnue`。
