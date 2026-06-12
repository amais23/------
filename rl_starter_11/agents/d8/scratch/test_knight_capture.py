import chess
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import chess_engine_d8_han

def test():
    # Set up a position where White can capture Black's Knight on e4 for free with a Pawn d3xe4.
    # FEN: White pawn on d3, Black Knight on e4.
    # rnbqkb1r/pppp1ppp/8/8/4n3/3P4/PPP2PPP/RNBQKBNR w KQkq - 0 1
    # White has two main options: d3xe4 (capturing the Knight, winning material) or some random move.
    board = chess.Board("rnbqkb1r/pppp1ppp/8/8/4n3/3P4/PPP2PPP/RNBQKBNR w KQkq - 0 1")
    
    engine = chess_engine_d8_han.SearchEngineD8()
    engine.init("")
    
    # We print the raw evaluation of the position
    raw_eval = engine.evaluate_nnue_direct(board.fen())
    print(f"Raw NNUE eval of position: {raw_eval} (centered: {raw_eval - 5111})")
    
    # What if we capture the knight?
    board_captured = board.copy()
    board_captured.push_uci("d3e4")
    raw_eval_captured = engine.evaluate_nnue_direct(board_captured.fen())
    print(f"Raw NNUE eval after d3xe4 (capturing Knight): {raw_eval_captured} (centered: {raw_eval_captured - 5111})")
    
    # What if we do a random move like a2a3?
    board_random = board.copy()
    board_random.push_uci("a2a3")
    raw_eval_random = engine.evaluate_nnue_direct(board_random.fen())
    print(f"Raw NNUE eval after a2a3 (random): {raw_eval_random} (centered: {raw_eval_random - 5111})")
    
    # Let's run a search and see what move it chooses!
    # We call search by using Python's agent or directly?
    # In agent.py, search is called by engine.search(board_fen, time_limit, depth_limit, ...)
    # Let's check agent.py's implementation of search.
    
if __name__ == '__main__':
    test()
