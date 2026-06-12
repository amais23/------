import multiprocessing as mp
import time
import json
import os
import sys
import numpy as np
import chess
import pettingzoo.classic.chess.chess_utils as cu
import matplotlib.pyplot as plt

# ═══════════════════════════════════════════
# Process-Isolated Agent Wrapper
# ═══════════════════════════════════════════
def agent_worker_loop(agent_module_name, conn):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    
    try:
        import importlib
        mod = importlib.import_module(agent_module_name)
        agent = mod.Agent()
        conn.send("READY")
        
        while True:
            msg = conn.recv()
            if msg is None:
                break
            obs, mask = msg
            action = agent.act(obs, mask)
            nps = getattr(agent, 'last_nps', 0.0)
            score = getattr(agent, 'last_score', 0)
            conn.send((action, nps, score))
    except Exception as e:
        import traceback
        conn.send(("ERROR", traceback.format_exc()))

class ProcessAgent:
    def __init__(self, agent_module_name):
        self.agent_module_name = agent_module_name
        self.parent_conn, self.child_conn = mp.Pipe()
        self.process = mp.Process(target=agent_worker_loop, args=(self.agent_module_name, self.child_conn))
        self.process.start()
        
        status = self.parent_conn.recv()
        if status != "READY":
            raise RuntimeError(f"Agent {agent_module_name} failed to initialize:\n{status}")
            
        self.last_nps = 0.0
        self.last_score = 0
        
    def act(self, obs, mask):
        self.parent_conn.send((obs, mask))
        res = self.parent_conn.recv()
        if isinstance(res, tuple) and len(res) == 2 and res[0] == "ERROR":
            raise RuntimeError(f"Agent {self.agent_module_name} crashed:\n{res[1]}")
        action, nps, score = res
        self.last_nps = nps
        self.last_score = score
        return action
        
    def terminate(self):
        try:
            self.parent_conn.send(None)
        except Exception:
            pass
        self.process.join(timeout=1.0)
        if self.process.is_alive():
            self.process.terminate()

