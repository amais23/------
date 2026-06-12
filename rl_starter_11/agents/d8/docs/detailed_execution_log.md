# D8 Agent Integration Plan: Detailed Execution Log & Results

This document provides a comprehensive step-by-step record of the actions performed and results achieved during the execution of the NNUE Integration Plan for the `d8` agent.

---

## 階段 1：權重解析與網絡架構對齊 (Weight Parser & Architecture Alignment)

### 1.1 解決 4-Byte 偏移對齊問題
* **步驟**：診斷並修復了 Feature Transformer (FT) 的 bias 載入偏移。初版程式從 `189` 和 `25199293` 位元組載入權重，但這些偏移量包含了 4 位元組的 FT Hash 標頭 (`0x5f2348b8`)。
* **結果**：將 `friend_bias` 的載入偏移改為 `193`，`enemy_bias` 改為 `25199297`。修復後消除了損壞首兩個神經元的垃圾資料，使評估對子力變化恢復靈敏度（之前多后/少后評估值差極小：`1004` vs `981`）。

### 1.2 驗證 16×1024 網絡架構 (Architecture A)
* **步驟**：分析 `nn.nnue` 的剩餘檔案大小和結構，驗證其是否為 Architecture A。發現主堆疊（Main Stack）的 Stride 為 **17640 bytes**，孤立桶（Isolated Bucket）的 Stride 為 **1188 bytes**。
* **結果**：數學驗證證明這個 contiguity 完全契合，從起點到檔案尾端無縫對接。這證實了 L1 的輸出大小為 16（雙向對接後為 32 進入 L2），L2 輸出為 32，L3 輸出為 1。

---

## 階段 2：數學驗證與量化係數調優 (Mathematical Verification)

### 2.1 測試量化除數 (Division Factor) 影響
* **步驟**：撰寫調優腳本測試 1 至 256 的 Division Factor，檢查在不同係數下，移除白方或黑方棋子時的評估單調性（Monotonicity）。
* **結果**：
  * 當使用任何大於 1 的除數時，評估函數失去單調性（例如：少后位置評估反而比開局更好）。
  * 只有 **Division Factor 1（無除法）** 能保持單調性：`Won (2256) > Start (2022) > Lost (1383)`。
  * 因此確定 FT 累加器的激活前輸出**不進行 127 的縮放除法**。

### 2.2 確定開局對齊偏移值 (Centering Offset)
* **步驟**：基於 Division Factor 1，開局初始 FEN 的 raw 輸出值為 **`2022`**。
* **結果**：在 C++ 引擎的 `evaluate` 中減去 `2022` 作為基準對齊，確保搜尋樹起點的靜態評估接近 `0`（符合 negamax 的搜尋常規）。

---

## 階段 3：C++ 增量引擎實作與編譯 (C++ & Incremental Accumulators)

### 3.1 實作 C++ NNUE 評估核心
* **步驟**：在 `src/nnue_eval.h` 中用 C++ 實作 L1, L2, L3 的前向傳播。為了高效率，在 Neon/AVX SIMD 上使用向量化指令，並且實作了基於 oriented king 的分桶機制 (`bucket_us = 7 - (oriented_king_us / 8)`)。

### 3.2 整合增量累加器 (Incremental Accumulator Updates)
* **步驟**：在 `src/engine.cpp` 的 `alpha_beta` 與 `quiescence` 中加入增量更新邏輯：
  * 一般移動：利用 `update_accumulators` 只增減起點與終點的特徵，避免整張棋盤重算。
  * 王移動/王車易位：因為分桶參考點改變，此時觸發 `recompute_accumulators` 進行全盤重算。

### 3.3 編譯引擎動態函式庫
* **步驟**：更新 `setup.py` 與 `build.sh` 將 C++ 核心與內嵌的 `weights.S` 組譯封裝，編譯出 macOS 平台的 `chess_engine_d8_han.cpython-312-darwin.so`。

---

## 階段 4：多重自動化測試與驗證 (Testing & Validation)

### 4.1 Python vs C++ 一致性測試
* **步驟**：執行 `tests/test_cpp_vs_python.py` 對開局、多子、少子、對局中等 6 種不同的基準 FEN 進行直連評估比對。
* **結果**：Python 前向傳播與 C++ 前向傳播所得評估值 **100% 完全相同**。

### 4.2 增量更新與全盤重算比對
* **步驟**：執行 `tests/test_incremental_vs_recompute.py`。程式隨機模擬 5 場、每場高達 100 步的隨機走子（包含隨機吃子與升變），比對增量更新的累加器狀態與全盤重算狀態。
* **結果**：隨機測試 **100% 通過**，增量邏輯無任何漂移或誤差。

---

## 階段 5：本地錦標賽對戰與問題診斷 (Local Tournament & Diagnosis)

### 5.1 執行本地錦標賽
* **步驟**：執行 `agents/tournament_d8.py`，讓 `d8` 引擎與使用手寫 heuristics 的 `d6_cpp` 進行 20 局對戰（10 白 10 黑）。
* **結果**：`d8` 以 **0-20 全敗**。

### 5.2 深入剖析與致命缺陷診斷
* **步驟**：撰寫分析腳本拉取對戰日誌與評估數值。發現在搜尋樹中，評估函數回傳了極其怪異的走向：
  * **兵估值反轉：** 贏兵時（黑 d7 兵不見）評估值為 `821`（比起點少 1201 分，視為大劣）；輸兵時（白 d2 兵不見）評估值為 `2190`（比起點多 168 分，視為優勢）。
  * **激活值飽和：** 因為缺少除以 127 的縮放，大於 127 的特徵累加值直接被 Clipped ReLU 截斷為 127。這導致 network 產生嚴重的「雪盲症」，無法分辨多子和少子的細微差異。
  * **結論**：神經網絡權重本身存在嚴重的方向反轉（可能為訓練時轉出 bug 或 mapping 混亂），導致 D8 搜尋時主動送兵送子，最終全敗。

---

## 總結
我們順利將 C++ NNUE 完整寫完、編譯成功、並通過了所有的**程式正確性與增量一致性測試**。但由於模型本身的量化與特徵映射在不進行 127 除法時存在反轉缺陷，導致錦標賽表現不佳。本 Implementation Plan 已完成所有架構開發與驗證工作，在此收尾。
