# D8 Agent - NNUE Chess AI

這是 `d8` 西洋棋代理人的核心開發目錄。`d8` 採用了內嵌式的神經網絡評估函數（NNUE, Architecture A），並結合高效的 C++ 搜尋引擎（具備 Aspiration Windows、移動排序與增量累加器），旨在打造一個能徹底擊敗傳統啟發式評估引擎（如 `d6_cpp`）的最強 AI 代理人。

---

## 📂 目錄結構與檔案分類

```
rl_starter_11/agents/d8/
├── README.md               # 本說明文件（主要導覽）
├── agent.py                # Python 代理人入口，負責與 PettingZoo 環境對接與調用 C++ 引擎
├── setup.py                # Pybind11 編譯配置文件
├── build.sh                # 一鍵編譯 C++ 引擎指令檔
├── pack.sh                 # 代理人打包發布指令檔
├── model.py                # 輕量級 Python 模型接口
├── nn.nnue                 # 序列化後的量化二進位權重檔（由 C++ 引擎加載）
├── src/                    # C++ 核心源碼
├── tests/                  # 單元測試與正確性校驗腳本
├── scratch/                # 數據生成、訓練、解析與快速驗證腳本
├── weights/                # 權重存放目錄（PyTorch 浮點與二進位權重）
└── docs/                   # 歷史開發報告與架構分析
```

---

## 🛠 核心程式說明

### 1. 代理人與編譯入口
* **[agent.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/agent.py)**：代理人 Python 接口，初始化 C++ 搜尋引擎，加載開局庫，並接收環境狀態（Observation 與 Mask）執行下子决策。
* **[setup.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/setup.py)**：利用 `setuptools` 與 `pybind11` 將 C++ 代碼編譯為 Python 模組。
* **[build.sh](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/build.sh)**：編譯腳本，會自動將 `nn.nnue` 編譯為 `weights.o` 並生成 `chess_engine_d8_han.so`。
* **[pack.sh](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/pack.sh)**：將代理人打包，便於部署。

### 2. C++ 搜尋與評估源碼 (`src/`)
* **[src/engine.cpp](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/src/engine.cpp)**：
  * 核心搜尋引擎：實現了具備 Aspiration Windows 的 Alpha-Beta 負極限極大值搜尋。
  * 狀態維護：包含移動排序（MVV-LVA）、歷史表與靜態搜尋（Quiescence Search）。
  * 累加器優化：負責增量更新 `m_accum_friend/enemy` 累加器（在非國王移動時，只對起點與終點進行加減），並在國王移動或易位時重算累加器。
* **[src/nnue_eval.h](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/src/nnue_eval.h)**：
  * NNUE 前向傳播：實現 L1 (1024→16)、L2 (32→32)、L3 (32→1) 層的整數矩陣乘法。
  * SIMD 向量化：支援 ARM Neon 與 AVX2 指令集，實現高效的累加器加減與 Clipped ReLU 激活。
  * 特徵映射：包含對齊 C++ 邏輯的 `friend_idx` 與 `enemy_idx` 計算公式。
* **[src/book_data.h](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/src/book_data.h)**：內嵌的開局庫數據，提供快速開局查找。
* **[src/weights.S](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/src/weights.S)**：匯編包裝檔，將外部 `nn.nnue` 二進位權重內嵌編譯進動態庫中。

### 3. 數據生成與訓練腳本 (`scratch/`)
* **[scratch/train_nnue.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/train_nnue.py)**：
  * PyTorch 訓練模型：使用 MPS (Apple Silicon GPU) 進行訓練。
  * 合成端局生成：自動產生 100,000 個端局隨機局面（`K+Q vs K` 等），提供精確的物質價值標籤。
  * 開局突變生成：包含隨機開局與棋子移去的合成數據（為了解決起始局面特徵未訓練的問題）。
* **[scratch/label_data.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/label_data.py)**：調用本地 Stockfish 引擎對從 PGN 提取的 FEN 進行快速並行分析標籤（時間限制 5ms 或深度 10）。
* **[scratch/save_nnue.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/save_nnue.py)**：讀取 PyTorch 訓練出的模型檔案 (`.pt`)，乘上對應的量化係數（FT=127, L1=64, L2=64, L3=75.6），四捨五入轉換成 `int16`/`int8`/`int32` 並序列化輸出為 `nn.nnue` 二進位檔案。
* **[scratch/download_data.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/download_data.py)**：從網路下載高水平對局 PGN 作為訓練基礎。

### 4. 調試與評估驗證工具 (`scratch/` 與 `tests/`)
* **[scratch/test_new_nnue.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/test_new_nnue.py)**：測試特定局面的直接 NNUE 靜態評估，用以確認多子/少子、不同端局之間是否具備**單調性 (Monotonicity)**。
* **[scratch/test_d8_search.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/scratch/test_d8_search.py)**：實際啟動搜尋引擎進行 10 步深度的模擬對局搜尋，驗證搜尋不崩潰且評估分數（NPS）與 Centipawn 回傳符合預期。
* **[tests/test_won_lost_responsive.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_won_lost_responsive.py)**：自動化單元測試，比對起始局面、多后局面與少后局面，驗證引擎基本物質響應敏感度。
* **[tests/test_incremental_vs_recompute.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_incremental_vs_recompute.py)**：隨機走步對局測試，比對 C++ 增量更新（Incremental）與全盤重新計算（Recompute）的累加器狀態，確保增量邏輯無任何漂移。
* **[tests/test_cpp_vs_python.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_cpp_vs_python.py)**：雙向比對 C++ 評估前向傳播與 Python 模擬前向傳播的值，確保激活與權重排序完全對齊。

---

## 🛠 歷史開發與架構文檔 (`docs/`)

* **[docs/nnue_layout_report.md](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/docs/nnue_layout_report.md)**：分析原始 `nn.nnue` 的 Stride 偏移，確定 L1、L2 和 L3 的神經元維度與分桶邊界。
* **[docs/findings_and_results.md](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/docs/findings_and_results.md)**：詳細記錄探究原版權重不匹配與窮舉尋找映射順序的過程，結論為必須使用自定義特徵重頭訓練。
* **[docs/detailed_execution_log.md](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/docs/detailed_execution_log.md)**：整合過程的完整執行日誌，包括調試偏移對齊問題、SIMD 整合與首個對戰版本全敗（由於噪聲與反轉問題）的診斷結果。
