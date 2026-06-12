import os
import sys
import torch
import chess
import numpy as np

sys.path.insert(0, "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8")
from scratch.train_nnue import NNUE, get_piece_features, get_enemy_features

model_save_path = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/weights/trained_model.pt"

def test():
    device = torch.device("cpu")
    model = NNUE()
    model.load_state_dict(torch.load(model_save_path, map_location=device))
    model.eval()
    
    positions = {
        "Start": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Up Pawn (d7)": "rnbqkbnr/ppp1pppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Down Pawn (d2)": "rnbqkbnr/pppppppp/8/8/8/8/PPP1PPPP/RNBQKBNR w KQkq - 0 1",
        "Up Knight (g8)": "rnbqkb1r/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Down Knight (g1)": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKB1R w KQkq - 0 1",
        "Up Queen (d8)": "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Down Queen (d1)": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1",
        "K+Q vs K": "k7/8/8/8/8/8/8/K1Q5 w - - 0 1",
        "K+R vs K": "k7/8/8/8/8/8/8/K1R5 w - - 0 1",
        "KvK": "k7/8/8/8/8/8/8/K7 w - - 0 1",
        "K vs K+R": "k7/8/8/8/8/8/8/K1R5 b - - 0 1"
    }
    
    print("================ PyTorch Float Predictions ================")
    print(f"{'Position':<20} | {'Float Output':<12}")
    print("-" * 40)
    for name, fen in positions.items():
        board = chess.Board(fen)
        is_white_pov = (board.turn == chess.WHITE)
        us = get_piece_features(board, is_white_pov)
        them = get_enemy_features(board, is_white_pov)
        
        us_t = torch.tensor(us, dtype=torch.long).unsqueeze(0)
        them_t = torch.tensor(them, dtype=torch.long).unsqueeze(0)
        us_offsets = torch.tensor([0], dtype=torch.long)
        them_offsets = torch.tensor([0], dtype=torch.long)
        
        with torch.no_grad():
            pred = model(us_t[0], us_offsets, them_t[0], them_offsets)
            val = pred.item()
            print(f"{name:<20} | {val:<12.5f}")

if __name__ == '__main__':
    test()
