import os
import glob
import chess
import chess.pgn
import chess.engine
import random
import time
import concurrent.futures
import threading
import numpy as np
from tqdm import tqdm

raw_dir = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/research/data/raw"
stockfish_path = "/opt/homebrew/bin/stockfish"

# Thread-local storage for reusing Stockfish engines
thread_local = threading.local()

def get_engine():
    if not hasattr(thread_local, "engine"):
        # We can configure Stockfish with basic parameters if needed
        thread_local.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    return thread_local.engine

def close_thread_engines():
    if hasattr(thread_local, "engine"):
        try:
            thread_local.engine.quit()
            del thread_local.engine
        except:
            pass

def extract_fens(limit_games=500):
    pgn_files = glob.glob(f"{raw_dir}/*.pgn")
    print(f"Found PGN files: {pgn_files}")
    
    all_fens = []
    game_count = 0
    
    for pgn_file in pgn_files:
        if game_count >= limit_games:
            break
        print(f"Reading {pgn_file}...")
        with open(pgn_file, "r", errors="ignore") as f:
            while game_count < limit_games:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                game_count += 1
                
                board = game.board()
                plies = []
                for move in game.mainline_moves():
                    board.push(move)
                    # Filter: mid-game plies 16 to 80, not in check
                    if 16 <= len(board.move_stack) <= 80 and not board.is_check():
                        # We can also check if the position is "quiet" (no captures/checks possible, or just not check)
                        # The original script only filtered out check.
                        plies.append(board.fen())
                
                if len(plies) > 10:
                    sampled = random.sample(plies, 10)
                else:
                    sampled = plies
                all_fens.extend(sampled)
                
    print(f"Parsed {game_count} games. Extracted {len(all_fens)} raw candidate FENs.")
    return list(set(all_fens)) # De-duplicate

def label_fen_worker(fen_info):
    idx, fen = fen_info
    try:
        engine = get_engine()
        board = chess.Board(fen)
        
        # 5ms or depth 10
        result = engine.analyse(board, chess.engine.Limit(time=0.005, depth=10))
        score_obj = result["score"].relative
        
        if score_obj.is_mate():
            mate_plies = score_obj.mate()
            score = 10000 - abs(mate_plies) if mate_plies > 0 else -10000 + abs(mate_plies)
        else:
            score = score_obj.score()
            
        return fen, score
    except Exception as e:
        return fen, None

def test_labeling(fens, max_workers=8):
    print(f"\n--- Testing with max_workers={max_workers} ---")
    start_time = time.time()
    
    # Run labeling
    labeled_data = []
    failed_count = 0
    out_of_bounds_count = 0
    
    fen_infos = list(enumerate(fens))
    
    # We want to clear thread local engine from previous runs
    close_thread_engines()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(executor.map(label_fen_worker, fen_infos), total=len(fens)))
        
        # Shutdown engines
        # Submit task to clean up each thread (conceptually)
        # To be absolutely sure, we run a cleanup task
        futures = [executor.submit(close_thread_engines) for _ in range(max_workers * 2)]
        concurrent.futures.wait(futures)
        
    for fen, score in results:
        if score is None:
            failed_count += 1
        elif not (-2000 <= score <= 2000):
            out_of_bounds_count += 1
            labeled_data.append((fen, score)) # still keep for stats
        else:
            labeled_data.append((fen, score))
            
    elapsed = time.time() - start_time
    pps = len(fens) / elapsed
    print(f"Elapsed: {elapsed:.2f} seconds")
    print(f"Speed: {pps:.2f} positions/second (PPS)")
    print(f"Failed: {failed_count}, Out of bounds (>2000 or <-2000): {out_of_bounds_count}")
    
    return labeled_data, pps, elapsed

