# C++ 核心源碼目錄 (`src/`)

本目錄包含 `d8` 引擎的核心 C++ 代碼，負責高效的 Alpha-Beta 搜尋以及向量化 NNUE 前向傳播。

---

## 📄 檔案說明

### 1. 搜尋引擎核心
* **[engine.cpp](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/src/engine.cpp)**:
  * 實現具備 Aspiration Windows、移動排序（MVV-LVA）、歷史啟發式（History Heuristic）與靜態搜尋（Quiescence Search）的 Negamax Alpha-Beta 搜尋樹。
  * 實現增量累加器（Incremental Accumulator）的狀態更新與回滾邏輯，並對國王移動與易位進行特殊全盤重算。
  * 提供 Python 動態庫擴展接口（藉由 `pybind11`）。

### 2. 神經網絡評估
* **[nnue_eval.h](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/src/nnue_eval.h)**:
  * NNUE 前向傳播核心邏輯（1024 ➡️ 16 ➡️ 32 ➡️ 1）。
  * 支援基於國王位置的分桶加載邏輯（Buckets 0-3 為無 L1 結構，Buckets 4-7 為完整 L1+L2+L3 結構）。
  * SIMD 向量化運作：使用 ARM Neon 指令集（針對 macOS M4）和 Intel AVX2 進行矩陣相加與 Clipped ReLU 激活的並行運算。

### 3. 權重內嵌匯編
* **[weights.S](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/src/weights.S)**:
  * 匯編指令文件，利用 `.incbin` 指令在編譯期直接將二進位權重檔 `nn.nnue` 內嵌打包至生成的 `chess_engine_d8_han.so` 中，省去運行時尋找檔案路徑的麻煩。

### 4. 開局數據
* **[book_data.h](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/src/book_data.h)**:
  * 內建的 Chess Polyglot 開局庫數據庫，供 `engine.cpp` 中的 `probe_book` 函數在開局時進行快速局面查找以省去搜尋開銷。
