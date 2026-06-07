# ML Arena API 規格與對局分析報告 (以 Battle #1151 為例)

本文件整理了 **ML Arena** 平台的所有後端 API 端點規格，並以 **Battle #1151** 的棋譜回放分析為例，展示如何對平台提供的原生 JSON 棋譜數據進行解析與重建。

---

## 第一部分：ML Arena 平台 API 規格整理

### 1. 驗證與使用者管理 (Authentication & User Profile)

所有一般對戰相關 API 需要透過 HTTP Header 進行身份驗證：

* **API Key 驗證**：在 Header 中帶入 `X-API-Key: <your_api_key>`。
* **JWT 驗證**：在 Header 中帶入 `Authorization: Bearer <access_token>`。

* **領取帳號 (Claim Account)**: `POST /api/enroll/claim`
  * 用於初次綁定學號並生成 API Key。
* **登入驗證 (Login)**: `POST /api/auth/login`
  * 回傳 JWT Token，支援多因素驗證 (MFA)。
* **使用者資料 (Get Me)**: `GET /api/users/me`
  * 取得當前使用者的完整資訊與 assigned API Key。

### 2. RL 競賽槽位管理 (RL Competition Slots)

每個使用者在競賽中分配有多個 Agent 槽位，可用於管理不同版本的模型。

* **取得槽位列表 (Get Slots)**: `GET /api/rl/competitions/{competition_id}/slots`
  * 回傳所有槽位的 Elo 分數、對局次數與權重狀態。
* **更新槽位代理人 (Upload Slot)**: `POST /api/rl/competitions/{competition_id}/slots`
  * 以 `multipart/form-data` 上傳 `agent.py`、`model.py` 與 `weights_file`。
* **設定自動出戰 (Set Auto-Battle)**: `POST /api/rl/competitions/{competition_id}/slots/{slot_index}/set-auto-battle`
  * 指定某個槽位為自動出戰代理人。

### 3. 配對與佇列 (Matchmaking & Queue)

* **加入佇列 (Join Queue)**: `POST /api/rl/competitions/{competition_id}/queue`
  * 傳入 `slot_id` 進入配對大廳進行線上 PvP。
* **離開佇列 (Leave Queue)**: `DELETE /api/rl/competitions/{competition_id}/queue`
* **查詢排隊狀態 (Get Queue Status)**: `GET /api/rl/competitions/{competition_id}/queue/status`
  * 查詢目前是否在排隊中，以及是否配對成功（`status: "matched"` 並附帶 `matched_session_id`）。

### 4. 對局與回放 (Battles & Replays)

* **取得對戰歷史 (Get Battles)**: `GET /api/rl/competitions/{competition_id}/battles`
* **取得釘選精彩對戰 (Get Pinned Battles)**: `GET /api/rl/competitions/{competition_id}/battles/pinned`
* **取得單一對局細節 (Get Battle Detail)**: `GET /api/rl/battles/{battle_id}`
* **取得對局回放棋譜 (Get Battle Replay)**: `GET /api/rl/battles/{battle_id}/replay`
  * 回傳該場戰役（10局）的完整動作編碼步驟。
* **單人測試賽 (Run Solo)**: `POST /api/rl/battles/solo`

---

## 第二部分：對局回放 API 格式與分析 (Battle #1151 實例)

### 1. Replay 原始回傳 JSON 格式

當調用 `GET /api/rl/battles/1151/replay` 時，後端會回傳如下結構：

```json
{
  "games": 10,       // 對戰的總局數
  "wins": [8, 0],    // 雙方獲勝局數 [Player 0 獲勝, Player 1 獲勝]
  "draws": 2,        // 和局數
  "steps": [         // 十局中所有按順序發生的棋步
    {
      "game": 0,     // 局數索引 (0-9)
      "step": 0,     // 局內步數索引 (從 0 開始)
      "player": 0,   // 出子玩家的索引 (0 或 1)
      "action": 3563 // 動作編碼 (0-4671)
    },
    ...
  ]
}
```

* **動作編碼格式**：此處的 `action` 為 PettingZoo Chess 的 `Discrete(4672)` 動作空間索引（$8 \times 8 \times 73$）。
* **分析挑戰**：由於 PettingZoo Chess 會為當前行動者旋轉棋盤（使行動者視角永遠在白方下側），故在還原 Player 1 (黑方) 的棋步時，需先做鏡像還原，才能得到正確的真實棋步。

---

### 2. Battle #1151 對戰重建與解析

#### 📌 基本資訊

