import sys, os
import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import chess_engine_d8_han
from tests.test_cpp_vs_python import py_evaluate

def test():
    board = chess.Board()
    moves = ["d2d4", "e7e5", "e2e4", "d8f6", "c1g5", "e8e7", "d1g4", "d7d5", "e1d2", "c8g4"]
    for m in moves:
        board.push(chess.Move.from_uci(m))
        
    print(f"Board FEN: {board.fen()}")
    
    engine = chess_engine_d8_han.SearchEngineD8()
    engine.init("")
    
    cpp_val = engine.evaluate_nnue_direct(board.fen())
    py_val = py_evaluate(board)
    
    print(f"C++ Static Eval: {cpp_val}")
    print(f"Py Static Eval:  {py_val}")
    print(f"Matches:         {cpp_val == py_val}")

if __name__ == '__main__':
    test()
