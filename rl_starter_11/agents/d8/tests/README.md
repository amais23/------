# 測試與驗證目錄 (`tests/`)

本目錄包含針對 `d8` 引擎編譯成果、數學公式、增量累加器與評估正確性的全方位單元測試與集成測試。

---

## 🧪 測試分類與檔案說明

### 1. 引擎整合與正確性測試
* **[test_won_lost_responsive.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_won_lost_responsive.py)**:
  * 驗證 C++ 引擎的物質敏感度（Up Queen > Start > Down Queen），是編譯後快速確認引擎是否具備基礎子力分辨能力的集成測試。
* **[test_incremental_vs_recompute.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_incremental_vs_recompute.py)**:
  * 模糊測試（Fuzz Testing）。隨機行走 100 步，比對「增量計算得到的累加器」與「重新全盤計算得到的累加器」數值，驗證 C++ 增量優化算法沒有任何漂移或邏輯錯誤。
* **[test_cpp_vs_python.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_cpp_vs_python.py)**:
  * 一致性對齊測試。提取中局多個典型 FEN 局面，比對 Python 的前向傳播公式與 C++ 模組運算值，確保雙方的矩陣運算與激活函數對齊（目前結果為 100% 完全一致）。
* **[test_timeout_fix.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_timeout_fix.py)**:
  * 測試 C++ 搜尋引擎的超時中斷機制，確保當搜尋時間超過設定閾值時，搜尋能及時安全中斷並返回當前最佳棋步。

### 2. 數學與前向傳播驗證
* **[test_nnue_correct_math.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_nnue_correct_math.py)**: 驗證神經網絡前向傳播的底層矩陣運算。
* **[test_nnue_eval.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_nnue_eval.py)**: 簡化版的評估前向測試。
* **[test_dual_sweep.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_dual_sweep.py)** & **[test_sweep_fine.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_sweep_fine.py)**: 執行輸入範圍掃描，驗證雙向 Clipped ReLU 激活的數值截斷邏輯。
* **[test_trace_dual.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_trace_dual.py)** & **[test_trace_layers.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_trace_layers.py)**: 追蹤每一層網絡在特定局面下的具體激活輸出值，便於逐層對齊。

### 3. 架構探索與權重分析
* **[test_true_architecture.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_true_architecture.py)** & **[test_architecture_comparison.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_architecture_comparison.py)**: 用於比較與確認 Architecture A 與其他網絡架構的層大小配置。
* **[test_verify_buckets.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_verify_buckets.py)**: 驗證多個分桶（Buckets）之間的偏移量和權重範圍。
* **[test_inspect_layers.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_inspect_layers.py)**, **[test_inspect_weights.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_inspect_weights.py)**, **[test_inspect_enemy_weights.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_inspect_enemy_weights.py)**, **[test_inspect_fc_metadata.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_inspect_fc_metadata.py)**: 分析權重文件內各層結構與 metadata 的調試工具。
* **[test_active_features.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_active_features.py)**: 解析特定局面下被啟用的特徵索引，輔助分析特徵映射。
* **[test_check_monotonicity.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_check_monotonicity.py)** & **[test_debug_fen.py](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/tests/test_debug_fen.py)**: 在開發歷史中用於測試原權重的單調性與特定局面問題排查。
