# Pull Request (PR) 說明與 Commit 標註指南

> **專案**：`rl_starter_11`
> **類別**：Bug Fix / Stability Improvement
> **目的**：修復高並行挑戰下，C++ 西洋棋引擎隨機產生的 Exit Code 139 (Segfault) 與 Exit Code 134 (Abort) 崩潰，並提升引擎在天梯平台上的穩定性。

---

## 1. 建議 Commit 訊息格式

我們建議將此次變更拆分為兩個語意明確的 Commit，或者合併為一個結構完整的 Commit：

### 方案 A：單個合併 Commit（推薦）
```text
fix(engine): resolve parallel search timeout segfaults and seenSquares castling bugs

- Pass Board by value in search_best_move to prevent search-timeout state corruption from propagating back to solve() (fixes Exit Code 139).
- Comment out buggy map_king_atk == 0 early-return optimization in seenSquares template in chess.hpp to prevent illegal castling into check and subsequent king capture (fixes Exit Code 134).
- Remove all debugging stack-tracing instrumentation from engine.cpp to guarantee zero recursive overhead.
- Recompile macOS and Linux manylinux2014 binaries (-O3, -flto, -DNDEBUG).
- Verify stability with 120 parallel game stress tests (4 threads, 0 errors).
```

### 方案 B：拆分為兩個 Commit
1. **修復超時局面損壞**：
   ```text
   fix(engine): pass Board by value in search_best_move to prevent timeout corruption

   When alpha_beta throws timeout, exception unwinding skips board.unmakeMove() calls, leaving the board in a wrong position. Passing Board by value isolates the search tree board state copy and prevents SIGSEGV (139) in solve().
   ```
2. **修復 seenSquares 庫的合法性判斷**：
   ```text
   fix(chess-library): resolve buggy early-return in seenSquares causing illegal castling

   Comment out map_king_atk == 0 early return in chess.hpp's seenSquares template. The buggy optimization incorrectly returned 0 controlled squares when the king was surrounded by friendly pieces, allowing illegal castling into check.
   ```

---

## 2. Pull Request (PR) 說明範本

### PR 標題
`fix(engine): 修復高並行搜尋超時 Segfault (139) 與王車易位合法性判斷 Bug (134)`

### PR 說明

#### 🔍 問題背景與影響
在天梯伺服器多個並行挑戰發起時，引擎會隨機崩潰退出（退出碼 139 或 134）。這會直接導致對局以失敗告終並扣除天梯點數。

#### 🛠️ 變更內容與修復原理

1. **修復搜尋超時引發的局面損壞 (`Exit Code 139`)**
   - **影響檔案**：[engine.cpp](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp) 中的 [search_best_move](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp#L1368) 函數。
   - **修正**：將傳遞參數從 `Board &board` 改為按值傳遞 `Board board`。
   - **原理**：防止超時異常拋出時被跳過的 `unmakeMove` 留下的損壞狀態污染 `solve()` 中的原始棋盤，避免後續套用著法時發生雜湊數組越界。

2. **修復 `chess.hpp` 的 `seenSquares` 控制格誤判 (`Exit Code 134`)**
   - **影響檔案**：[chess.hpp](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/deps/chess.hpp) 中的 [seenSquares](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/deps/chess.hpp#L3912) 模板函數。
   - **修正**：註解屏蔽 `map_king_atk == Bitboard(0ull)` 的早退優化。
   - **原理**：當國王被己方棋子完全包圍時，原先優化會錯誤判定對手控制了 0 個格子。這使得國王在搜尋中得以「非法易位至對手火網下」，導致下一個半回合國王被吃掉，在後續遞迴中觸發「國王消失」的 `std::abort()` 崩潰。

3. **效能優化與二進位檔編譯**
   - 移除了所有偵錯插樁程式碼，確保搜尋樹中 0 效能損耗。
   - 重新編譯 macOS 與 Linux (manylinux2014) 目標之 `.so` 動態庫檔，並打包為 `model.zip`。

#### 🧪 測試與驗證數據
* **本地測試**：已在本機環境下通過 `tests/` 下的所有基本單元測試。
* **Docker 並行壓力測試**：
  在 `manylinux2014_x86_64` 容器內執行 4 執行緒、每執行緒 30 輪大量超時搜尋壓力測試（包含初始局面、複雜中局、少子殘局等），**120 場solve對決 100% 通過，0 次崩潰**（修復前平均在第 11-17 場即會崩潰）。
* **天梯部署**：已更新至天梯槽位 2 (`D6 Engine`)，運行正常。
