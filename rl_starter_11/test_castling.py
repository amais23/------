import sys
sys.path.append("/Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp")
import chess_engine

print("Move action for e8g8 (black FEN):")
print(chess_engine.test_move_to_action("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1", "e8g8"))