* **對戰 ID**: 1151
* **Player 0**: **D4 Pro v2** (我們的 Agent - 學號 `41241213S`, ELO 1592.9 $\rightarrow$ 1593.2)
* **Player 1**: **JT_agent** (對手 Agent - 學號 `41375007H`, ELO 923.1 $\rightarrow$ 922.8)
* **最終結果**: Player 0 (D4 Pro v2) 獲得 **8 勝 0 敗 2 和**，總比分 8.0 - 0.0，取得勝利。

#### 📌 典型對局棋譜重建 (以 Game 0 為例)

Game 0 共歷時 25 步，最終白方在第 13 手以皇后將死黑方獲勝：

> **`1. Nf3 Na6 2. Nc3 Rb8 3. e4 Nb4 4. a3 Nd3+ 5. Bxd3 Ra8 6. e5 Rb8 7. Nb5 Ra8 8. Ng5 Rb8 9. Bxh7 Ra8 10. d4 Rb8 11. Nxa7 Ra8 12. Qh5 Rb8 13. Qxf7#`**
>
> * **白方 (我方 D4 Pro v2) 表現**：出子極具邏輯，第 1 手 Nf3 穩定控制中心，第 12 手將皇后挺進至 Qh5 威脅 f7 弱點，並於第 13 手迅速將死。
> * **黑方 (JT_agent) 表現**：走子極為消極且不合常理。黑馬與黑車一直在 `Na6` / `Rb8` / `Nb4` / `Ra8` 來回移動，並且在第 4 手將馬送到白方象口 (`Nd3+`) 進行無意義的犧牲。這表明 JT_agent 的模型缺乏有效的走子評估，或陷入了局部的死循環。

#### 📌 和局分析 (以 Game 2 與 Game 3 為例)

* **Game 2 棋譜**：
    `1. Nf3 Na6 2. Nc3 Rb8 3. e4 Nb4 4. a3 Nd3+ 5. Bxd3 Ra8 6. e5 Rb8 7. Nb5 Ra8 8. Nc3 Rb8 9. Nb5 Ra8 ...` (在第 18 步終止)
* **原因說明**：
    黑方不斷重複 `Rb8` 與 `Ra8`，而我方在確定優勢或局勢下，也在 `Nb5` 與 `Nc3` 來回重複。雙方在連續重複同一位置達三次後，觸發西洋棋的 **三次重複局面 (Threefold Repetition)** 規則，因而被系統直接裁定為和局。這說明搜尋引擎在對抗無反應的對手時，若無開局庫或特殊的多樣化隨機因子介入，有機會因追求分數平穩而落入重複走子的陷阱。

## 完整對局

Battle ID: 1151
Status: completed
Participants:

* Player 2120: 41241213S | Slot: D4 Pro v2 (ID: 7) | Elo Before: 1592.9 | Elo After: 1593.2 | Delta: +0.3315 | Final Rank: 1 | Final Score: 8.0
* Player 2121: 41375007H | Slot: JT_agent (ID: 49) | Elo Before: 923.1 | Elo After: 922.8 | Delta: -0.3315 | Final Rank: 2 | Final Score: 0.0

--- Game 0 ---
Moves: 1. Nf3 Na6 2. Nc3 Rb8 3. e4 Nb4 4. a3 Nd3+ 5. Bxd3 Ra8 6. e5 Rb8 7. Nb5 Ra8 8. Ng5 Rb8 9. Bxh7 Ra8 10. d4 Rb8 ... Rb8 9. Bxh7 Ra8 10. d4 Rb8 11. Nxa7 Ra8 12. Qh5 Rb8 13. Qxf7#
Total Moves: 25
Result: 1-0 (White Win)
Final FEN: 1rbqkbnr/NppppQpB/8/4P1N1/3P4/P7/1PP2PPP/R1B1K2R b KQk - 0 13

--- Game 1 ---
Moves: 1. Nf3 Na6 2. Nc3 Rb8 3. e4 Nb4 4. a3 Nd3+ 5. Bxd3 Ra8 6. e5 Rb8 7. Nb5 Ra8 8. O-O Rb8 9. Nxa7 Ra8 10. Nxc8 Ra7 ... Kd8 15. Ng5 Kc8 16. Nxf7 Kb8 17. Nxh8 Ka8 18. Qf3 Kb8 19. Qxf8#
Total Moves: 37
Result: 1-0 (White Win)
Final FEN: 1k3QnN/1pppp1pp/8/1N2P3/8/P2B4/1PPP1PPP/R1B2RK1 b - - 0 19

