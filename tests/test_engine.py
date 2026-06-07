import os
import sys
import unittest
import numpy as np
import chess

# 確保能 import 到 /tmp 解壓出來的 C++ 引擎
# 這裡模擬 Bootloader 載入機制
PID = os.getpid()
EXTRACT_DIR = f"/tmp/chess_assets_{PID}"
if EXTRACT_DIR not in sys.path:
    sys.path.insert(0, EXTRACT_DIR)
sys.path.insert(0, "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp")

class TestChessEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """測試前置作業：嘗試載入編譯好的 C++ 核心"""
        try:
            import chess_engine_d6_han
            cls.engine = chess_engine_d6_han.SearchEngine()
            # 初始化一個空的開局庫路徑進行測試
            cls.engine.init("")
            print("✅ 成功載入 C++ chess_engine_d6_han 模組，開始執行核心測試。")
        except ImportError:
            raise unittest.SkipTest(
                "❌ 找不到 chess_engine_d6_han.so！請確認已在 manylinux 容器內編譯並重命名置於 /tmp 下。"
            )

    def make_pettingzoo_obs(self, board: chess.Board) -> np.ndarray:
        """
        輔助工具：將 python-chess 的 Board 物件
        完美轉換為 PettingZoo 的 (8, 8, 111) 觀測值矩陣
        """
        working_board = board.mirror() if board.turn == chess.BLACK else board.copy()
        obs = np.zeros((8, 8, 111), dtype=np.int8)

        # 1. 填入王車易位權限 (Channel 0~3)
        if working_board.has_kingside_castling_rights(chess.WHITE):  obs[0, 0, 0] = 1
        if working_board.has_queenside_castling_rights(chess.WHITE): obs[0, 0, 1] = 1
        if working_board.has_kingside_castling_rights(chess.BLACK):  obs[0, 0, 2] = 1
        if working_board.has_queenside_castling_rights(chess.BLACK): obs[0, 0, 3] = 1

        # 2. 填入棋子位置 (我方 Channel 7~12, 對手 13~18)
        piece_map = {
            chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 2,
            chess.ROOK: 3, chess.QUEEN: 4, chess.KING: 5
        }

        for square in chess.SQUARES:
            piece = working_board.piece_at(square)
            if piece is not None:
                file_idx = chess.square_file(square)
                rank_idx = 7 - chess.square_rank(square)
                
                is_my_piece = (piece.color == chess.WHITE)
                base_channel = 7 if is_my_piece else 13
                channel = base_channel + piece_map[piece.piece_type]
                
                obs[rank_idx, file_idx, channel] = 1

        # 3. 處理吃過路兵 (En Passant) 標記
        if working_board.has_legal_en_passant():
            ep_sq = working_board.ep_square
            file_idx = chess.square_file(ep_sq)
            # 由於 working_board 已經翻轉，當前玩家一定是 WHITE
            obs[0, file_idx, 13] = 1

        return obs

    def test_initial_board_solve(self):
        """測試 1：初始局面下，C++ 引擎是否能正常搜尋並吐出合法 Action"""
        board = chess.Board()
        obs = self.make_pettingzoo_obs(board)
        
        # 建立一個全 1 的 action_mask (代表全合法，交給 C++ 自己剪枝)
        action_mask = np.ones(4672, dtype=np.int8)

        # 告訴 C++ 引擎我們開局是白方
        self.engine.new_game()
        
        # 執行搜尋
        action = self.engine.solve(obs, action_mask, -1)
        
        print(f"  [測試 1] 初始局面 C++ 回傳 Action Index: {action}")
        self.assertTrue(0 <= action < 4672, "Action 索引超出 PettingZoo 範圍！")

    def test_black_perspective_alignment(self):
        """測試 2：驗證黑方絕對棋盤轉換邏輯是否正確"""
        # 模擬一個經典開局：1. e4 e5 2. Nf3 (此時輪到黑方下棋)
        board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2")
        
        # 因為我們搜尋引擎使用相對棋盤，我們需要把這個黑方盤面「翻轉」成相對盤面傳給 C++
        # 在相對盤面中，黑方會誤以為自己是白方
        obs = self.make_pettingzoo_obs(board)
        action_mask = np.ones(4672, dtype=np.int8)

        # 透過 new_game 與第一次 solve 讓 C++ 觸發顏色偵測（這局我是黑方）
        self.engine.new_game()
        
        # 執行搜尋，看 C++ 會不會因為黑白轉換而崩潰或噴出非法步
        action = self.engine.solve(obs, action_mask, -1)
        
        print(f"  [測試 2] 黑方局勢下 C++ 回傳 Action Index: {action}")
        self.assertTrue(0 <= action < 4672, "黑方視角下的 Action 索引無效！")

    def test_fallback_mechanism(self):
        """測試 3：當發生極端例外或超時時，Fallback 機制是否能保底回傳隨機合法步"""
        # 給予一個故意全零的錯誤矩陣（這在 parse_observation 會噴錯或觸發初始盤面）
        invalid_obs = np.zeros((8, 8, 111), dtype=np.int8)
        
        # 故意給一個只有特定位置合法的 mask
        strict_mask = np.zeros(4672, dtype=np.int8)
        strict_mask[142] = 1  # 強制只有 index 142 合法
        
        action = self.engine.solve(invalid_obs, strict_mask, -1)
        
        print(f"  [測試 3] 例外狀況下 Fallback 回傳 Action Index: {action}")
        self.assertEqual(action, 142, "Fallback 機制未能正確遵循 action_mask 的唯一合法步！")

if __name__ == "__main__":
    unittest.main()