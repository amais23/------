# 伺服器的和局邏輯有bug

對局 <https://mlarena.spkuan.cc/rl/battles/2398> 中，第十場比賽（Episode 9，0-indexed）錯誤的和局了，當時比賽還沒結束。

## Bug 分析

| 項目 | 結果 |
|---|---|
| 步數（雙方合計） | 96 步 |
| `board.is_game_over()` | **False** — 棋局未結束 |
| `board.can_claim_draw()` | **True** — 可主張和局（但非強制）|
| 三重複局？ | **False** |
| 五重複局？ | **False** |
| 50步規則計數（halfmove clock） | 10（距50步規則還很遠）|
| 最終局面 FEN | `1k6/8/5p1p/1P4p1/2R1K3/6P1/r4P1P/8 w - - 10 49` |

**結論：** `can_claim_draw()` 為 True 表示在第 96 步（Step 95 結束後）輪到白方時，白方**可以主張**和局。但伺服器直接強制判和，而非等待玩家主張，行為有誤。白方（41241213S）有車在 c4、王在 e4，局面仍在優勢中。

### 關於「重複三次」的詳細分析

經分析，**在棋局被伺服器終止前，沒有任何一個棋面實際重複出現過三次**。整個對局中重複次數最多的棋面也只出現了 **2 次**：

1. **棋面 A**（白王在 e3，黑車在 a2）出現了 **2 次**：
   - 第 45 回合白方走完後（Step 88，FEN: `1k6/8/5p1p/1P4p1/2R5/4K1P1/r4P1P/8 b - -`）
   - 第 47 回合白方走完後（Step 92，同上 FEN）
2. **棋面 B**（白王在 e3，黑車在 a3）出現了 **2 次**：
   - 第 45 回合黑方走完後（Step 89，FEN: `1k6/8/5p1p/1P4p1/2R5/r3K1P1/5P1P/8 w - -`）
   - 第 47 回合黑方走完後（Step 93，同上 FEN）

**為什麼 `board.can_claim_draw()` 會是 True？**
在 Step 95（第 48 回合黑方走 `Ra7`）結束後，輪到白方走棋：
- 當前棋面（白王在 e4，黑車在 a7，FEN: `1k6/8/5p1p/1P4p1/2R1K3/6P1/r4P1P/8 w - -`）此前只出現過 1 次。
- 但白方有一個合法移動 **`Ke3`**（UCI: `e4e3`），如果白方選擇走這一步，棋盤將會轉化為上述已出現過兩次的 **棋面 A**（即第三次出現）。
- 根據西洋棋 FIDE 規則，當輪到某方走棋，且該方**即將下出的一步會導致棋面第三次重複**時，該方可以合法主張和局（Claim a draw）。
- 因此，python-chess 的 `board.can_claim_threefold_repetition()` 與 `board.can_claim_draw()` 在此時回傳了 `True`。

**伺服器的 Bug 在哪裡？**
伺服器並沒有等待白方決定是否走 `Ke3` 並主動聲明和局，而是在**黑方剛下完第 95 步後**（此時白方尚未下子，且場面上沒有任何棋面重複了三次），就直接由伺服器強制判和。這是不符合西洋棋規則的。


## 棋局資訊

- **白方（Player 0）：** 41241213S（D6 Engine，slot 8，ELO 1572）
- **黑方（Player 1）：** 41275022H（Try，slot 160，ELO 1399）
- **其他9場比賽結果：** 白方全勝（9–0），此為錯誤和局的第10場

## 棋譜（PGN）

```pgn
[Event "ML Arena Battle #2398 Episode 10"]
[Site "https://mlarena.spkuan.cc/rl/battles/2398"]
[Date "2026.06.07"]
[Round "10"]
[White "41241213S (D6 Engine)"]
[Black "41275022H (Try)"]
[Result "1/2-1/2"]
[WhiteElo "1572"]
[BlackElo "1399"]

1. c4 d5 2. cxd5 Qxd5 3. d4 e5 4. Nf3 Bb4+ 5. Bd2 Bxd2+ 6. Qxd2 exd4 7. Nc3 Qd7
8. Nxd4 Nc6 9. Ndb5 Qxd2+ 10. Kxd2 Kd8 11. Nd5 Bd7 12. Nbxc7 Rc8 13. Nb5 Nge7
14. e4 Nxd5 15. exd5 Nb4 16. a3 Bxb5 17. axb4 Bxf1 18. Rhxf1 a6 19. Rfc1 Re8
20. Rxc8+ Kxc8 21. Kd3 Kb8 22. Ra5 Re1 23. g3 Rf1 24. Ke3 Rd1 25. Rc5 f6 26. b5
axb5 27. Rxb5 h6 28. Ke2 Ra1 29. d6 Ra6 30. Rd5 Kc8 31. d7+ Kd8 32. Rb5 b6 33.
Rd5 Ra7 34. Rd6 b5 35. Rd5 b4 36. Rd4 b3 37. Rd3 Rxd7 38. Rxb3 Kc8 39. Rc3+ Kb8
40. Rc4 Rb7 41. b4 Ra7 42. b5 Ra1 43. Rg4 g5 44. Rc4 Ra2+ 45. Ke3 Ra3+ 46. Kd4
Ra2 47. Ke3 Ra3+ 48. Ke4 Ra2 1/2-1/2
```

