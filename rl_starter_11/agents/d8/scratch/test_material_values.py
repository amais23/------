import sys, os
import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import chess_engine_d8_han
from tests.test_cpp_vs_python import py_evaluate

def test():
    engine = chess_engine_d8_han.SearchEngineD8()
    engine.init("")
    
    fens = {
        "Start": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Up Pawn (d7)": "rnbqkbnr/ppp1pppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Down Pawn (d2)": "rnbqkbnr/pppppppp/8/8/8/8/PPP1PPPP/RNBQKBNR w KQkq - 0 1",
        "Up Knight (g8)": "rnbqkb1r/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Down Knight (g1)": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKB1R w KQkq - 0 1",
        "Up Rook (a8)": "1nbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Down Rook (a1)": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBNR w KQkq - 0 1",
        "Up Bishop (f8)": "rnbqk1nr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Down Bishop (f1)": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK1NR w KQkq - 0 1",
        "Up Queen (d8)": "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Down Queen (d1)": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1",
    }
    
    print(f"{'FEN Name':<20} | {'C++ Raw':<8} | {'Py Raw':<8} | {'Matches':<8}")
    print("-" * 55)
    for name, fen in fens.items():
        board = chess.Board(fen)
        py_val = py_evaluate(board)
        cpp_val = engine.evaluate_nnue_direct(fen)
        matches = "YES" if py_val == cpp_val else "NO"
        print(f"{name:<20} | {cpp_val:<8} | {py_val:<8} | {matches:<8}")

if __name__ == '__main__':
    test()