--- Game 2 ---
Moves: 1. Nf3 Na6 2. Nc3 Rb8 3. e4 Nb4 4. a3 Nd3+ 5. Bxd3 Ra8 6. e5 Rb8 7. Nb5 Ra8 8. Nc3 Rb8 9. Nb5 Ra8 ...
Total Moves: 18
Result: Incomplete (Stops at step 18)
Final FEN: r1bqkbnr/pppppppp/8/1N2P3/8/P2B1N2/1PPP1PPP/R1BQK2R w KQk - 7 10

--- Game 3 ---
Moves: 1. Nf3 Na6 2. Nc3 Rb8 3. e4 Nb4 4. a3 Nd3+ 5. Bxd3 Ra8 6. O-O Rb8 7. Nb5 Ra8 8. Nbd4 Rb8 9. Nb5 Ra8 10. Ne5 Rb8 ...
Total Moves: 20
Result: Incomplete (Stops at step 20)
Final FEN: 1rbqkbnr/pppppppp/8/1N2N3/4P3/P2B4/1PPP1PPP/R1BQ1RK1 w k - 11 11

--- Game 4 ---
Moves: 1. Nf3 Na6 2. Nc3 Rb8 3. e4 Nb4 4. a3 Nd3+ 5. Bxd3 Ra8 6. O-O Rb8 7. Nb5 Ra8 8. Re1 Rb8 9. Nxa7 Ra8 10. Nxc8 Ra7 ... Ka8 18. Nxc7+ Ka7 19. Nb5+ Ka8 20. e5 Kb8 21. Qf3 Ka8 22. Qxf8#
Total Moves: 43
Result: 1-0 (White Win)
Final FEN: k4QnN/1p1pp1pp/8/1N2P3/8/P2B4/1PPP1PPP/R1B1R1K1 b - - 0 22

--- Game 5 ---
Moves: 1. Nf3 Na6 2. Nc3 Rb8 3. e4 Nb4 4. a3 Nd3+ 5. Bxd3 Ra8 6. O-O Rb8 7. Nb5 Ra8 8. h3 Rb8 9. Nxa7 Ra8 10. Nxc8 Ra7 ... Ka8 18. Nxc7+ Ka7 19. Nb5+ Ka8 20. e5 Kb8 21. Qf3 Ka8 22. Qxf8#
Total Moves: 43
Result: 1-0 (White Win)
Final FEN: k4QnN/1p1pp1pp/8/1N2P3/8/P2B3P/1PPP1PP1/R1B2RK1 b - - 0 22

--- Game 6 ---
Moves: 1. Nf3 Na6 2. Nc3 Rb8 3. e4 Nb4 4. a3 Nd3+ 5. Bxd3 Ra8 6. O-O Rb8 7. e5 Ra8 8. Ng5 Rb8 9. Qf3 Ra8 10. Qxf7# ...
Total Moves: 19
Result: 1-0 (White Win)
Final FEN: r1bqkbnr/pppppQpp/8/4P1N1/8/P1NB4/1PPP1PPP/R1B2RK1 b k - 0 10

--- Game 7 ---
Moves: 1. Nf3 Na6 2. Nc3 Rb8 3. e4 Nb4 4. Nb5 Nd3+ 5. Bxd3 Ra8 6. O-O Rb8 7. Nxa7 Ra8 8. Nxc8 Ra7 9. Nxa7 Qc8 10. Nxc8 Kd8 ... Ka8 16. Nxc7+ Ka7 17. Nb5+ Ka8 18. e5 Kb8 19. Qf3 Ka8 20. Qxf8#
Total Moves: 39
Result: 1-0 (White Win)
Final FEN: k4QnN/1p1pp1pp/8/1N2P3/8/3B4/PPPP1PPP/R1B2RK1 b - - 0 20

--- Game 8 ---
Moves: 1. Nf3 Na6 2. Nc3 Rb8 3. e4 Nb4 4. Nb5 Nd3+ 5. Bxd3 Ra8 6. O-O Rb8 7. Nxa7 Ra8 8. Nxc8 Ra7 9. Nxa7 Qc8 10. Nxc8 Kd8 ... Kd8 11. Ne5 Ke8 12. Qh5 Kd8 13. Nxf7+ Ke8 14. Nfd6+ Kd8 15. Qe8#
Total Moves: 29
Result: 1-0 (White Win)
Final FEN: 2NkQbnr/1pppp1pp/3N4/8/4P3/3B4/PPPP1PPP/R1B2RK1 b - - 4 15

--- Game 9 ---
Moves: 1. Nf3 Na6 2. Nc3 Rb8 3. e5 Rb8 7. Nxa7 Ra8 8. Nxc8 Ra7 9. Nxa7 Qc8 10. Nxc8 Kd8 ... Kd8 13. Ng5 Kc8 14. Nxf7 Kb8 15. Nxh8 Ka8 16. Qf3 Kb8 17. Qxf8#
Total Moves: 33
Result: 1-0 (White Win)
Final FEN: 1k3QnN/1pppp1pp/8/1N2P3/8/3B4/PPPP1PPP/R1B1K2R b KQ - 0 17

