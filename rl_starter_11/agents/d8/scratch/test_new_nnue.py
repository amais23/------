import sys
import os
import chess

# Add agent dir to path
sys.path.insert(0, "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8")
import chess_engine_d8_han as engine

def test():
    eng = engine.SearchEngineD8()
    eng.init("")
    
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
    
    print("================ NNUE Direct Raw Evaluations ================")
    print(f"{'Position':<20} | {'Raw Score':<12}")
    print("-" * 40)
    for name, fen in positions.items():
        try:
            score = eng.evaluate_nnue_direct(fen)
            print(f"{name:<20} | {score:<12}")
        except Exception as e:
            print(f"{name:<20} | Error: {e}")

if __name__ == '__main__':
    test()