## 原始 API 資料（action indices）

以下為 `/api/rl/battles/2398/replay` 回傳的第10場（`game: 9`）原始步驟：

```
step  0  player=0  action=1253  → c7c5
step  1  player=1  action=1837  → d2d4
step  2  player=0  action=1394  → c5d4
step  3  player=1  action=1772  → d1d4
step  4  player=0  action=1837  → d7d5
step  5  player=1  action=2421  → e2e4
step  6  player=0  action=3563  → g8f6
step  7  player=1  action=2946  → f1b5
step  8  player=0  action=1175  → c8d7
step  9  player=1  action=891   → b5d7
step 10  player=0  action=1756  → d8d7
step 11  player=1  action=2557  → e4d5
step 12  player=0  action=645   → b8c6
step 13  player=1  action=1982  → d4d2
step 14  player=0  action=3123  → f6d5
step 15  player=1  action=645   → b1c3
step 16  player=0  action=2028  → d5b4
step 17  player=1  action=1861  → d2d7
step 18  player=0  action=2338  → e8d7
step 19  player=1  action=2337  → e1d1
step 20  player=0  action=1375  → c6d4
step 21  player=1  action=1175  → c1d2
step 22  player=0  action=937   → b4c2
step 23  player=1  action=14    → a1c1
step 24  player=0  action=1664  → c2b4
step 25  player=1  action=3561  → g1e2
step 26  player=0  action=2421  → e7e5
step 27  player=1  action=2468  → e2d4
step 28  player=0  action=2557  → e5d4
step 29  player=1  action=1373  → c3b5
step 30  player=0  action=77    → a7a6
step 31  player=1  action=1835  → d2b4
step 32  player=0  action=153   → a6b5
step 33  player=1  action=834   → b4f8
step 34  player=0  action=4097  → h8f8
step 35  player=1  action=77    → a2a3
step 36  player=0  action=2937  → f8c8
step 37  player=1  action=4105  → h1e1
step 38  player=0  action=1220  → c8c1
step 39  player=1  action=1753  → d1c1
step 40  player=0  action=1829  → d7d6
step 41  player=1  action=1169  → c1b1
step 42  player=0  action=28    → a8a4
step 43  player=1  action=2388  → e1e8
step 44  player=0  action=3581  → g7g6
step 45  player=1  action=2853  → e8f8
step 46  player=0  action=1904  → d6e6
step 47  player=1  action=3440  → f8d8
step 48  player=0  action=306   → a4c4
step 49  player=1  action=2997  → f2f3
step 50  player=0  action=807   → b5b4
step 51  player=1  action=153   → a3b4
step 52  player=0  action=1461  → c4b4
step 53  player=1  action=4165  → h2h3
step 54  player=0  action=2485  → e6e7
step 55  player=1  action=2280  → d8a8
step 56  player=0  action=2048  → d4d3
step 57  player=1  action=546   → a8a3
step 58  player=0  action=890   → b4d4
step 59  player=1  action=590   → b1c1
step 60  player=0  action=2121  → d3d2
step 61  player=1  action=1174  → c1d1
step 62  player=0  action=2053  → d4b4
step 63  player=1  action=661   → b2b3
step 64  player=0  action=890   → b4d4
step 65  player=1  action=149   → a3a2
step 66  player=0  action=2048  → d4d3
step 67  player=1  action=734   → b3b4
step 68  player=0  action=2120  → d3d4
step 69  player=1  action=807   → b4b5
step 70  player=0  action=2047  → d4d5
step 71  player=1  action=880   → b5b6
step 72  player=0  action=1974  → d5d6
step 73  player=1  action=95    → a2d2
step 74  player=0  action=1907  → d6b6
step 75  player=1  action=1753  → d1c1
step 76  player=0  action=736   → b6c6
step 77  player=1  action=1169  → c1b1
step 78  player=0  action=1318  → c6c5
step 79  player=1  action=1834  → d2b2
step 80  player=0  action=669   → b7b5
step 81  player=1  action=658   → b2a2
step 82  player=0  action=807   → b5b4
step 83  player=1  action=117   → a2a8
step 84  player=0  action=1417  → c5g5
step 85  player=1  action=3589  → g2g4
step 86  player=0  action=3748  → g5c5
step 87  player=1  action=514   → a8a7
step 88  player=0  action=2413  → e7e6
step 89  player=1  action=441   → a7a6
step 90  player=0  action=2484  → e6d5
step 91  player=1  action=369   → a6a7
step 92  player=0  action=1976  → d5e6
step 93  player=1  action=441   → a7a6
step 94  player=0  action=2486  → e6e5
step 95  player=1  action=369   → a6a7  ← 遊戲在此被伺服器錯誤終止
```

## 最終局面

```
1k6/8/5p1p/1P4p1/2R1K3/6P1/r4P1P/8 w - - 10 49
```

```
. k . . . . . .   8
. . . . . . . .   7
. . . . . p . p   6
. P . . . . p .   5
. . R . K . . .   4
. . . . . . P .   3
r . . . . P . P   2
. . . . . . . .   1
a b c d e f g h
```

白方（白王在 e4，白車在 c4，白兵在 b5/g3）仍有繼續作戰的能力，伺服器不應在此時強制判和。
