# chess agent D4.6 轉 C++ 計畫

將 python chess agent 由 python 轉 C++，原始路徑在 rl_starter_11/agents/d4_6，model.zip 包含 chess 庫以及 Syzygy 殘局庫，在 rl_starter_11/model.zip。目標是將原本的 python 程式碼重寫成 C++，並最佳化效能。

## 限制

1. 可以上傳伺服器 2 個 .py + 1 個 .zip
2. 可以使用記憶體空間為 4096 MB
3. 時間限制為 600 秒，要比賽10回合，等於平均每回合有60秒的時間
4. 伺服器運行在docker 環境，python 為 3.10

## 核心戰略：單次回合通訊與動態引導（Bootloading）

為了在「2 個 .py + 1 個 .zip」的限制下 達到最完美的效能與隱蔽性，我們採取以下策略：

1. 記憶體直通（Zero-copy）：Python 端不對矩陣做任何處理，直接把 PettingZoo 傳進來的 observation 記憶體指針丟進 .so。

2. 動態引導（Bootloader）：遠端伺服器啟動時，agent.py 會自動把 model.zip 解壓到有寫入權限的 /tmp 目錄，然後把 /tmp 加進 sys.path，動態 import 我們編譯好的 C++ 核心。

3. 純 C++ 內循環：棋盤重建、合法步生成、Alpha-Beta 遞迴、置換表（TT）、開局/殘局庫查詢、Action 編碼，全部在 C++ 內一氣呵成，算完只吐回一個整數（Action ID）。

## 📋 實戰任務清單（To-Do List）

### 階段一：開發準備與環境對齊（本地端）

[ ] 確認編譯容器：在本地安裝 Docker，並拉取官方 quay.io/pypa/manylinux2014_x86_64 鏡像。這是為了確保編譯出來的 .so 能相容伺服器上的舊版 GLIBC。

[ ] 選定 C++ 西洋棋基底：下載開源的 Header-only（純標頭檔）C++ 西洋棋庫（例如 thkim/chess.h），放到開發目錄下。這樣你就不用自己徒手寫 Bitboard 的合法步生成。

[ ] 準備 Pybind11：確保編譯環境中有 pybind11，用來做 C++ 與 Python 3.10 的橋樑。

### 階段二：撰寫 C++ 核心代碼 (engine.cpp)

[ ] 實作環境解析器（Observation Parser）：

在 C++ 中利用 py::array_t 的 unchecked<3>() 直讀矩陣。

解析第 7 到 18 管道（Channels），把棋子位置轉化為 C++ 西洋棋庫的 uint64_t 位元棋盤。

解析第 0 到 3 管道，讀取王車易位權限。

[ ] 實作對局歷史與重複偵測：

在 C++ 內部建立一個 std::unordered_map<uint64_t, int> 用來當作 Zobrist Hash 的歷史紀錄。

修正原本的 Bug：設計一個穩健的「新局重置」邏輯。如果盤面變回 32 顆滿棋，或者我方顏色改變，立刻清空對局歷史。

[ ] 整合超高速 Alpha-Beta 搜尋：

移植你原本的搜尋框架（Iterative Deepening、LMR、Null Move、Killer Moves）。

建立全域的置換表（TT），修正原本的 Bug：絕對不要每回合清空 TT，讓它跨回合繼承搜尋成果。

[ ] 實作 PettingZoo 專屬 Action 編碼器：

在 C++ 內部寫好 73 個直列/斜列/升變橫列（Planes）的映射邏輯。

修正原本的致命 Bug：當我方是真實黑棋時，C++ 的 best_move 必須先進行垂直翻轉（鏡像化），再經過 (col *8 + row)* 73 + plane 轉成絕對 Action ID。

### 階段三：交叉編譯與偽裝打包

[ ] 撰寫建置腳本 (setup.py)：

設定編譯參數為 -O3 -flto（開啟極致優化與連結期優化）。

防禦策略：絕對不要加 -march=native，避免伺服器 CPU 不支援新指令集而噴出 Illegal Instruction。

[ ] 執行 Docker 編譯：

進入 manylinux 容器，切換到 Python 3.10 路徑下執行編譯。

將產出的 .so 檔案重新命名為乾淨的 chess_search.so。

[ ] 封裝 model.zip：

把 chess_search.so、開局庫 book.bin、殘局庫 syzygy/ 資料夾全部塞進 model.zip。

### 階段四：撰寫 Python 進入點 (agent.py)

[ ] 實作解壓引導（Bootloader）：

在 Agent.__init__ 被觸發時，檢查 /tmp/chess_search.so 是否存在。

若不存在，用 zipfile 把 model.zip 解壓到 /tmp。

將 /tmp 附加到 sys.path。

[ ] 對接競賽介面：

保留官方規定的 class Agent 與 act(observation, action_mask) 簽名。

在 act 裡，直接一行程式碼呼叫 chess_search.solve(observation) 並回傳。

## 💡 關鍵贏球策略與避坑指南

### 時限動態調配（伺服器專屬）

C++ 的速度太快，中局每秒能看數百萬個節點。建議在 C++ 搜尋內加入嚴格的時間計時器。如果是中局前期，分配 1.5 秒；如果是殘局或時間快不夠了，壓縮到 0.4 秒。C++ 能在 0.4 秒內瞬間完成 6~7 步的深搜，依然可以碾壓純 Python。

### 殘局庫的黑白方視角翻轉

在使用 C++ 呼叫 Syzygy 殘局庫探測時，如果我方真實顏色是黑棋，傳進殘局庫探測器的棋盤必須先做 .mirror() 翻轉，否則殘局庫會把黑棋贏面當成白棋贏面，導致 Agent 在殘局時主動送子。

### 完美防禦重複和局陷阱

在 C++ 搜尋分支（模擬路徑）中，只要探測到某個步法會導致 Zobrist Hash 出現第 3 次（三手重複和局），如果當前局面我方大優，直接給予該步法極低的懲罰分，一票否決，避免勝勢下被對手強行逼和。
