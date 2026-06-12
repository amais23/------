import sys
import os
import chess
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import chess_engine_d8_han

def generate_random_game(move_count=60):
    board = chess.Board()
    moves_uci = []
    for _ in range(move_count):
        if board.is_game_over():
            break
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            break
        
        # Prioritize captures/promotions sometimes to test those code paths
        captures = [m for m in legal_moves if board.is_capture(m)]
        promotions = [m for m in legal_moves if m.promotion is not None]
        
        if promotions and random.random() < 0.5:
            move = random.choice(promotions)
        elif captures and random.random() < 0.3:
            move = random.choice(captures)
        else:
            move = random.choice(legal_moves)
            
        moves_uci.append(move.uci())
        board.push(move)
    return moves_uci

def test():
    engine = chess_engine_d8_han.SearchEngineD8()
    engine.init("")
    
    print("Generating and testing 5 random games...")
    for game_idx in range(5):
        moves = generate_random_game(100)
        print(f"Game {game_idx + 1}: Testing sequence of {len(moves)} moves...")
        success = engine.test_incremental_vs_recompute_moves(moves)
        assert success, f"❌ Mismatch detected in game {game_idx + 1}!"
        print(f"✅ Game {game_idx + 1} passed successfully!")
        
    print("🎉 All incremental vs recompute verification tests passed successfully!")

if __name__ == '__main__':
    test()
