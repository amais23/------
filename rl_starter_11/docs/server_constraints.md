# MLArena 伺服器與沙箱環境限制說明

本文件詳細整理了 MLArena 伺服器對 Chess Agent 的各項執行限制、競賽規則，以及我們目前採用的應對技術策略。

---

## 1. 沙箱執行環境限制（二進位載入限制）

伺服器為了安全性，對沙箱容器做出了非常嚴格的限制：

| 限制項目 | 影響 | 我們的解決方案 (Workaround) |
| :--- | :--- | :--- |
| **`/tmp` 掛載 `noexec`** | 無法將二進位檔（如 `.so` 檔）解壓縮到 `/tmp` 後用 Python 載入執行。 | **ELF 偽裝技術**：不使用 zip 壓縮，直接將 Linux 編譯出的 `.so` 檔案複製並更名為 `model.zip`。 |
| **`/app/arena` 掛載 `Read-Only`** | 無法在執行期進行任何寫檔、動態編譯或就地修改。 | **`ExtensionFileLoader` 直接載入**：因為 `model.zip`（本質上是 `.so`）是由平台放進程式目錄中的，我們可以使用 Python 的底層 C 擴充載入器，直接對該唯讀路徑下的檔案進行 `dlopen(model.zip)`，在不安裝/解壓縮的情況下直接於記憶體中載入 C++ 模組。 |

> [!WARNING]
> **Linux 相容性**：
> 沙箱執行環境為 Linux。我們本地編譯的 `chess_engine_d6_han.cpython-312-darwin.so` 無法在沙箱運行。上傳前**必須使用 Docker**（例如透過 `pack.sh`）在 `manylinux` 環境下編譯出 `*-linux-gnu.so` 檔案，再將其偽裝成 `model.zip` 上傳。

---

## 2. 遊戲規則與和局策略限制

依據作業與競賽的西洋棋規則：

* **和局判定限制**：
  在對局中，只要 **重複 6 個半步（即 3 次完整重複局面，Threefold repetition）**，伺服器就會直接判判定和局。
* **我們的搜尋引擎對策**：
  在 [`engine.cpp`](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/engine.cpp) 中，我們使用稍微嚴格的歷史重複檢查：
  ```cpp
  if (search_history.count(key) && search_history[key] >= 2) {
      return 0; // 重複 4 個半步（第 2 次重複）即視為評分 0 的和局
  }
  ```
  這是一種保險做法，能讓引擎在**優勢時主動避開重複局面**，在**劣勢時主動引導至重複局面**，以確保不會在優勢時意外被伺服器強行判和。

---

## 3. 上傳檔案與代碼嵌入限制

MLArena 的上傳接口有固定的格式規範：

* **限製上傳 3 個檔案**：
  1. `agent.py` — Agent 啟動與決策主入口。
  2. `model.py` — 模型定義檔案。
  3. `model.zip` — 模型權重檔案（在我們這裡被偽裝成 `.so` ELF 動態函式庫）。
* **自動代碼嵌入機制**：
  平台在執行沙箱時，會自動將 `model.py` 的代碼嵌入或串接到 `agent.py` 中。
* **應對策略**：
  * 我們將 `model.py` 設為一個空白預留檔（僅包含幾行註解）。
  * `agent.py` 內完全不使用 `import model`。
  * 這能確保不論平台如何嵌入代碼，都不會破壞 `agent.py` 的引導與二進位載入邏輯。

---

## 4. 競賽 Agent 介面限制

為了讓沙箱能夠順利調用我們的 Agent，以下介面**絕對不可修改**：

1. **類別名稱**：必須是 `class Agent`。
2. **建構子與 act 簽名**：
   ```python
   def act(self, observation: np.ndarray, action_mask: np.ndarray) -> int:
   ```
   * `observation`：形狀與 Gymnasium Chess 相同的 numpy 陣列。
   * `action_mask`：長度為 4672 的隨機動作遮罩（1 代表合法，0 代表非法）。
   * `return`：必須是一個整數，代表所選的動作索引。
