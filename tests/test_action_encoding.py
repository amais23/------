import sys
import os
import unittest
import numpy as np
import chess
import pettingzoo.classic.chess.chess_utils as cu

sys.path.insert(0, "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp")
import chess_engine

class TestActionEncoding(unittest.TestCase):

    def setUp(self):
        chess_engine.init("")

    def _py_m2a(self, board, move):
        if board.turn == chess.BLACK:
            rel_board = board.mirror()
            rel_move = chess.Move(
                from_square=move.from_square ^ 56,
                to_square=move.to_square ^ 56,
                promotion=move.promotion
            )
            col = rel_move.from_square % 8
            row = rel_move.from_square // 8
            return (col * 8 + row) * 73 + cu.get_move_plane(rel_move)
        else:
            col = move.from_square % 8
            row = move.from_square // 8
            return (col * 8 + row) * 73 + cu.get_move_plane(move)

    def verify_fen(self, fen: str):
        board = chess.Board(fen)
        for move in board.legal_moves:
            uci_str = move.uci()
            py_act = self._py_m2a(board, move)
            cpp_act = chess_engine.test_move_to_action(fen, uci_str)
            self.assertEqual(py_act, cpp_act, f"Mismatch on FEN: {fen}, move: {uci_str}. Py: {py_act}, Cpp: {cpp_act}")

    def test_standard_moves(self):
        """測試常規移動和騎士移動"""
        fens = [
            chess.STARTING_FEN,
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
            "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
            "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        ]
        for fen in fens:
            self.verify_fen(fen)

    def test_promotions(self):
        """測試各種升變步 (Rook, Bishop, Knight, Queen)"""
        fens = [
            # 白兵即將在 e7 升變，黑棋有些子可以吃
            "rnbqk1nr/1pppbPpp/8/8/8/8/1PPPP1PP/RNBQKBNR w KQkq - 0 5",
            # 黑兵即將在 e2 升變
            "rnbqkbnr/1pppp1pp/8/8/8/8/1PPPBpPP/RNBQK1NR b KQkq - 0 5",
            # 複雜升變局面
            "3r4/2P5/8/8/8/8/2p5/3R4 w - - 0 1",
            "3r4/2P5/8/8/8/8/2p5/3R4 b - - 0 1",
        ]
        for fen in fens:
            self.verify_fen(fen)

    def test_en_passant(self):
        """測試吃過路兵"""
        fens = [
            # 白方可以吃過路兵
            "rnbqkbnr/pppp1ppp/8/3Pp3/8/8/PPP1PPPP/RNBQKBNR w KQkq e6 0 2",
            # 黑方可以吃過路兵
            "rnbqkbnr/ppp1pppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 2",
        ]
        for fen in fens:
            self.verify_fen(fen)

    def test_castling(self):
        """測試王車易位 (Castling)"""
        fens = [
            # 白棋和黑棋皆可雙側易位
            "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1",
            "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R b KQkq - 0 1",
            # 白棋只能王側，黑棋只能后側
            "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w Kq - 0 1",
        ]
        for fen in fens:
            self.verify_fen(fen)

if __name__ == "__main__":
    unittest.main()
