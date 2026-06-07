import sys
import os
import unittest
import chess
import chess.polyglot

sys.path.insert(0, "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp")
import chess_engine_d6_han as chess_engine

class TestBookProbe(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 選擇一個小一點的 bin 檔案進行測試
        cls.book_path = "/Users/Shared/西洋棋代理人/Lichess_51_Books/Books/AlPhAbEtACeta.bin"
        cls.reader = chess.polyglot.open_reader(cls.book_path)

    def test_zobrist_hashing(self):
        """測試不同局面下，C++ 的 Polyglot Zobrist Hash 與 python-chess 的 Hash 是否一致"""
        fens = [
            chess.STARTING_FEN,
            # 1. e4 e5
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            # 1. e4 e5 2. Nf3 Nc6 (輪到白棋)
            "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
            # 1. e4 e5 2. Nf3 Nc6 3. Bb5 (輪到黑棋)
            "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
            # 帶有過路兵與易位的複雜局面 (白棋)
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            # 帶有過路兵與易位的複雜局面 (黑棋)
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R b KQkq - 0 1",
        ]

        for fen in fens:
            board = chess.Board(fen)
            # Python 計算絕對 Zobrist Hash
            py_hash = chess.polyglot.zobrist_hash(board)
            
            # C++ 計算 Zobrist Hash (由 test_book_info 提供)
            # 注意：不論 board.turn 是白是黑，我們在比對絕對 Hash 時，
            # 如果是黑棋，test_book_info(fen, is_black=True) 會呼叫 relative_to_absolute 把相對棋盤翻轉為絕對棋盤，然後計算它的 Zobrist Hash。
            # 但等等，此處的 fen 本身就是絕對棋盤的 FEN！
            # 如果我們傳入絕對黑棋 FEN 給 C++，C++ 重建出的 board 的 turn 是 WHITE (因為 C++ 端的 rebuild_fen_from_observation 永遠將其重建為 w)。
            # 等等！讓我們看看 `rebuild_fen_from_observation` L502：
            # `return placement + " w " + castling_str + " " + ep_str + " 0 1";`
            # 這代表 C++ 中重建出的 Board 永遠是 WHITE 走步 (相對視角)！
            # 也就是說，如果我們在 Python 端做 `chess_engine.solve(obs, mask)`，
            # 傳入的 `obs` 已經是相對棋盤了，所以 C++ 重建出來的 `board` 必定是相對棋盤 (Turn 也是 w)。
            # 當真實棋盤是黑棋時，C++ 的 `solve` 會檢測到 `is_black = true`，然後在查開局庫時呼叫 `relative_to_absolute(board)`，把它還原成絕對棋盤，再去計算 Zobrist Hash！
            # 所以！如果我們想在 `test_book_info` 裡測試這個「相對還原成絕對」的邏輯：
            # 我們應該傳入一個相對棋盤的 FEN 給 `test_book_info`！
            # 例如：真實局面是絕對黑棋 FEN，其轉成相對 FEN (即 turn 也是 w，且黑白 pieces 互換、y 軸翻轉)。
            # 然後我們把這個相對 FEN 傳給 `test_book_info(rel_fen, is_black=True)`。
            # 那麼 C++ 的 `test_book_info` 應該會把它還原成絕對 FEN (即原來的絕對黑棋 FEN)，算出的 Hash 應該與原來的絕對黑棋 FEN 的 python-chess hash 一致！
            
            # 讓我們來寫這個測試邏輯：
            if board.turn == chess.WHITE:
                # 白棋直接測，相對跟絕對是一樣的
                cpp_hash, cpp_move = chess_engine.test_book_info(fen, False)
                self.assertEqual(py_hash, cpp_hash, f"Hash mismatch for White FEN: {fen}")
            else:
                # 黑棋：我們先將絕對棋盤轉成相對棋盤，再傳給 C++
                rel_board = board.mirror()
                rel_fen = rel_board.fen()
                
                # C++ 接收相對棋盤並還原
                cpp_hash, cpp_move = chess_engine.test_book_info(rel_fen, True)
                self.assertEqual(py_hash, cpp_hash, f"Hash mismatch for Black FEN: {fen} (Rel FEN: {rel_fen})")

    def test_book_probing_moves(self):
        """測試 C++ 查出的 Move 是否包含在 python-chess 查出的合法開局移動中"""
        # 尋找一個在開局庫中有匹配的局面
        # 初始局面一定有
        board = chess.Board()
        py_entries = list(self.reader.find_all(board))
        py_moves = {entry.move.uci() for entry in py_entries}
        
        # 測試 20 次，看 C++ 隨機選出的 move 是否都在 py_moves 中
        for _ in range(20):
            cpp_hash, cpp_move = chess_engine.test_book_info(board.fen(), False)
            if cpp_move:
                self.assertIn(cpp_move, py_moves, f"Cpp move {cpp_move} not in Python book entries: {py_moves}")

        # 測試黑棋的局面，例如 1. e4
        board = chess.Board("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
        py_entries = list(self.reader.find_all(board))
        py_moves = {entry.move.uci() for entry in py_entries}
        
        if py_moves:
            # 我們將絕對黑棋棋盤轉成相對棋盤 FEN
            rel_board = board.mirror()
            rel_fen = rel_board.fen()
            
            for _ in range(20):
                # C++ 還原絕對棋盤並查詢，回傳在相對棋盤上的移動
                cpp_hash, cpp_move_rel = chess_engine.test_book_info(rel_fen, True)
                
                if cpp_move_rel:
                    # 還原後的相對移動，必須能被轉回絕對移動
                    # 例如相對 move 轉絕對 move：from 和 to 都要 ^ 56
                    m_rel = chess.Move.from_uci(cpp_move_rel)
                    m_abs = chess.Move(
                        from_square=m_rel.from_square ^ 56,
                        to_square=m_rel.to_square ^ 56,
                        promotion=m_rel.promotion
                    )
                    cpp_move_abs = m_abs.uci()
                    self.assertIn(cpp_move_abs, py_moves, f"Cpp absolute move {cpp_move_abs} (rel: {cpp_move_rel}) not in Python book entries: {py_moves}")

if __name__ == "__main__":
    unittest.main()