# ═══════════════════════════════════════════
# Observation & Move Conversion Helpers
# ═══════════════════════════════════════════
def fen_to_obs(board):
    obs = np.zeros((8, 8, 111), dtype=np.int8)
    is_white = (board.turn == chess.WHITE)
    
    if is_white:
        if board.has_kingside_castling_rights(chess.WHITE): obs[0, 0, 0] = 1
        if board.has_queenside_castling_rights(chess.WHITE): obs[0, 0, 1] = 1
        if board.has_kingside_castling_rights(chess.BLACK): obs[0, 0, 2] = 1
        if board.has_queenside_castling_rights(chess.BLACK): obs[0, 0, 3] = 1
    else:
        if board.has_kingside_castling_rights(chess.BLACK): obs[0, 0, 0] = 1
        if board.has_queenside_castling_rights(chess.BLACK): obs[0, 0, 1] = 1
        if board.has_kingside_castling_rights(chess.WHITE): obs[0, 0, 2] = 1
        if board.has_queenside_castling_rights(chess.WHITE): obs[0, 0, 3] = 1
    
    piece_map = {
        chess.PAWN: 0,
        chess.KNIGHT: 1,
        chess.BISHOP: 2,
        chess.ROOK: 3,
        chess.QUEEN: 4,
        chess.KING: 5
    }
    
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece is not None:
            if is_white:
                r = 7 - (sq // 8)
                ch = (7 + piece_map[piece.piece_type]) if piece.color == chess.WHITE else (13 + piece_map[piece.piece_type])
            else:
                r = sq // 8
                ch = (7 + piece_map[piece.piece_type]) if piece.color == chess.BLACK else (13 + piece_map[piece.piece_type])
            c = sq % 8
            obs[r, c, ch] = 1
            
    if board.has_legal_en_passant():
        ep_sq = board.ep_square
        ep_col = ep_sq % 8
        if is_white:
            obs[0, ep_col, 13] = 1
        else:
            obs[7, ep_col, 7] = 1
            
    return obs

def get_action_mask(board):
    is_white = (board.turn == chess.WHITE)
    mask = np.zeros(4672, dtype=np.int8)
    for move in board.legal_moves:
        if is_white:
            rel_move = move
        else:
            rel_move = chess.Move(
                chess.square_mirror(move.from_square),
                chess.square_mirror(move.to_square),
                promotion=move.promotion
            )
        col = rel_move.from_square % 8
        row = rel_move.from_square // 8
        act_idx = (col * 8 + row) * 73 + cu.get_move_plane(rel_move)
        if 0 <= act_idx < 4672:
            mask[act_idx] = 1
    return mask

def action_to_move(board, action):
    is_white = (board.turn == chess.WHITE)
    for move in board.legal_moves:
        if is_white:
            rel_move = move
        else:
            rel_move = chess.Move(
                chess.square_mirror(move.from_square),
                chess.square_mirror(move.to_square),
                promotion=move.promotion
            )
        col = rel_move.from_square % 8
        row = rel_move.from_square // 8
        act_idx = (col * 8 + row) * 73 + cu.get_move_plane(rel_move)
        if act_idx == action:
            return move
    return list(board.legal_moves)[0]

# ═══════════════════════════════════════════
# Play Game Worker
# ═══════════════════════════════════════════
def play_game(white_name, black_name, game_idx, seed):
    agent_modules = {
        "d6_cpp": "d6_cpp.agent",
        "d8": "d8.agent"
    }
    
    white_module = agent_modules[white_name]
    black_module = agent_modules[black_name]
    
    white_agent = None
    black_agent = None
    history = []
    
    try:
        white_agent = ProcessAgent(white_module)
        black_agent = ProcessAgent(black_module)
        
        board = chess.Board()
        rng = np.random.default_rng(seed)
        
        # 4 random opening plies
        for _ in range(4):
            if board.is_game_over():
                break
            moves = list(board.legal_moves)
            if moves:
                move = rng.choice(moves)
                board.push(move)
        
        while not board.is_game_over() and board.fullmove_number * 2 <= 300:
            is_white = board.turn == chess.WHITE
            active_agent = white_agent if is_white else black_agent
            active_name = white_name if is_white else black_name
            
            obs = fen_to_obs(board)
            mask = get_action_mask(board)
            
            start_time = time.time()
            action = active_agent.act(obs, mask)
            elapsed = time.time() - start_time
            
            nps = active_agent.last_nps
            score = active_agent.last_score
            
            move = action_to_move(board, action)
            if move not in board.legal_moves:
                move = list(board.legal_moves)[0]
                
            board.push(move)
            
            history.append({
                "ply": len(board.move_stack),
                "player": "white" if is_white else "black",
                "agent": active_name,
                "move_uci": move.uci(),
                "nps": float(nps),
                "score": int(score),
                "time_elapsed": float(elapsed)
            })
            
        res = board.result()
        return {
            "white_name": white_name,
            "black_name": black_name,
            "game_idx": game_idx,
            "seed": int(seed),
            "result": res,
            "history": history,
            "error": None
        }
    except Exception as e:
        import traceback
        return {
            "white_name": white_name,
            "black_name": black_name,
            "game_idx": game_idx,
            "seed": int(seed),
            "result": "error",
            "history": history,
            "error": traceback.format_exc()
        }
    finally:
        if white_agent:
            white_agent.terminate()
        if black_agent:
            black_agent.terminate()

def play_game_entry(white_name, black_name, game_idx, seed, conn):
    res = play_game(white_name, black_name, game_idx, seed)
    conn.send(res)

# ═══════════════════════════════════════════
# Main Execution & Reporting
# ═══════════════════════════════════════════
if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)
    
    matchups = [
        ("d6_cpp", "d8")
    ]
    
    tasks = []
    game_idx = 0
    import random
    rng = random.Random(42)
    
    for w_name, b_name in matchups:
        for _ in range(10):
            seed = rng.randint(0, 1000000)
            tasks.append((w_name, b_name, game_idx, seed))
            game_idx += 1
        for _ in range(10):
            seed = rng.randint(0, 1000000)
            tasks.append((b_name, w_name, game_idx, seed))
            game_idx += 1
            
    print(f"Total games scheduled: {len(tasks)}")
    print("Starting process pool...")
    
    results = []
    completed = 0
    max_workers = 8
    active_processes = []
    task_queue = list(tasks)
    
    while task_queue or active_processes:
        while len(active_processes) < max_workers and task_queue:
            w_name, b_name, g_idx, seed = task_queue.pop(0)
            parent_conn, child_conn = mp.Pipe()
            p = mp.Process(target=play_game_entry, args=(w_name, b_name, g_idx, seed, child_conn))
            p.start()
            active_processes.append((p, parent_conn, (w_name, b_name, g_idx)))
            
        still_active = []
        for p, conn, info in active_processes:
            if conn.poll():
                try:
                    res = conn.recv()
                    results.append(res)
                    completed += 1
                    
                    w_name = res["white_name"]
                    b_name = res["black_name"]
                    outcome = res["result"]
                    err = res["error"]
                    
                    status_str = f"Game {res['game_idx']+1}/20: {w_name} (White) vs {b_name} (Black) -> Result: {outcome}"
                    if err:
                        status_str += f" (CRASHED)"
                        print(f"Error in Game {res['game_idx']+1}: {err}")
                    print(f"[{completed:02d}/20] {status_str}")
                    sys.stdout.flush()
                except Exception as ex:
                    print(f"Error reading result for Game {info[2]+1}: {ex}")
                p.join()
            elif not p.is_alive():
                p.join()
                completed += 1
                print(f"[{completed:02d}/20] Game {info[2]+1} died unexpectedly.")
            else:
                still_active.append((p, conn, info))
                
        active_processes = still_active
        time.sleep(0.1)

    results_file = "tournament_results_d8.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nRaw results saved to {results_file}")
    
    # Analyze
    stats = {("d6_cpp", "d8"): {"games": 0, "d6_wins": 0, "d8_wins": 0, "draws": 0, "errors": 0}}
    for res in results:
        w = res["white_name"]
        b = res["black_name"]
        outcome = res["result"]
        stats[("d6_cpp", "d8")]["games"] += 1
        if outcome == "1-0":
            if w == "d8": stats[("d6_cpp", "d8")]["d8_wins"] += 1
            else: stats[("d6_cpp", "d8")]["d6_wins"] += 1
        elif outcome == "0-1":
            if w == "d8": stats[("d6_cpp", "d8")]["d6_wins"] += 1
            else: stats[("d6_cpp", "d8")]["d8_wins"] += 1
        elif outcome in ("1/2-1/2", "draw"):
            stats[("d6_cpp", "d8")]["draws"] += 1
        else:
            stats[("d6_cpp", "d8")]["errors"] += 1
            
    print("\n--- Match Statistics ---")
    print(stats[("d6_cpp", "d8")])
    
    # Write report
    report_md = "# D8 vs D6_CPP Tournament Report\n\n"
    report_md += f"Total games: {stats[('d6_cpp', 'd8')]['games']}\n"
    report_md += f"D8 Wins: {stats[('d6_cpp', 'd8')]['d8_wins']}\n"
    report_md += f"D6_CPP Wins: {stats[('d6_cpp', 'd8')]['d6_wins']}\n"
    report_md += f"Draws: {stats[('d6_cpp', 'd8')]['draws']}\n"
    report_md += f"Errors: {stats[('d6_cpp', 'd8')]['errors']}\n"
    
    win_rate = (stats[('d6_cpp', 'd8')]['d8_wins'] + 0.5 * stats[('d6_cpp', 'd8')]['draws']) / stats[('d6_cpp', 'd8')]['games'] * 100
    report_md += f"\n**D8 Win Rate / Score Rate**: {win_rate:.2f}%\n"
    
    report_file = "tournament_report_d8.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"Tournament report saved to {report_file}")
