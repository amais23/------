import numpy as np
import chess
import pettingzoo.classic.chess.chess_utils as cu

# Add parent dir to path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from d8.agent import Agent

def test_agent():
    agent = Agent()
    board = chess.Board()
    
    # Let's construct a PettingZoo observation
    def get_obs(board):
        obs = np.zeros((8, 8, 111), dtype=np.int8)
        is_white = (board.turn == chess.WHITE)
        if is_white:
            if board.has_kingside_castling_rights(chess.WHITE): obs[0, 0, 0] = 1
            if board.has_queenside_castling_rights(chess.WHITE): obs[0, 0, 1] = 1
            if board.has_kingside_castling_rights(chess.BLACK): obs[0, 0, 2] = 1
            if board.has_queenside_castling_rights(chess.BLACK): obs[0, 0, 3] = 1
        else:
            if board.has_kingside_castling_rights(chess.BLACK): obs[0, 0, 0] = 1
            if board.has_queenside_castling_rights(chess.BLACK): obs[0, 0, 1] = 1
            if board.has_kingside_castling_rights(chess.WHITE): obs[0, 0, 2] = 1
            if board.has_queenside_castling_rights(chess.WHITE): obs[0, 0, 3] = 1
        
        piece_map = {chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 2, chess.ROOK: 3, chess.QUEEN: 4, chess.KING: 5}
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece is not None:
                if is_white:
                    r = 7 - (sq // 8)
                    ch = (7 + piece_map[piece.piece_type]) if piece.color == chess.WHITE else (13 + piece_map[piece.piece_type])
                else:
                    r = sq // 8
                    ch = (7 + piece_map[piece.piece_type]) if piece.color == chess.BLACK else (13 + piece_map[piece.piece_type])
                c = sq % 8
                obs[r, c, ch] = 1
        return obs

    def get_mask(board):
        is_white = (board.turn == chess.WHITE)
        mask = np.zeros(4672, dtype=np.int8)
        for move in board.legal_moves:
            if is_white:
                rel_move = move
            else:
                rel_move = chess.Move(
                    chess.square_mirror(move.from_square),
                    chess.square_mirror(move.to_square),
                    promotion=move.promotion
                )
            col = rel_move.from_square % 8
            row = rel_move.from_square // 8
            act_idx = (col * 8 + row) * 73 + cu.get_move_plane(rel_move)
            if 0 <= act_idx < 4672:
                mask[act_idx] = 1
        return mask

    obs = get_obs(board)
    mask = get_mask(board)
    
    print("Act on starting position:")
    action = agent.act(obs, mask)
    print("Action:", action)
    print("Last NPS:", agent.last_nps)
    print("Last Score:", agent.last_score)

if __name__ == '__main__':
    test_agent()
