import os
import glob
import chess
import chess.pgn
import chess.engine
import random
import concurrent.futures
import threading
from tqdm import tqdm

raw_dir = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/research/data/raw"
processed_dir = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/research/data/processed"
os.makedirs(processed_dir, exist_ok=True)

output_file = os.path.join(processed_dir, "dataset.txt")
stockfish_path = "/opt/homebrew/bin/stockfish"

# Thread-local storage for reusing Stockfish engines
thread_local = threading.local()

def get_engine():
    if not hasattr(thread_local, "engine"):
        thread_local.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    return thread_local.engine

# 1. Extract FENs from PGN files
def extract_fens():
    pgn_files = glob.glob(f"{raw_dir}/*.pgn")
    print(f"Found PGN files: {pgn_files}")
    
    all_fens = []
    game_count = 0
    
    for pgn_file in pgn_files:
        with open(pgn_file, "r", errors="ignore") as f:
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                game_count += 1
                
                # Walk through the game and sample positions
                board = game.board()
                plies = []
                for move in game.mainline_moves():
                    board.push(move)
                    # Sample only mid-game positions (plies 16 to 80)
                    # and filter out positions where the side to move is in check
                    if 16 <= len(board.move_stack) <= 80 and not board.is_check():
                        plies.append(board.fen())
                
                # Randomly sample at most 10 positions per game
                if len(plies) > 10:
                    sampled = random.sample(plies, 10)
                else:
                    sampled = plies
                all_fens.extend(sampled)
                
    print(f"Parsed {game_count} games. Extracted {len(all_fens)} raw candidate FENs.")
    return list(set(all_fens)) # De-duplicate

# 2. Label a single FEN using the thread-local Stockfish
def label_fen_worker(fen):
    try:
        engine = get_engine()
        board = chess.Board(fen)
        
        # Search for 5ms or depth 10 to keep it very fast but accurate
        result = engine.analyse(board, chess.engine.Limit(time=0.005, depth=10))
        score_obj = result["score"].relative
        
        # Get score from the side to move's perspective
        if score_obj.is_mate():
            mate_plies = score_obj.mate()
            score = 10000 - abs(mate_plies) if mate_plies > 0 else -10000 + abs(mate_plies)
        else:
            score = score_obj.score()
            
        if score is not None:
            # Filter extreme scores
            if -2000 <= score <= 2000:
                return f"{fen},{score}\n"
    except Exception as e:
        pass
    return None

def close_thread_engines():
    if hasattr(thread_local, "engine"):
        try:
            thread_local.engine.quit()
        except:
            pass

def main():
    fens = extract_fens()
    
    # Target about 120,000 positions
    random.shuffle(fens)
    fens = fens[:120000]
    print(f"Selected {len(fens)} FENs for Stockfish labeling.")
    
    # Use ThreadPoolExecutor to run multiple Stockfish instances in parallel
    max_workers = 8 # M4 has 8+ cores
    print(f"Starting parallel labeling with {max_workers} workers...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Wrap with tqdm to show progress bar
        list_results = list(tqdm(executor.map(label_fen_worker, fens), total=len(fens)))
        
        # Clean up engines
        executor.submit(close_thread_engines)
        
    labeled_count = 0
    with open(output_file, "w") as out:
        for r in list_results:
            if r is not None:
                out.write(r)
                labeled_count += 1
                
    print(f"Successfully labeled and saved {labeled_count} positions to {output_file}.")

if __name__ == '__main__':
    main()
