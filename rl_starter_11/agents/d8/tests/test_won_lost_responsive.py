import sys, os
import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import chess_engine_d8_han

def test():
    engine = chess_engine_d8_han.SearchEngineD8()
    engine.init("")
    
    # 1. Starting position FEN
    start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    start_score = engine.evaluate_nnue_direct(start_fen)
    print(f"Starting FEN: {start_fen}")
    print(f"Score: {start_score} ({start_score / 96.0:.2f} cp)")
    
    # 2. Won position FEN (White up a Queen - Black is missing Queen at d8)
    won_fen = "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    won_score = engine.evaluate_nnue_direct(won_fen)
    print(f"Won FEN: {won_fen}")
    print(f"Score: {won_score} ({won_score / 96.0:.2f} cp)")
    
    # 3. Lost position FEN (White down a Queen - White is missing Queen at d1)
    lost_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1"
    lost_score = engine.evaluate_nnue_direct(lost_fen)
    print(f"Lost FEN: {lost_fen}")
    print(f"Score: {lost_score} ({lost_score / 96.0:.2f} cp)")
    
    # Assertions to verify responsiveness
    assert won_score > start_score, f"Won score ({won_score}) should be greater than start score ({start_score})"
    assert lost_score < start_score, f"Lost score ({lost_score}) should be less than start score ({start_score})"
    assert won_score - start_score > 150, f"Won score difference ({won_score - start_score}) should be > 150"
    assert start_score - lost_score > 200, f"Lost score difference ({start_score - lost_score}) should be > 200"
    
    print("✅ Responsiveness verification successful! Evaluation varies significantly with material changes.")

if __name__ == '__main__':
    test()