def main():
    print("Step 1: Extracting FENs from raw PGN files...")
    # Limit to 300 games to be quick
    raw_fens = extract_fens(limit_games=300)
    
    # Sample 1000 FENs for the test
    test_size = 1000
    if len(raw_fens) < test_size:
        print(f"Warning: Only found {len(raw_fens)} FENs, using all of them.")
        test_fens = raw_fens
    else:
        random.shuffle(raw_fens)
        test_fens = raw_fens[:test_size]
        
    print(f"Selected {len(test_fens)} FENs for small-scale testing.")
    
    # Let's run a small test of 100 first to warm up and test with 4 workers
    warmup_size = min(100, len(test_fens))
    print(f"Warming up with {warmup_size} positions (4 workers)...")
    test_labeling(test_fens[:warmup_size], max_workers=4)
    
    # Now run the main test of 1000 positions with 8 workers
    print(f"\nRunning main test with {len(test_fens)} positions (8 workers)...")
    labeled_data, pps_8, elapsed_8 = test_labeling(test_fens, max_workers=8)
    
    # Also run with 12 workers to see if it scales better on M4 (M4 has 10 cores, usually 4 performance + 6 efficiency or 6 performance + 4 efficiency depending on the model, or M4 Pro/Max has more)
    # Let's test 12 workers on a subset of 300 positions to compare scaling
    test_subset = test_fens[:300]
    print(f"\nRunning comparison test with 300 positions (12 workers)...")
    _, pps_12, _ = test_labeling(test_subset, max_workers=12)
    
    print(f"\nRunning comparison test with 300 positions (16 workers)...")
    _, pps_16, _ = test_labeling(test_subset, max_workers=16)
    
    # Analyze quality of labeled data from the 8-worker run
    valid_scores = [score for _, score in labeled_data if score is not None and -2000 <= score <= 2000]
    total_valid = len(valid_scores)
    
    print("\n=== Quality Analysis (Main Test 8 Workers) ===")
    print(f"Total processed: {len(test_fens)}")
    print(f"Valid positions (-2000 <= score <= 2000): {total_valid} ({total_valid/len(test_fens)*100:.2f}%)")
    
    if total_valid > 0:
        scores_arr = np.array(valid_scores)
        mean_val = np.mean(scores_arr)
        std_val = np.std(scores_arr)
        min_val = np.min(scores_arr)
        max_val = np.max(scores_arr)
        p25 = np.percentile(scores_arr, 25)
        p50 = np.percentile(scores_arr, 50)
        p75 = np.percentile(scores_arr, 75)
        
        print(f"Mean Score: {mean_val:.2f}")
        print(f"Std Dev: {std_val:.2f}")
        print(f"Min Score: {min_val}")
        print(f"Max Score: {max_val}")
        print(f"25th Percentile: {p25}")
        print(f"Median (50th): {p50}")
        print(f"75th Percentile: {p75}")
        
        # Quiet positions: let's analyze if the positions are truly quiet.
        # Quiet check in C++ / chess engine is usually that there's no check, and no simple tactical capture.
        # But here we just filtered out board.is_check().
        # Let's count how many positions have captures available as a proxy for tactical complexity.
        captures_count = 0
        for fen, score in labeled_data[:200]: # check a subset
            if score is None: continue
            board = chess.Board(fen)
            has_capture = any(board.is_capture(move) for move in board.legal_moves)
            if has_capture:
                captures_count += 1
        print(f"Proxy for 'Quietness' (Checked 200 positions):")
        print(f"  Positions with captures available: {captures_count} ({captures_count/200*100:.1f}%)")
        print(f"  Positions without captures available (Quiet): {200-captures_count} ({(200-captures_count)/200*100:.1f}%)")
        
    print("\n=== Time & Cost Estimation ===")
    target_sizes = [100000, 500000, 1000000, 2500000, 5000000]
    best_pps = max(pps_8, pps_12, pps_16)
    best_workers = 8 if best_pps == pps_8 else (12 if best_pps == pps_12 else 16)
    print(f"Using best measured speed: {best_pps:.2f} PPS (with {best_workers} workers)")
    
    for size in target_sizes:
        seconds = size / best_pps
        hours = seconds / 3600
        print(f"  For {size/1e6:.1f}M positions: {hours:.2f} hours ({seconds:.0f} seconds)")

if __name__ == "__main__":
    main()
