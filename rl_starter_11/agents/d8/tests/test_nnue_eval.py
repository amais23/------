import sys, os
import chess

# Ensure local path is used
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess_engine_d8_han

def test():
    engine = chess_engine_d8_han.SearchEngineD8()
    engine.init("")
    
    # Starting position
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    raw_score = engine.evaluate_nnue_direct(fen)
    print(f"Starting Position FEN: {fen}")
    print(f"C++ NNUE Raw Score: {raw_score}")
    print(f"C++ NNUE Centipawn Score: {raw_score / 96.0:.2f} cp")
    
    # Assert starting position score matches corrected score (2022)
    assert raw_score == 2022, f"Expected starting raw score 2022, got {raw_score}"
    print("✅ Verification successful! Raw score matches 2022 exactly.")

if __name__ == '__main__':
    test()
