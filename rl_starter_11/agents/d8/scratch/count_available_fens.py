import os
import glob
import chess
import chess.pgn

raw_dir = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/research/data/raw"

def count_all_available_fens():
    pgn_files = glob.glob(f"{raw_dir}/*.pgn")
    print(f"Found PGN files: {pgn_files}")
    
    all_fens = set()
    game_count = 0
    total_plies_scanned = 0
    
    for pgn_file in pgn_files:
        print(f"Scanning {pgn_file}...")
        with open(pgn_file, "r", errors="ignore") as f:
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                game_count += 1
                
                board = game.board()
                for move in game.mainline_moves():
                    total_plies_scanned += 1
                    is_capture = board.is_capture(move)
                    is_promotion = move.promotion is not None
                    
                    board.push(move)
                    
                    if (16 <= len(board.move_stack) <= 80 
                        and not board.is_check() 
                        and not is_capture 
                        and not is_promotion):
                        all_fens.add(board.fen())
                
                if game_count % 2000 == 0:
                    print(f"  Processed {game_count} games, current unique FENs: {len(all_fens)}")
                    
    print(f"\n--- Total Scan Results ---")
    print(f"Total games processed: {game_count}")
    print(f"Total plies scanned: {total_plies_scanned}")
    print(f"Total unique quiet FENs: {len(all_fens)}")
    
if __name__ == "__main__":
    count_all_available_fens()
