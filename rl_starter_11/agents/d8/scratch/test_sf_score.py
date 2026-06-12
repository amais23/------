import chess
import chess.engine

stockfish_path = "/opt/homebrew/bin/stockfish"

def test():
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    
    # Starting position (White to move)
    board = chess.Board()
    result = engine.analyse(board, chess.engine.Limit(time=0.01))
    score_obj = result["score"]
    print("Start position (White to move):")
    print("  score_obj:", score_obj)
    print("  score_obj.relative.score():", score_obj.relative.score())
    print("  score_obj.white().score():", score_obj.white().score())
    
    # Same position but Black to move (we can't easily do it for start, but let's do K+R vs K)
    # White up a Rook, White to move
    board = chess.Board("k7/8/8/8/8/8/8/K1R5 w - - 0 1")
    result = engine.analyse(board, chess.engine.Limit(time=0.01))
    score_obj = result["score"]
    print("\nWhite up a Rook (White to move):")
    print("  score_obj:", score_obj)
    print("  score_obj.relative.score():", score_obj.relative.score())
    print("  score_obj.white().score():", score_obj.white().score())
    
    # White up a Rook, Black to move
    board = chess.Board("k7/8/8/8/8/8/8/K1R5 b - - 0 1")
    result = engine.analyse(board, chess.engine.Limit(time=0.01))
    score_obj = result["score"]
    print("\nWhite up a Rook (Black to move):")
    print("  score_obj:", score_obj)
    print("  score_obj.relative.score():", score_obj.relative.score())
    print("  score_obj.white().score():", score_obj.white().score())
    
    engine.quit()

if __name__ == '__main__':
    test()
