# Pull Request (PR) Template for Disservin's `chess-library`

This document contains the PR title, description, code diff, and commit message to be submitted to the official [chess-library](https://github.com/Disservin/chess-library) repository to fix the `seenSquares` early-return bug in [chess.hpp](file:///Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp/deps/chess.hpp).

---

## 1. Commit Message

```text
fix: resolve seenSquares incorrect early-return when king has no empty/enemy adjacent squares

Comment out the buggy optimization check in `seenSquares` that returns `0ull` when `map_king_atk` is empty. 
When a king is completely surrounded by friendly pieces, `map_king_atk` evaluates to `0ull`, which incorrectly skips the calculation of attack paths for all opponent pieces on the board. This allows illegal king moves or castling moves into check, causing state corruptions (e.g. king capture) during search.
```

---

## 2. Pull Request Description (English)

### Title
`fix: correct seenSquares early-return when king is completely surrounded`

### Description

#### 🔴 The Issue
In `movegen::seenSquares`, there is an early-return optimization check:
```cpp
auto king_sq          = board.kingSq(~c);
Bitboard map_king_atk = attacks::king(king_sq) & enemy_empty;

if (map_king_atk == Bitboard(0ull) && !board.chess960()) return 0ull;
```

Here, `enemy_empty` represents the squares that do not contain friendly pieces of the side whose moves are being checked (so it includes empty squares and opponent pieces).

If the king of the side to move is completely surrounded by its own friendly pieces (for example, in highly congested positions or before pieces move out of the back rank), `map_king_atk` evaluates to `0ull` because none of the adjacent squares around the king are empty or occupied by enemy pieces.

When this happens:
1. `seenSquares` immediately returns `0ull`.
2. This informs the move generator that the opponent controls **0 squares** on the entire board.
3. This allows the king to castle or move through squares controlled by the opponent's long-range slider pieces (e.g. Queens, Rooks, Bishops), since the attacked squares are incorrectly reported as safe.
4. During search tree evaluations, this leads to illegal positions where the king is captured (e.g. `Qxg8` capturing the castled king), causing `kingSq` assertions to fail or segfaults.

#### 🛠️ The Fix
Comment out or remove the buggy early-return check. Calculating the seen squares of all pieces is robust and carries negligible overhead since `seenSquares` is only called for king and castling moves.

```cpp
template <Color::underlying c>
[[nodiscard]] inline Bitboard movegen::seenSquares(const Board& board, Bitboard enemy_empty) {
    auto king_sq          = board.kingSq(~c);
    Bitboard map_king_atk = attacks::king(king_sq) & enemy_empty;

    // Commented out to prevent incorrect early-returns when the king is surrounded:
    // if (map_king_atk == Bitboard(0ull) && !board.chess960()) return 0ull;

    auto occ     = board.occ() ^ Bitboard::fromSquare(king_sq);
    ...
```

---

## 3. Code Diff

```diff
diff --git a/include/chess.hpp b/include/chess.hpp
index 1234567..89abcde 100644
--- a/include/chess.hpp
+++ b/include/chess.hpp
@@ -3912,7 +3912,7 @@ template <Color::underlying c>
 [[nodiscard]] inline Bitboard movegen::seenSquares(const Board& board, Bitboard enemy_empty) {
     auto king_sq          = board.kingSq(~c);
     Bitboard map_king_atk = attacks::king(king_sq) & enemy_empty;
 
-    if (map_king_atk == Bitboard(0ull) && !board.chess960()) return 0ull;
+    // if (map_king_atk == Bitboard(0ull) && !board.chess960()) return 0ull;
 
     auto occ     = board.occ() ^ Bitboard::fromSquare(king_sq);
     auto queens  = board.pieces(PieceType::QUEEN, c);
```
