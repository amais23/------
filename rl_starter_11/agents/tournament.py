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
    # 確保 agents 的父目錄在 sys.path 中
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
        
        # 等待 READY
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
    """將 chess.Board 轉換為符合 C++ 重建規格 of (8,8,111) 觀測值"""
    obs = np.zeros((8, 8, 111), dtype=np.int8)
    is_white = (board.turn == chess.WHITE)
    
    # 1. 易位權 (channels 0..3)
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
    
    # 2. 棋子擺放 (channels 7..12 當前玩家, 13..18 對手)
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
            
    # 3. 吃過路兵權利 (channels 7 白兵第4橫列, 13 黑兵第5橫列)
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
        "d4_pro": "d4_pro.agent",
        "d6_cpp": "d6_cpp.agent",
        "d7_rl": "d7_rl.agent"
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
        
        # 前 4 步隨機移動以增加對局多樣性
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
            
        res = board.result() # "1-0", "0-1", "1/2-1/2"
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
        ("d4_pro", "d6_cpp"),
        ("d4_pro", "d7_rl"),
        ("d6_cpp", "d7_rl")
    ]
    
    tasks = []
    game_idx = 0
    import random
    rng = random.Random(1337)
    
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
    print("Starting process pool with 10 cores...")
    
    results = []
    completed = 0
    max_workers = 10
    active_processes = []
    task_queue = list(tasks)
    
    while task_queue or active_processes:
        # 1. 補滿行程
        while len(active_processes) < max_workers and task_queue:
            w_name, b_name, g_idx, seed = task_queue.pop(0)
            parent_conn, child_conn = mp.Pipe()
            p = mp.Process(target=play_game_entry, args=(w_name, b_name, g_idx, seed, child_conn))
            p.start()
            active_processes.append((p, parent_conn, (w_name, b_name, g_idx)))
            
        # 2. 輪詢檢查狀態
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
                    
                    status_str = f"Game {res['game_idx']+1}/60: {w_name} (White) vs {b_name} (Black) -> Result: {outcome}"
                    if err:
                        status_str += f" (CRASHED)"
                        print(f"Error in Game {res['game_idx']+1}: {err}")
                    print(f"[{completed:02d}/60] {status_str}")
                    sys.stdout.flush()
                except Exception as ex:
                    print(f"Error reading result for Game {info[2]+1}: {ex}")
                p.join()
            elif not p.is_alive():
                p.join()
                completed += 1
                print(f"[{completed:02d}/60] Game {info[2]+1} died unexpectedly.")
            else:
                still_active.append((p, conn, info))
                
        active_processes = still_active
        time.sleep(0.1)

            
    # 儲存 JSON 原始資料
    results_file = "tournament_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nRaw results saved to {results_file}")
    
    # ═══════════════════════════════════════════
    # Data Analysis
    # ═══════════════════════════════════════════
    # 統計勝率
    stats = {}
    for matchup in matchups:
        stats[matchup] = {"games": 0, "w_wins": 0, "b_wins": 0, "draws": 0, "errors": 0}
        
    for res in results:
        w = res["white_name"]
        b = res["black_name"]
        m_key = (w, b) if (w, b) in stats else ((b, w) if (b, w) in stats else None)
        if m_key is None:
            continue
            
        stats[m_key]["games"] += 1
        outcome = res["result"]
        if outcome == "1-0":
            if w == m_key[0]:
                stats[m_key]["w_wins"] += 1
            else:
                stats[m_key]["b_wins"] += 1
        elif outcome == "0-1":
            if w == m_key[0]:
                stats[m_key]["b_wins"] += 1
            else:
                stats[m_key]["w_wins"] += 1
        elif outcome in ("1/2-1/2", "draw"):
            stats[m_key]["draws"] += 1
        else:
            stats[m_key]["errors"] += 1
            
    # 輸出勝率表格 (Markdown)
    report_md = "# 西洋棋 Agent 對戰大賽統計報告\n\n"
    report_md += "本對戰使用 10 核心平行運算，對戰雙方各擔任 10 場白棋與 10 場黑棋，共 20 場對局。\n\n"
    report_md += "## 對戰勝率統計\n\n"
    report_md += "| 對戰組合 (Agent A vs Agent B) | Agent A 做白勝率 | Agent A 做黑勝率 | 總勝率 (A / B / 和) | Agent A 勝分率 |\n"
    report_md += "| :--- | :---: | :---: | :---: | :---: |\n"
    
    for (a, b), data in stats.items():
        # 尋找 a 為白、b 為黑的場次結果
        w_matches = [r for r in results if r["white_name"] == a and r["black_name"] == b]
        b_matches = [r for r in results if r["white_name"] == b and r["black_name"] == a]
        
        a_win_w = sum(1 for r in w_matches if r["result"] == "1-0")
        b_win_w = sum(1 for r in w_matches if r["result"] == "0-1")
        draw_w = sum(1 for r in w_matches if r["result"] in ("1/2-1/2", "draw"))
        
        b_win_b = sum(1 for r in b_matches if r["result"] == "1-0")
        a_win_b = sum(1 for r in b_matches if r["result"] == "0-1")
        draw_b = sum(1 for r in b_matches if r["result"] in ("1/2-1/2", "draw"))
        
        total_a_wins = a_win_w + a_win_b
        total_b_wins = b_win_w + b_win_b
        total_draws = draw_w + draw_b
        total_games = len(w_matches) + len(b_matches)
        
        win_rate_as_white = (a_win_w + 0.5 * draw_w) / max(len(w_matches), 1) * 100
        win_rate_as_black = (a_win_b + 0.5 * draw_b) / max(len(b_matches), 1) * 100
        total_score_rate = (total_a_wins + 0.5 * total_draws) / max(total_games, 1) * 100
        
        report_md += f"| **{a}** vs **{b}** | {win_rate_as_white:.1f}% | {win_rate_as_black:.1f}% | {total_a_wins}勝 / {total_b_wins}敗 / {total_draws}和 | {total_score_rate:.1f}% |\n"
        
    print("\n--- Match Statistics ---")
    for k, v in stats.items():
        print(f"{k[0]} vs {k[1]}: {v}")
        
    # NPS 統計
    nps_data = {"d4_pro": [], "d6_cpp": [], "d7_rl": []}
    for res in results:
        for step in res["history"]:
            ag = step["agent"]
            nps = step["nps"]
            # 書與殘局庫的 NPS=0.0，不計入搜尋 NPS 統計中，以避免低估實際搜尋效能
            if nps > 0:
                nps_data[ag].append(nps)
                
    # 繪製 NPS Boxplot
    plt.figure(figsize=(8, 6))
    agents_list = ["d4_pro", "d6_cpp", "d7_rl"]
    plot_data = [nps_data[ag] for ag in agents_list]
    
    # 避免無數據畫圖報錯
    plot_data = [d if len(d) > 0 else [0.0] for d in plot_data]
    
    plt.boxplot(plot_data, tick_labels=agents_list)
    plt.title("NPS (Nodes Per Second) Comparison (Search Moves Only)")
    plt.ylabel("NPS")
    plt.yscale("log") # 通常 NPS 差好幾個數量級，用對數軸更清楚
    plt.grid(True, which="both", ls="--", alpha=0.5)
    
    nps_fig_path = "nps_comparison.png"
    plt.savefig(nps_fig_path, dpi=150)
    plt.close()
    print(f"Saved NPS comparison plot to {nps_fig_path}")
    
    # 繪製分數變化趨勢 (Evaluation Score Trend)
    # 我們找一場手數最多且無出錯的 d6_cpp (White) vs d7_rl (Black) 對局來繪圖
    target_match = None
    max_ply = 0
    for res in results:
        if res["result"] != "error" and len(res["history"]) > max_ply:
            if (res["white_name"] == "d6_cpp" and res["black_name"] == "d7_rl") or \
               (res["white_name"] == "d7_rl" and res["black_name"] == "d6_cpp"):
                max_ply = len(res["history"])
                target_match = res
                
    if target_match:
        w_name = target_match["white_name"]
        b_name = target_match["black_name"]
        g_id = target_match["game_idx"]
        
        ply_axis = []
        w_scores = []
        b_scores = []
        
        for step in target_match["history"]:
            ply = step["ply"]
            player = step["player"]
            score = step["score"]
            # 表格/圖書有時回傳 30000 或是大數，做個限制
            if abs(score) > 15000:
                score = 15000 if score > 0 else -15000
                
            ply_axis.append(ply)
            if player == "white":
                # 白棋的 evaluation
                w_scores.append((ply, score))
            else:
                # 黑棋的 evaluation
                b_scores.append((ply, score))
                
        # 繪圖
        plt.figure(figsize=(10, 6))
        if w_scores:
            p_w, s_w = zip(*w_scores)
            plt.plot(p_w, s_w, marker='o', label=f"White ({w_name}) Eval", color="blue")
        if b_scores:
            p_b, s_b = zip(*b_scores)
            # 因為黑棋的分數在引擎中可能是相對於黑棋，或者是相對於白棋。
            # 大部分的極小化極大搜尋回傳的值都是當前輪到玩家的相對值，
            # 這裡為了對齊，我們直接顯示引擎輸出的原始值。
            plt.plot(p_b, s_b, marker='x', label=f"Black ({b_name}) Eval", color="red")
            
        plt.title(f"Evaluation Score Trend in Game {g_id+1} ({w_name} vs {b_name})")
        plt.xlabel("Ply (Half-Moves)")
        plt.ylabel("Engine Score")
        plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
        plt.grid(True, ls="--", alpha=0.5)
        plt.legend()
        
        eval_fig_path = "eval_score_trend.png"
        plt.savefig(eval_fig_path, dpi=150)
        plt.close()
        print(f"Saved Evaluation Score Trend plot to {eval_fig_path}")
    else:
        eval_fig_path = None
        
    # 寫入報告
    report_md += "\n## 搜尋效能對比 (NPS)\n\n"
    report_md += "下圖展示了三種 Agent 搜尋節點速度的對比（對數座標軸，已排除開局庫與殘局庫直接回傳 0 NPS 的著手）：\n\n"
    report_md += f"![NPS Comparison]({nps_fig_path})\n\n"
    
    report_md += "| Agent | 平均 NPS | 最大 NPS | 走子數 |\n"
    report_md += "| :--- | :---: | :---: | :---: |\n"
    for ag in agents_list:
        data = nps_data[ag]
        if data:
            report_md += f"| {ag} | {np.mean(data):.1f} | {np.max(data):.1f} | {len(data)} |\n"
        else:
            report_md += f"| {ag} | N/A | N/A | 0 |\n"
            
    if eval_fig_path:
        report_md += "\n## 評估函數分數變化趨勢\n\n"
        report_md += f"我們選擇了第 {target_match['game_idx']+1} 局 ({target_match['white_name']} vs {target_match['black_name']}，共 {len(target_match['history'])} 步) 來觀察對局中各自評估分數的變化：\n\n"
        report_md += f"![Eval Score Trend]({eval_fig_path})\n\n"
        report_md += "> **註**：C++ 引擎與 Python Alpha-Beta 引擎的分數大多為輪到該方時的相對估值。30000 代表 Tablebase 殘局庫宣告的勝利。\n"
        
    report_file = "tournament_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"Tournament report saved to {report_file}")
