# 開發報告與架構文檔目錄 (`docs/`)

本目錄包含 `d8` 引擎整合過程中的核心技術設計、量化架構探索、訓練優化筆記，以及歷史對戰調試報告。

---

## 📂 檔案分類與用途說明

### 1. 當前開發與訓練設計（最新）
* **[nnue_training_notes.md](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/docs/nnue_training_notes.md)**:
  * 記錄最新的 v4 訓練設計，詳細闡述了開局物質單調性缺失的根本原因、FT Embedding 的極低方差初始化（1e-4）、合成開局突變數據生成方法以及驗證 FEN 基準。

### 2. 歷史調試與執行日誌
* **[detailed_execution_log.md](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/docs/detailed_execution_log.md)**:
  * 詳細的步驟記錄與結果分析。包含了第一版編譯調試 FT bias 4-byte 載入偏移、C++ 增量累加器驗證，以及初版錦標賽 0-20 大敗後的「雪盲症與隨機權重反轉」問題深度剖析。

### 3. 架構探索與格式解密報告
* **[nnue_layout_report.md](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/docs/nnue_layout_report.md)**:
  * 解析原始 `nn.nnue` 權重佈局的逆向分析報告，精確推導出 Isolated Buckets 與 Main Stacks 的二進位 Stride 長度，奠定了 C++ 記憶體指針映射的基礎。
* **[findings_and_results.md](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/docs/findings_and_results.md)**:
  * 記錄早期試圖解密原版權重以適配 C++ `Architecture A` 的嘗試，展示了為何原版權重無法直接匹配，從而論證了「必須從頭自主訓練」的技術決策。

### 4. 遺留的基礎文檔
* **[d6_engine_full_report.md](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/docs/d6_engine_full_report.md)**:
  * `d6_cpp` 代理人的技術報告，詳細分析了 d6 的啟發式靜態評估函數（HCE）、王安全與子力位置表（PST）邏輯，適合作為特徵提取與子力對齊的參考。
* **[implementation_plan.md](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/docs/implementation_plan.md)**:
  * 舊版 C++ 引擎實作計劃，詳細說明了 C++ 類別設計、SIMD 加速設計與編譯整合流。