---

## 第三部分：Battle #1424 對局分析與戰術檢討

### 1. 戰役基本資訊
*   **對戰 ID**: 1424
*   **Player 0 (White)**: **D4_6** (我們的 Agent - 學號 `41241213S`, ELO 1559.6 $\rightarrow$ 1553.1)
*   **Player 1 (Black)**: **My Chess Agent 1** (對手 Agent - 學號 `41275022H`, ELO 1162.1 $\rightarrow$ 1174.5)
*   **最終結果**: **10 局皆為和局 (10 Draws)**，總比分 5.0 - 5.0。
*   **Elo 變動**: 我方 ELO 減少了 **-6.5266** 分。這是因為在 Elo 計分系統中，高分段代理人被低分段代理人逼和會受到較大懲罰。

### 2. 典型對局棋譜重建 (十局走子完全一致)
由於雙方皆為確定性 (Deterministic) 決策模型，十局對局走法與結果完全相同。以下為 Game 0 的完整棋步分析：

> **`1. Nc3 Nf6 2. Nf3 Nc6 3. d4 d5 4. e3 e6 5. Bd3 Bd6 6. Bb5 O-O 7. Bxc6 bxc6 8. Ne5 Bb7 9. Rb1 Nd7 10. Qh5 Nf6 11. Qg5 Ne4 12. Nxe4 dxe4 13. Qxd8 Rfxd8 14. Nc4 Bb4+ 15. Kd1 Rab8 16. a3 Be7 17. Ne5 c5 18. c3 f6 19. Nc4 e5 20. Ra1 exd4 21. cxd4 cxd4 22. exd4 Rxd4+ 23. Nd2 Bd6 24. h3 f5 25. Ra2 Bd5 26. Ra1 Rd8 27. Rb1 Ba2 28. Ra1 Bb3+ 29. Ke1 Bd5 30. Rb1 Ba2 31. Ra1 Bd5 32. Rb1 Ba2 33. Ra1`** (第 65 步終止)
> 
> *   **中局戰術失誤 (第 19~22 手)**：
>     我方執白在第 19 手將馬退回 `c4`，給了黑方在中心發動 `e5` 與 `exd4` 攻勢的機會。在第 22 手黑方 `22... Rxd4+` 將軍同時抽雙我方 `c4` 上的馬，我方被迫以 `23. Nd2` 擋將，導致該馬被釘死，且隨後黑方透過雙車重疊在 d 檔上持續施壓，我方因而淨輸一隻大車，局勢崩盤（子力差達到 -5，FEN: `3r2k1/p1p3pp/3d4/5p2/3rp3/P6P/bP1N1PP1/R1B1K2R b - - 17 33`）。
> 
> *   **利用「三次重複局面」戰術避敗 (第 29~33 手)**：
>     當局勢陷入必敗且子力差距過大時，我方的 Alpha-Beta 搜尋引擎評估到若進行正常對局將獲得極低的分數（約 -500 分），但若能促成「三次重複局面」，在評估函數中會被判定為 `0` 分。
>     因此，我方主動尋求重複走子（將車在 `a1` 與 `b1` 之間反覆移動）。
> 
> *   **對手配合逼和**：
>     對手 **My Chess Agent 1** (Elo 1162) 由於同樣缺乏重複局面懲罰機制，或者程式決策完全確定，因而配合我方的反覆挑釁，將象在 `a2` 與 `d5` 之間來回移動。最終雙方在第 30、31、32、33 手形成三次重複局面，系統判定為和局。

### 3. 戰術與優化建議
1.  **增加隨機性與多樣性**：由於 10 局比賽走法完全相同，若我們的 Agent 存在戰術盲點，容易被對方以相同的走法連續逼和 10 局。應在開局庫階段或前幾手引入輕微的隨機選擇權重，使每局走法不同。
2.  **深化中局戰術搜尋**：對手在第 22 手的 `Rxd4+` 抽雙是個簡單的兩步戰術漏洞，說明搜尋深度在中局因時間限制縮水，或靜態搜尋 (Quiescence Search) 尚未涵蓋這類非吃子將軍/抽雙的局面。
3.  **加入重複局面懲罰/歷史 Zobrist 雜湊追蹤**：目前已在 `d4_pro` 中新增了 `real_game_history` 與 `search_history` 機制，這能有效防止我們在**佔優勢時**誤入重複走子的死循環，並能更聰明地避開對手的主動逼和。

