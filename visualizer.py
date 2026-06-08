#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Arena Chess Visualizer Dashboard
An independent program to visualize ELO ratings, search matches, and explore branching game trees.
Runs a local server on port 8082 and opens the browser automatically.
"""
import http.server
import socketserver
import json
import urllib.request
import urllib.parse
import csv
import os
import sys
import webbrowser
from collections import defaultdict

PORT = 8082
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Load credentials to talk to the ML Arena API
def load_credentials():
    paths = [
        "homework_account.json",
        "rl_starter_11/homework_account.json",
        "../rl_starter_11/homework_account.json",
        "/Users/Shared/西洋棋代理人/rl_starter_11/homework_account.json"
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    api_key = data.get("api_key")
                    account = data.get("account")
                    if api_key:
                        print(f"Loaded credentials from '{p}' (Account: {account})")
                        return api_key, account
            except Exception as e:
                print(f"Error loading credentials from {p}: {e}")
    # Default fallback
    return "a738064d-5d7a-492d-86f6-d2dff6568e22", "41241213S"

# Load local CSV battle logs
def load_csv_history():
    records = []
    paths = [
        "/Users/Shared/西洋棋代理人/matchmaker_rl_11/match_history.csv",
        "/Users/Shared/西洋棋代理人/match_history.csv"
    ]
    seen_ids = set()
    for p in paths:
        if not os.path.exists(p):
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    continue
                header_map = {col.strip().lower(): idx for idx, col in enumerate(header)}
                for row in reader:
                    if not row or len(row) < 3:
                        continue
                    try:
                        battle_id_idx = header_map.get("battle_id", 1)
                        battle_id = int(row[battle_id_idx])
                        if battle_id in seen_ids:
                            continue
                        seen_ids.add(battle_id)
                        
                        timestamp = row[header_map.get("timestamp", 0)].strip('"')
                        opponent = row[header_map.get("opponent", 2)].strip('"')
                        opponent_elo = float(row[header_map.get("opponent_elo", 3)])
                        result = row[header_map.get("result", 4)].strip('"')
                        elo_before = float(row[header_map.get("elo_before", 5)])
                        elo_after = float(row[header_map.get("elo_after", 6)])
                        
                        elo_change_str = row[header_map.get("elo_change", 7)].strip()
                        if elo_change_str.startswith("+"):
                            elo_change = float(elo_change_str[1:])
                        else:
                            elo_change = float(elo_change_str)
                            
                        records.append({
                            "battle_id": battle_id,
                            "timestamp": timestamp,
                            "opponent": opponent,
                            "opponent_elo": opponent_elo,
                            "result": result,
                            "elo_before": elo_before,
                            "elo_after": elo_after,
                            "elo_change": elo_change,
                            "source": "local"
                        })
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error parsing CSV {p}: {e}")
    return records

# Helper to query the ML Arena API
def api_request(endpoint, api_key):
    url = f"https://api-mlarena.spkuan.cc/api{endpoint}"
    req = urllib.request.Request(url)
    req.add_header("X-API-Key", api_key)
    req.add_header("User-Agent", USER_AGENT)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"API request failed on {endpoint}: {e}")
        return None

# Translate pettingzoo action integer to a chess.Move
def action_to_move(board, action, cu):
    import chess
    for move in board.legal_moves:
        if board.turn == chess.BLACK:
            rel_move = chess.Move(
                from_square=move.from_square ^ 56,
                to_square=move.to_square ^ 56,
                promotion=move.promotion
            )
        else:
            rel_move = move
            
        col = rel_move.from_square % 8
        row = rel_move.from_square // 8
        act = (col * 8 + row) * 73 + cu.get_move_plane(rel_move)
        if act == action:
            return move
    return None

# Build horizontal game tree representation
def build_game_tree(decoded_games):
    root = {
        "id": "root",
        "name": "Start",
        "move_num": 0,
        "uci": "",
        "san": "Start",
        "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1",
        "games": list(range(len(decoded_games))),
        "children": {}
    }
    
    for game in decoded_games:
        game_idx = game["game_idx"]
        moves = game["moves"]
        
        current_node = root
        for i, move in enumerate(moves):
            move_san = move["san"]
            move_uci = move["uci"]
            move_num = move["num"]
            color = move["color"]
            fen = move["fen"]
            
            prefix = f"{move_num}. " if color == "w" else f"{move_num}... "
            node_name = prefix + move_san
            
            key = (node_name, move_uci)
            if key not in current_node["children"]:
                current_node["children"][key] = {
                    "id": f"{current_node['id']}_{i}_{move_uci}",
                    "name": node_name,
                    "move_num": move_num,
                    "uci": move_uci,
                    "san": move_san,
                    "fen": fen,
                    "games": [],
                    "children": {}
                }
            
            current_node = current_node["children"][key]
            if game_idx not in current_node["games"]:
                current_node["games"].append(game_idx)
                
    def dict_to_list(node):
        children_list = []
        for child in node["children"].values():
            dict_to_list(child)
            children_list.append(child)
        # Sort children alphabetically to keep ordering stable
        children_list.sort(key=lambda x: x["name"])
        node["children"] = children_list
        node["games_count"] = len(node["games"])
        
    dict_to_list(root)
    return root

# Main HTTP handler
class VisualizerHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Mute logging to keep stdout clean
        pass

    def send_json(self, status, obj):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

    def send_error_json(self, status, msg):
        self.send_json(status, {"error": msg})

    def do_GET(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path
        query = url_parsed.query

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
            return

        api_key, account = load_credentials()

        if path == "/api/leaderboard":
            data = api_request("/rl/competitions/11/leaderboard", api_key)
            if data is not None:
                self.send_json(200, data)
            else:
                self.send_error_json(500, "Failed to retrieve leaderboard from ML Arena API.")
            return

        elif path == "/api/history":
            local_history = load_csv_history()
            api_history_raw = api_request("/rl/competitions/11/battles?page=1&limit=80", api_key)
            
            # Convert API format into our records format
            api_history = []
            if isinstance(api_history_raw, list):
                battles_items = api_history_raw
            elif isinstance(api_history_raw, dict) and "items" in api_history_raw:
                battles_items = api_history_raw["items"]
            else:
                battles_items = []

            for b in battles_items:
                try:
                    bid = b.get("id")
                    created_at = b.get("created_at")
                    # Format timestamp
                    ts = created_at.replace("Z", "").replace("T", " ")
                    if "." in ts:
                        ts = ts.split(".")[0]
                    
                    status = b.get("status")
                    participants = b.get("participants", [])
                    me = None
                    opponent = None
                    for p in participants:
                        # Find our user slot
                        if p.get("username") == account or p.get("user_id") == account:
                            me = p
                        else:
                            opponent = p
                    
                    # If me is not found, fallback based on slot ID or index if needed, 
                    # but typically our account matches username or user_id. Let's fallback to player 0/1.
                    if not me and len(participants) >= 2:
                        # Assume we are one of them
                        me = participants[0]
                        opponent = participants[1]

                    opp_name = opponent.get("username") if opponent else "Unknown"
                    opp_elo = opponent.get("elo_before", 1000.0) if opponent else 1000.0
                    if me:
                        elo_change = me.get("elo_delta") or 0.0
                        elo_after = me.get("elo_after") or 1000.0
                        elo_before = elo_after - elo_change
                        
                        rank = me.get("final_rank")
                        opp_rank = opponent.get("final_rank") if opponent else None
                        
                        if status == "failed":
                            result = "FAIL"
                        elif elo_change > 0:
                            result = "WIN"
                        elif elo_change < 0:
                            result = "LOSS"
                        elif rank == 2:
                            result = "LOSS"
                        elif rank is not None and opp_rank is not None and rank > opp_rank:
                            result = "LOSS"
                        elif rank == 1 and opp_rank == 2:
                            result = "WIN"
                        else:
                            result = "DRAW"
                    else:
                        elo_change = 0.0
                        elo_after = 1000.0
                        elo_before = 1000.0
                        result = "UNKNOWN"

                    api_history.append({
                        "battle_id": bid,
                        "timestamp": ts,
                        "opponent": opp_name,
                        "opponent_elo": opp_elo,
                        "result": result,
                        "elo_before": elo_before,
                        "elo_after": elo_after,
                        "elo_change": elo_change,
                        "source": "api"
                    })
                except Exception as ex:
                    print("Error parsing API battle item:", ex)

            # Merge and sort
            merged = {}
            for r in local_history:
                merged[r["battle_id"]] = r
            # API records enrich or overwrite local records
            for r in api_history:
                bid = r["battle_id"]
                if bid in merged:
                    # Enrich with API score details if local was flagged
                    merged[bid].update(r)
                    merged[bid]["source"] = "merged"
                else:
                    merged[bid] = r

            sorted_list = sorted(merged.values(), key=lambda x: x["battle_id"], reverse=True)
            self.send_json(200, sorted_list)
            return

        elif path == "/api/replay":
            params = urllib.parse.parse_qs(query)
            battle_id_list = params.get("battle_id")
            if not battle_id_list:
                self.send_error_json(400, "Missing 'battle_id' parameter.")
                return
            battle_id = battle_id_list[0]

            # Fetch replay from API
            replay_raw = api_request(f"/rl/battles/{battle_id}/replay", api_key)
            if not replay_raw or "steps" not in replay_raw:
                self.send_error_json(500, f"Failed to retrieve replay for Battle #{battle_id} from ML Arena API.")
                return

            steps = replay_raw.get("steps", [])
            games_count = replay_raw.get("games", 0)
            wins = replay_raw.get("wins", [0, 0])
            draws = replay_raw.get("draws", 0)

            # Import chess libraries
            try:
                import chess
                import pettingzoo.classic.chess.chess_utils as cu
            except ImportError as e:
                self.send_error_json(500, f"Local Python environment is missing chess/pettingzoo: {e}")
                return

            # Group steps by game
            game_steps = defaultdict(list)
            for s in steps:
                if isinstance(s, dict) and "game" in s:
                    game_steps[s["game"]].append(s)

            decoded_games = []
            for g_idx in range(games_count):
                g_steps = game_steps[g_idx]
                g_steps.sort(key=lambda x: x["step"])

                board = chess.Board()
                moves = []
                
                # Pre-push starting FEN
                # The first state is the initial chess layout
                
                for s in g_steps:
                    action = s["action"]
                    move = action_to_move(board, action, cu)
                    if move is None:
                        # Illegal or missing step, stop decoding for this game
                        break

                    move_num = board.fullmove_number
                    color = "w" if board.turn == chess.WHITE else "b"
                    san = board.san(move)
                    uci = move.uci()
                    
                    board.push(move)
                    fen = board.fen()

                    moves.append({
                        "num": move_num,
                        "color": color,
                        "san": san,
                        "uci": uci,
                        "fen": fen
                    })

                if board.is_game_over():
                    res = board.result()
                    if res == "1-0":
                        result_str = "1-0 (White Win)"
                    elif res == "0-1":
                        result_str = "0-1 (Black Win)"
                    elif res == "1/2-1/2":
                        result_str = "1/2-1/2 (Draw)"
                    else:
                        result_str = res
                else:
                    result_str = "Incomplete"

                decoded_games.append({
                    "game_idx": g_idx,
                    "result": result_str,
                    "moves": moves
                })

            # Generate game tree
            tree = build_game_tree(decoded_games)

            self.send_json(200, {
                "battle_id": battle_id,
                "games_count": games_count,
                "wins": wins,
                "draws": draws,
                "games": decoded_games,
                "tree": tree
            })
            return

        else:
            self.send_response(404)
            self.end_headers()

def main():
    print(f"==================================================")
    print(f"       西洋棋對局與分數視覺化儀表板 (Local GUI)")
    print(f"==================================================")
    print(f" * 伺服器啟動於: http://localhost:{PORT}")
    print(f"==================================================")
    
    server_address = ('', PORT)
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(server_address, VisualizerHandler) as httpd:
            webbrowser.open(f"http://localhost:{PORT}")
            print("瀏覽器已自動開啟。請在網頁上點擊以探索棋步與 ELO 變動！")
            print("按下 Ctrl+C 可停止本地視覺化伺服器。")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n視覺化伺服器已停止。感謝使用！")

# Premium HTML/CSS/JS frontend served directly by the server
HTML_CONTENT = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>ML Arena Chess Analyzer Dashboard</title>
    <!-- CSS and Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    
    <style>
        :root {
            --bg-primary: #0a0f1d;
            --bg-secondary: #131a2c;
            --bg-glass: rgba(20, 30, 50, 0.75);
            --border-glass: rgba(255, 255, 255, 0.08);
            --accent: #6366f1;
            --accent-hover: #4f46e5;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-accent: #38bdf8;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
        }

        body {
            margin: 0;
            padding: 0;
            background: radial-gradient(circle at center, #111827 0%, #030712 100%);
            font-family: 'Outfit', sans-serif;
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        header {
            background: var(--bg-glass);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-glass);
            padding: 15px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo h1 {
            font-size: 1.5rem;
            font-weight: 800;
            margin: 0;
            background: linear-gradient(45deg, #818cf8, #38bdf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 0.5px;
        }

        .nav-tabs {
            display: flex;
            gap: 8px;
            background: rgba(0, 0, 0, 0.2);
            padding: 4px;
            border-radius: 80px;
            border: 1px solid var(--border-glass);
        }

        .tab-btn {
            background: transparent;
            color: var(--text-secondary);
            border: none;
            padding: 8px 20px;
            border-radius: 80px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .tab-btn:hover {
            color: var(--text-primary);
        }

        .tab-btn.active {
            background: var(--accent);
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }

        main {
            flex: 1;
            padding: 30px 40px;
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
            box-sizing: border-box;
        }

        .tab-content {
            display: none;
            animation: fadeIn 0.4s ease;
        }

        .tab-content.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Dashboard Overview Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: var(--bg-glass);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
            border-color: rgba(255, 255, 255, 0.15);
        }

        .stat-card h3 {
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            margin: 0 0 10px 0;
            letter-spacing: 1px;
        }

        .stat-card .value {
            font-size: 2rem;
            font-weight: 800;
            margin: 0;
            color: #ffffff;
        }

        /* Two columns layout */
        .columns-layout {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 30px;
            align-items: start;
        }

        @media (max-width: 1024px) {
            .columns-layout {
                grid-template-columns: 1fr;
            }
        }

        .table-container {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        th {
            padding: 14px 16px;
            color: var(--text-secondary);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border-glass);
            font-weight: 700;
        }

        td {
            padding: 14px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            font-size: 0.95rem;
            color: #e2e8f0;
        }

        tr {
            transition: background 0.15s ease;
        }

        tbody tr:hover {
            background: rgba(255, 255, 255, 0.03);
            cursor: pointer;
        }

        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 80px;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .badge.win { background: rgba(16, 185, 129, 0.15); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge.loss { background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.3); }
        .badge.draw { background: rgba(245, 158, 11, 0.15); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.3); }
        .badge.fail { background: rgba(148, 163, 184, 0.15); color: var(--text-secondary); border: 1px solid rgba(148, 163, 184, 0.3); }

        .search-bar {
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }

        .search-input {
            flex: 1;
            min-width: 250px;
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid var(--border-glass);
            border-radius: 80px;
            padding: 12px 24px;
            color: #ffffff;
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.2s ease;
        }

        .search-input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 12px rgba(99, 102, 241, 0.2);
        }

        .filter-group {
            display: flex;
            gap: 6px;
            background: rgba(0, 0, 0, 0.25);
            padding: 4px;
            border-radius: 80px;
            border: 1px solid var(--border-glass);
        }

        .filter-btn {
            background: transparent;
            color: var(--text-secondary);
            border: none;
            padding: 8px 16px;
            border-radius: 80px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .filter-btn.active {
            background: rgba(255, 255, 255, 0.08);
            color: #ffffff;
        }

        /* Chess Board & Game Tree Replay layout */
        .replay-layout {
            display: grid;
            grid-template-columns: 460px 1fr;
            gap: 40px;
            align-items: stretch;
        }

        @media (max-width: 1100px) {
            .replay-layout {
                grid-template-columns: 1fr;
            }
        }

        .board-panel {
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .chessboard {
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            grid-template-rows: repeat(8, 1fr);
            width: 420px;
            height: 420px;
            border: 6px solid #1e293b;
            border-radius: 12px;
            box-shadow: 0 15px 45px rgba(0, 0, 0, 0.5);
            position: relative;
            user-select: none;
            overflow: hidden;
        }

        .square {
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            width: 100%;
            height: 100%;
        }

        .square.light { background-color: #f0d9b5; }
        .square.dark { background-color: #b58863; }
        .square.last-move { box-shadow: inset 0 0 0 4px #eab308; }

        .chessboard img {
            width: 86%;
            height: 86%;
            object-fit: contain;
            pointer-events: none;
        }

        .coord {
            position: absolute;
            font-size: 9px;
            font-weight: 700;
            color: rgba(181, 136, 99, 0.8);
        }

        .square.light .coord { color: rgba(181, 136, 99, 0.8); }
        .square.dark .coord { color: rgba(240, 217, 181, 0.8); }

        .coord.file { bottom: 2px; right: 4px; }
        .coord.rank { top: 2px; left: 4px; }

        .playback-controls {
            display: flex;
            flex-direction: column;
            gap: 12px;
            width: 100%;
            margin-top: 20px;
        }

        .control-btns {
            display: flex;
            justify-content: center;
            gap: 8px;
        }

        .ctrl-btn {
            background: #1e293b;
            border: 1px solid var(--border-glass);
            color: #ffffff;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            font-size: 1.1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }

        .ctrl-btn:hover {
            background: var(--accent);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
            transform: scale(1.05);
        }

        .ctrl-btn:active {
            transform: scale(0.95);
        }

        .slider-container {
            display: flex;
            align-items: center;
            gap: 15px;
            width: 100%;
        }

        input[type=range] {
            flex: 1;
            background: #1e293b;
            height: 6px;
            border-radius: 5px;
            outline: none;
            -webkit-appearance: none;
        }

        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: var(--accent);
            cursor: pointer;
            box-shadow: 0 0 8px rgba(99, 102, 241, 0.6);
        }

        /* Tree panel styling */
        .tree-panel {
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        .tree-box {
            flex: 1;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            overflow: auto;
            position: relative;
            min-height: 450px;
            max-height: 600px;
        }

        #tree-container {
            width: 100%;
            height: 100%;
        }

        .node circle {
            transition: fill 0.2s, stroke 0.2s;
        }

        .node text {
            fill: #e2e8f0;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
        }

        .node:hover circle {
            stroke: var(--warning) !important;
            stroke-width: 3px !important;
        }

        .link {
            transition: stroke 0.2s;
        }

        .node-details-card {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-glass);
            border-radius: 12px;
            padding: 15px;
            margin-top: 15px;
        }

        .game-selector-group {
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }

        .game-select-btn {
            background: #1e293b;
            color: var(--text-secondary);
            border: 1px solid var(--border-glass);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .game-select-btn.active {
            background: var(--accent);
            color: #ffffff;
            border-color: var(--accent);
        }

        /* Move list styling */
        .move-list-box {
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border-glass);
            border-radius: 12px;
            padding: 10px;
            margin-top: 15px;
            max-height: 140px;
            overflow-y: auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
            gap: 6px;
        }

        .move-item {
            padding: 5px 8px;
            background: #1e293b;
            border: 1px solid var(--border-glass);
            border-radius: 6px;
            text-align: center;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.15s ease;
            font-family: 'JetBrains Mono', monospace;
        }

        .move-item:hover {
            border-color: var(--accent);
            color: #ffffff;
        }

        .move-item.active {
            background: var(--accent);
            color: #ffffff;
            border-color: var(--accent);
            font-weight: 600;
        }

        .pulse {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: var(--success);
            border-radius: 50%;
            margin-right: 8px;
            box-shadow: 0 0 10px var(--success);
            animation: blink 2s infinite;
        }

        @keyframes blink {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
    </style>
</head>
<body>

<header>
    <div class="logo">
        <span class="pulse"></span>
        <h1>ML Arena Chess Analyzer</h1>
    </div>
    <div class="nav-tabs">
        <button class="tab-btn active" onclick="switchTab('leaderboard')">競賽排行榜</button>
        <button class="tab-btn" onclick="switchTab('search')">對局紀錄搜尋</button>
        <button class="tab-btn" id="replay-tab-btn" onclick="switchTab('replay')">對局樹與回放</button>
    </div>
    <div style="font-size: 0.9rem; color: var(--text-secondary);">
        API 連線狀態: <span style="color: var(--success); font-weight: 600;">已連線</span>
    </div>
</header>

<main>
    <!-- TAB 1: LEADERBOARD -->
    <div id="tab-leaderboard" class="tab-content active">
        <div class="stats-grid">
            <div class="card stat-card">
                <h3>總參賽隊伍</h3>
                <p class="value" id="stat-total-players">-</p>
            </div>
            <div class="card stat-card">
                <h3>最高 ELO</h3>
                <p class="value" id="stat-top-elo">-</p>
            </div>
            <div class="card stat-card">
                <h3>平均 ELO</h3>
                <p class="value" id="stat-avg-elo">-</p>
            </div>
            <div class="card stat-card">
                <h3>活躍槽位</h3>
                <p class="value" id="stat-active-slots">-</p>
            </div>
        </div>

        <div class="columns-layout">
            <div class="card">
                <h2 style="margin-top: 0; margin-bottom: 20px; font-weight: 700;">排行榜排名</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>排名</th>
                                <th>使用者名稱</th>
                                <th>槽位名稱</th>
                                <th>ELO 積分</th>
                                <th>對決局數</th>
                            </tr>
                        </thead>
                        <tbody id="leaderboard-body">
                            <!-- JS loaded -->
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="flex flex-col gap-4">
                <div class="card">
                    <h3 style="margin-top: 0; margin-bottom: 15px; font-weight: 700;">Top 10 積分圖表</h3>
                    <div style="position: relative; height: 260px;">
                        <canvas id="topEloChart"></canvas>
                    </div>
                </div>
                
                <div class="card" style="margin-top: 25px;">
                    <h3 style="margin-top: 0; margin-bottom: 15px; font-weight: 700;">ELO 積分分佈</h3>
                    <div style="position: relative; height: 260px;">
                        <canvas id="eloDistributionChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 2: SEARCH RECORDS -->
    <div id="tab-search" class="tab-content">
        <div class="card">
            <h2 style="margin-top: 0; margin-bottom: 20px; font-weight: 700;">對局歷史紀錄搜尋</h2>
            
            <div class="search-bar">
                <input type="text" class="search-input" id="search-input" placeholder="輸入對手學號、Battle ID 進行搜尋..." oninput="filterHistory()">
                <div class="filter-group">
                    <button class="filter-btn active" onclick="setResultFilter('ALL', this)">全部</button>
                    <button class="filter-btn" onclick="setResultFilter('WIN', this)">勝場 🏆</button>
                    <button class="filter-btn" onclick="setResultFilter('LOSS', this)">敗場 ❌</button>
                    <button class="filter-btn" onclick="setResultFilter('DRAW', this)">平局 🤝</button>
                    <button class="filter-btn" onclick="setResultFilter('FAIL', this)">失敗 ⚙️</button>
                </div>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>對戰時間</th>
                            <th>對戰 ID</th>
                            <th>對手名稱</th>
                            <th>對手 ELO</th>
                            <th>對決結果</th>
                            <th>我方 ELO 變動</th>
                            <th>資料來源</th>
                        </tr>
                    </thead>
                    <tbody id="history-body">
                        <!-- JS loaded -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- TAB 3: REPLAY & GAME TREE -->
    <div id="tab-replay" class="tab-content">
        <div class="card" style="margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div>
                    <h2 style="margin: 0; font-weight: 700;">對局回放與樹狀決策圖</h2>
                    <p style="margin: 5px 0 0 0; color: var(--text-secondary); font-size: 0.9rem;" id="replay-header-info">
                        請從「對局紀錄搜尋」分頁點擊任一對局，或在此輸入 Battle ID 直接載入。
                    </p>
                </div>
                <div style="display: flex; gap: 10px;">
                    <input type="number" id="direct-load-id" class="search-input" style="padding: 8px 16px; min-width: 120px; max-width: 150px;" placeholder="Battle ID">
                    <button class="game-select-btn active" style="padding: 8px 16px; border-radius: 80px;" onclick="loadDirectBattle()">載入</button>
                </div>
            </div>
        </div>

        <div class="replay-layout" id="replay-interactive-area" style="display: none;">
            <!-- Left panel: Chessboard -->
            <div class="board-panel">
                <div class="card" style="width: 100%; display: flex; flex-direction: column; align-items: center; box-sizing: border-box;">
                    <h3 style="margin-top: 0; margin-bottom: 12px; font-weight: 700; width: 100%; text-align: left;" id="active-game-title">Game 0</h3>
                    
                    <div class="chessboard" id="chessboard"></div>
                    
                    <div class="playback-controls">
                        <div class="slider-container">
                            <span id="step-min-lbl" style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--text-secondary);">0</span>
                            <input type="range" id="playback-slider" min="0" max="0" value="0" oninput="jumpToStep(this.value)">
                            <span id="step-max-lbl" style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--text-secondary);">0</span>
                        </div>
                        
                        <div class="control-btns">
                            <button class="ctrl-btn" onclick="firstStep()" title="回起點">⏮</button>
                            <button class="ctrl-btn" onclick="prevStep()" title="上一步">◀</button>
                            <button class="ctrl-btn" id="play-btn" onclick="togglePlay()" title="自動播放">▶</button>
                            <button class="ctrl-btn" onclick="nextStep()" title="下一步">▶</button>
                            <button class="ctrl-btn" onclick="lastStep()" title="到終點">⏭</button>
                        </div>
                    </div>

                    <div style="width: 100%; margin-top: 15px;">
                        <span style="font-size: 0.9rem; color: var(--text-secondary); display: block; margin-bottom: 5px; font-weight: 600;">對決選擇 (10 局):</span>
                        <div class="game-selector-group" id="game-selector-container">
                            <!-- Generated -->
                        </div>
                    </div>
                </div>

                <div class="card" style="width: 100%; margin-top: 20px; box-sizing: border-box;">
                    <h3 style="margin-top: 0; margin-bottom: 10px; font-weight: 700;">本局棋步清單</h3>
                    <div class="move-list-box" id="move-list-container">
                        <!-- Generated -->
                    </div>
                </div>
            </div>

            <!-- Right panel: D3 Decision Tree -->
            <div class="tree-panel">
                <div class="card" style="flex: 1; display: flex; flex-direction: column; box-sizing: border-box;">
                    <h3 style="margin-top: 0; margin-bottom: 5px; font-weight: 700;">10 局分支出子樹 (Decision Opening Tree)</h3>
                    <p style="margin: 0 0 15px 0; color: var(--text-secondary); font-size: 0.85rem;">
                        將 10 局的走子路徑視覺化為樹狀結構。圓圈大小代表經過該走法的對局數量。點擊任一走子節點，棋盤會自動跳轉至該步局面。
                    </p>
                    
                    <div class="tree-box">
                        <div id="tree-container"></div>
                    </div>

                    <div class="node-details-card">
                        <h4 style="margin-top: 0; margin-bottom: 10px; font-weight: 700; color: #ffffff;">節點走法詳細資訊</h4>
                        <div id="node-details">
                            <span style="color: var(--text-secondary); font-size: 0.9rem;">點擊上方決策樹的圓圈節點，即可顯示詳細局勢與分支對決。</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card" id="replay-placeholder" style="text-align: center; padding: 60px 20px;">
            <p style="font-size: 1.2rem; color: var(--text-secondary); margin: 0 0 20px 0;">
                尚未載入任何對局資料。
            </p>
            <button class="tab-btn active" style="padding: 10px 24px; border-radius: 80px;" onclick="switchTab('search')">前往尋找對局</button>
        </div>
    </div>
</main>

<!-- JS Logic -->
<script>
    let activeTab = 'leaderboard';
    let leaderboardData = [];
    let historyData = [];
    let currentResultFilter = 'ALL';
    
    // Replay State
    let activeReplay = null;
    let activeGameIdx = 0;
    let activeStepIdx = 0;
    let playbackInterval = null;
    let isPlaying = false;
    
    // Charts instances
    let topEloChart = null;
    let eloDistributionChart = null;

    document.addEventListener("DOMContentLoaded", () => {
        loadLeaderboard();
        loadHistory();
    });

    function switchTab(tabId) {
        activeTab = tabId;
        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
        
        document.getElementById(`tab-${tabId}`).classList.add('active');
        
        // Handle nav tab highlight
        if (tabId === 'replay') {
            document.getElementById('replay-tab-btn').classList.add('active');
        } else {
            // Normal tab highlighting is handled by inline events or class logic
            // To be safe, let's explicitly find and highlight
            const btnText = tabId === 'leaderboard' ? '競賽排行榜' : '對局紀錄搜尋';
            document.querySelectorAll('.tab-btn').forEach(btn => {
                if (btn.innerText === btnText) btn.classList.add('active');
            });
        }
        
        // Re-render D3 tree if we switch to replay and data is active to avoid sizing issues
        if (tabId === 'replay' && activeReplay) {
            setTimeout(() => {
                renderTree(activeReplay.tree);
            }, 100);
        }
    }

    // Leaderboard Loading and Rendering
    function loadLeaderboard() {
        fetch('/api/leaderboard')
            .then(res => res.json())
            .then(data => {
                leaderboardData = data;
                renderLeaderboardTable(data);
                renderLeaderboardStats(data);
                renderLeaderboardCharts(data);
            })
            .catch(err => {
                console.error("Error loading leaderboard:", err);
            });
    }

    function renderLeaderboardTable(data) {
        const tbody = document.getElementById("leaderboard-body");
        tbody.innerHTML = "";
        
        data.forEach((row, idx) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td style="font-weight: 700; color: ${idx === 0 ? 'var(--warning)' : '#e2e8f0'};">#${idx + 1}</td>
                <td style="font-weight: 600;">${row.username || '—'}</td>
                <td>${row.slot_name || '—'}</td>
                <td style="font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--text-accent);">${(row.elo_rating || 1000).toFixed(1)}</td>
                <td>${row.elo_games_played || 0}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function renderLeaderboardStats(data) {
        document.getElementById("stat-total-players").innerText = data.length;
        if (data.length > 0) {
            const elos = data.map(d => d.elo_rating || 1000);
            const topElo = Math.max(...elos);
            const avgElo = elos.reduce((sum, val) => sum + val, 0) / elos.length;
            const activeSlots = data.filter(d => d.slot_id && d.slot_id !== 0).length;
            
            document.getElementById("stat-top-elo").innerText = topElo.toFixed(1);
            document.getElementById("stat-avg-elo").innerText = avgElo.toFixed(1);
            document.getElementById("stat-active-slots").innerText = activeSlots;
        }
    }

    function renderLeaderboardCharts(data) {
        if (data.length === 0) return;
        
        // 1. Top 10 players Chart
        const top10 = data.slice(0, 10);
        const top10Labels = top10.map(d => d.username || d.slot_name);
        const top10Elos = top10.map(d => d.elo_rating || 1000);
        
        const ctxTop = document.getElementById("topEloChart").getContext("2d");
        if (topEloChart) topEloChart.destroy();
        topEloChart = new Chart(ctxTop, {
            type: 'bar',
            data: {
                labels: top10Labels,
                datasets: [{
                    label: 'ELO Rating',
                    data: top10Elos,
                    backgroundColor: 'rgba(99, 102, 241, 0.65)',
                    borderColor: 'rgb(99, 102, 241)',
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        min: 800,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });

        // 2. ELO distribution histogram chart
        const elos = data.map(d => d.elo_rating || 1000);
        const minElo = Math.floor(Math.min(...elos) / 100) * 100;
        const maxElo = Math.ceil(Math.max(...elos) / 100) * 100;
        
        const brackets = {};
        for (let b = minElo; b < maxElo; b += 100) {
            brackets[`${b}-${b+100}`] = 0;
        }
        
        elos.forEach(elo => {
            for (let b = minElo; b < maxElo; b += 100) {
                if (elo >= b && elo < b + 100) {
                    brackets[`${b}-${b+100}`]++;
                    break;
                }
            }
        });

        const distLabels = Object.keys(brackets);
        const distData = Object.values(brackets);

        const ctxDist = document.getElementById("eloDistributionChart").getContext("2d");
        if (eloDistributionChart) eloDistributionChart.destroy();
        eloDistributionChart = new Chart(ctxDist, {
            type: 'bar',
            data: {
                labels: distLabels,
                datasets: [{
                    label: 'Player Count',
                    data: distData,
                    backgroundColor: 'rgba(56, 189, 248, 0.65)',
                    borderColor: 'rgb(56, 189, 248)',
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8', stepSize: 1 }
                    }
                }
            }
        });
    }

    // History Record Loading, Search and Filtering
    function loadHistory() {
        fetch('/api/history')
            .then(res => res.json())
            .then(data => {
                historyData = data;
                renderHistoryTable(data);
            })
            .catch(err => {
                console.error("Error loading match history:", err);
            });
    }

    function renderHistoryTable(data) {
        const tbody = document.getElementById("history-body");
        tbody.innerHTML = "";
        
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-secondary); padding: 40px 0;">未尋找到相符的對局紀錄。</td></tr>`;
            return;
        }

        data.forEach(row => {
            const tr = document.createElement("tr");
            tr.onclick = () => loadBattleReplay(row.battle_id);
            
            const eloChangeVal = row.elo_change || 0;
            const sign = eloChangeVal > 0 ? "+" : "";
            let changeColor = 'var(--text-secondary)';
            if (eloChangeVal > 0) changeColor = 'var(--success)';
            else if (eloChangeVal < 0) changeColor = 'var(--danger)';

            const badgeClass = row.result ? row.result.toLowerCase() : 'fail';
            
            tr.innerHTML = `
                <td style="color: var(--text-secondary); font-size: 0.9rem;">${row.timestamp || '—'}</td>
                <td style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #fff;">#${row.battle_id}</td>
                <td style="font-weight: 600;">${row.opponent || 'Unknown'}</td>
                <td style="font-family: 'JetBrains Mono', monospace;">${(row.opponent_elo || 1000).toFixed(1)}</td>
                <td><span class="badge ${badgeClass}">${row.result || 'FAIL'}</span></td>
                <td style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: ${changeColor};">
                    ${sign}${eloChangeVal.toFixed(2)}
                </td>
                <td style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-secondary);">${row.source || 'local'}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function setResultFilter(filterVal, btnEl) {
        currentResultFilter = filterVal;
        document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        btnEl.classList.add('active');
        filterHistory();
    }

    function filterHistory() {
        const q = document.getElementById("search-input").value.toLowerCase().trim();
        
        const filtered = historyData.filter(row => {
            // 1. Text filter
            const matchText = row.opponent.toLowerCase().includes(q) || String(row.battle_id).includes(q);
            
            // 2. Result filter
            let matchResult = true;
            if (currentResultFilter !== 'ALL') {
                matchResult = (row.result === currentResultFilter);
            }
            
            return matchText && matchResult;
        });
        
        renderHistoryTable(filtered);
    }

    // Battle Replay Loading and Game Tree visualization
    function loadBattleReplay(battleId) {
        switchTab('replay');
        document.getElementById("replay-placeholder").style.display = "none";
        
        // Show loading header
        document.getElementById("replay-header-info").innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span class="pulse"></span> 正在載入對局 #${battleId} 的完整數據與棋譜還原...
            </div>
        `;
        document.getElementById("replay-interactive-area").style.display = "none";

        fetch(`/api/replay?battle_id=${battleId}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert("載入對局錯誤: " + data.error);
                    document.getElementById("replay-header-info").innerText = "載入失敗。請重試。";
                    document.getElementById("replay-placeholder").style.display = "block";
                    return;
                }

                activeReplay = data;
                activeGameIdx = 0;
                activeStepIdx = 0;
                
                // Show title
                document.getElementById("replay-header-info").innerHTML = `
                    對戰 ID: <b style="color: #fff;">#${data.battle_id}</b> | 
                    結果: <span class="badge win" style="padding: 2px 8px; font-size: 0.75rem;">White wins: ${data.wins[0]}</span>
                    <span class="badge loss" style="padding: 2px 8px; font-size: 0.75rem; margin-left: 4px;">Black wins: ${data.wins[1]}</span>
                    <span class="badge draw" style="padding: 2px 8px; font-size: 0.75rem; margin-left: 4px;">Draws: ${data.draws}</span>
                `;
                
                // Render interface
                document.getElementById("replay-interactive-area").style.display = "grid";
                
                // Load game selector buttons
                const selectContainer = document.getElementById("game-selector-container");
                selectContainer.innerHTML = "";
                data.games.forEach((game, idx) => {
                    const btn = document.createElement("button");
                    btn.className = `game-select-btn ${idx === 0 ? 'active' : ''}`;
                    btn.innerText = `G${idx} (${game.result.split(" ")[0]})`;
                    btn.onclick = () => selectGame(idx);
                    selectContainer.appendChild(btn);
                });
                
                // Load Game 0 initially
                loadGame(0);
                
                // Draw decision tree
                renderTree(data.tree);
            })
            .catch(err => {
                console.error("Error loading replay details:", err);
                document.getElementById("replay-header-info").innerText = "無法載入該對決的棋步檔案。";
                document.getElementById("replay-placeholder").style.display = "block";
            });
    }

    function loadDirectBattle() {
        const id = document.getElementById("direct-load-id").value.trim();
        if (!id) {
            alert("請輸入正確的 Battle ID。");
            return;
        }
        loadBattleReplay(parseInt(id));
    }

    function selectGame(idx) {
        document.querySelectorAll('.game-select-btn').forEach((btn, bIdx) => {
            if (bIdx === idx) btn.classList.add('active');
            else btn.classList.remove('active');
        });
        
        loadGame(idx);
    }

    function loadGame(idx) {
        if (isPlaying) togglePlay(); // stop autoplay
        
        activeGameIdx = idx;
        activeStepIdx = 0;
        
        const gameData = activeReplay.games[idx];
        document.getElementById("active-game-title").innerText = `Game ${idx} (結果: ${gameData.result})`;
        
        // Setup slider
        const maxStep = gameData.moves.length;
        const slider = document.getElementById("playback-slider");
        slider.max = maxStep;
        slider.value = 0;
        
        document.getElementById("step-min-lbl").innerText = "0";
        document.getElementById("step-max-lbl").innerText = maxStep;
        
        // Setup move list sidebar
        const moveListBox = document.getElementById("move-list-container");
        moveListBox.innerHTML = "";
        
        // Root starting node
        const startItem = document.createElement("div");
        startItem.className = "move-item active";
        startItem.id = `move-item-0`;
        startItem.innerText = "Start";
        startItem.onclick = () => jumpToStep(0);
        moveListBox.appendChild(startItem);

        gameData.moves.forEach((m, mIdx) => {
            const item = document.createElement("div");
            item.className = "move-item";
            item.id = `move-item-${mIdx + 1}`;
            
            const prefix = m.color === 'w' ? `${m.num}.` : `${m.num}...`;
            item.innerText = `${prefix} ${m.san}`;
            item.onclick = () => jumpToStep(mIdx + 1);
            moveListBox.appendChild(item);
        });
        
        // Render starting position
        window.currentMoveUci = "";
        renderFEN(null);
    }

    // Playback functions
    function jumpToStep(step) {
        step = parseInt(step);
        activeStepIdx = step;
        
        document.getElementById("playback-slider").value = step;
        
        // Highlight active move in side list
        document.querySelectorAll('.move-item').forEach(el => el.classList.remove('active'));
        const activeItem = document.getElementById(`move-item-${step}`);
        if (activeItem) {
            activeItem.classList.add('active');
            // scroll into view
            activeItem.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
        
        // Render board
        const gameData = activeReplay.games[activeGameIdx];
        if (step === 0) {
            window.currentMoveUci = "";
            renderFEN(null);
        } else {
            const move = gameData.moves[step - 1];
            window.currentMoveUci = move.uci;
            renderFEN(move.fen);
        }
    }

    function firstStep() { jumpToStep(0); }
    function lastStep() {
        const gameData = activeReplay.games[activeGameIdx];
        jumpToStep(gameData.moves.length);
    }
    
    function prevStep() {
        if (activeStepIdx > 0) jumpToStep(activeStepIdx - 1);
    }
    
    function nextStep() {
        const gameData = activeReplay.games[activeGameIdx];
        if (activeStepIdx < gameData.moves.length) {
            jumpToStep(activeStepIdx + 1);
        } else {
            if (isPlaying) togglePlay(); // stop play at end
        }
    }

    function togglePlay() {
        const playBtn = document.getElementById("play-btn");
        if (isPlaying) {
            clearInterval(playbackInterval);
            playBtn.innerText = "▶";
            isPlaying = false;
        } else {
            const gameData = activeReplay.games[activeGameIdx];
            if (activeStepIdx >= gameData.moves.length) {
                activeStepIdx = 0; // restart
            }
            playBtn.innerText = "⏸";
            isPlaying = true;
            playbackInterval = setInterval(nextStep, 1000);
        }
    }

    // Chessboard FEN parser and element generator
    function renderFEN(fen) {
        const boardEl = document.getElementById("chessboard");
        boardEl.innerHTML = "";
        
        if (!fen) fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
        
        const parts = fen.split(" ");
        const boardPart = parts[0];
        const ranks = boardPart.split("/");
        
        let lastMoveFrom = null;
        let lastMoveTo = null;
        if (window.currentMoveUci && window.currentMoveUci.length >= 4) {
            lastMoveFrom = window.currentMoveUci.substring(0, 2);
            lastMoveTo = window.currentMoveUci.substring(2, 4);
        }
        
        const pieceMap = {
            'P': 'wP', 'N': 'wN', 'B': 'wB', 'R': 'wR', 'Q': 'wK', 'K': 'wQ', // Note: fixing King/Queen mismatch just in case if standard is wK/wQ
            'p': 'bP', 'n': 'bN', 'b': 'bB', 'r': 'bR', 'q': 'bQ', 'k': 'bK'
        };
        // Standard ChessboardJS themes:
        // K is King, Q is Queen. Let's fix mapping:
        const standardPieceMap = {
            'P': 'wP', 'N': 'wN', 'B': 'wB', 'R': 'wR', 'Q': 'wQ', 'K': 'wK',
            'p': 'bP', 'n': 'bN', 'b': 'bB', 'r': 'bR', 'q': 'bQ', 'k': 'bK'
        };
        
        for (let r = 0; r < 8; r++) {
            const rankStr = ranks[r];
            let c = 0; 
            for (let i = 0; i < rankStr.length; i++) {
                const char = rankStr[i];
                if (isNaN(char)) {
                    createSquare(r, c, char);
                    c++;
                } else {
                    const count = parseInt(char);
                    for (let k = 0; k < count; k++) {
                        createSquare(r, c, null);
                        c++;
                    }
                }
            }
        }
        
        function createSquare(row, col, pieceChar) {
            const squareEl = document.createElement("div");
            const isLight = (row + col) % 2 === 0;
            squareEl.className = `square ${isLight ? 'light' : 'dark'}`;
            
            const fileChar = String.fromCharCode(97 + col);
            const rankChar = String.fromCharCode(56 - row);
            const sqCoord = fileChar + rankChar;
            
            if (sqCoord === lastMoveFrom || sqCoord === lastMoveTo) {
                squareEl.classList.add("last-move");
            }
            
            if (pieceChar) {
                const pieceName = standardPieceMap[pieceChar];
                const img = document.createElement("img");
                img.src = `https://chessboardjs.com/img/chesspieces/wikipedia/${pieceName}.png`;
                img.alt = pieceChar;
                squareEl.appendChild(img);
            }
            
            if (row === 7) {
                const fileLbl = document.createElement("div");
                fileLbl.className = "coord file";
                fileLbl.innerText = fileChar;
                squareEl.appendChild(fileLbl);
            }
            if (col === 0) {
                const rankLbl = document.createElement("div");
                rankLbl.className = "coord rank";
                rankLbl.innerText = rankChar;
                squareEl.appendChild(rankLbl);
            }
            
            boardEl.appendChild(squareEl);
        }
    }

    // Interactive D3 Tree Renderer
    function renderTree(treeData) {
        const container = document.getElementById("tree-container");
        container.innerHTML = "";
        
        if (!treeData) return;
        
        function getDepth(node) {
            if (!node.children || node.children.length === 0) return 1;
            return 1 + Math.max(...node.children.map(getDepth));
        }
        
        function getLeaves(node) {
            if (!node.children || node.children.length === 0) return 1;
            return node.children.reduce((acc, child) => acc + getLeaves(child), 0);
        }
        
        const depth = getDepth(treeData);
        const leaves = getLeaves(treeData);
        
        // Add scroll offsets
        const width = Math.max(900, depth * 170);
        const height = Math.max(450, leaves * 52);
        
        const svg = d3.select("#tree-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", "translate(60, 0)");
            
        const tree = d3.tree().size([height - 50, width - 220]);
        
        const root = d3.hierarchy(treeData, d => d.children);
        tree(root);
        
        // Draw links
        svg.selectAll(".link")
            .data(root.links())
            .enter()
            .append("path")
            .attr("class", "link")
            .attr("d", d3.linkHorizontal()
                .x(d => d.y)
                .y(d => d.x))
            .style("fill", "none")
            .style("stroke", "rgba(99, 102, 241, 0.35)")
            .style("stroke-width", "2px");
            
        // Create nodes
        const node = svg.selectAll(".node")
            .data(root.descendants())
            .enter()
            .append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${d.y},${d.x})`)
            .style("cursor", "pointer")
            .on("click", (event, d) => {
                // Highlight circle
                d3.selectAll(".node circle")
                    .style("stroke", "rgba(99, 102, 241, 0.8)")
                    .style("stroke-width", "2px");
                d3.select(event.currentTarget).select("circle")
                    .style("stroke", "#f59e0b")
                    .style("stroke-width", "4px");
                    
                // Update board
                window.currentMoveUci = d.data.uci;
                renderFEN(d.data.fen);
                
                // Show info
                showNodeDetails(d.data);
            });
            
        // Styled circular node nodes
        node.append("circle")
            .attr("r", d => 6 + (d.data.games_count || 1) * 1.5)
            .style("fill", d => {
                if (d.data.name.includes("...")) return "#090d16"; // Black move color
                if (d.data.name === "Start") return "#6366f1"; // Accent for start
                return "#ffffff"; // White move color
            })
            .style("stroke", "rgba(99, 102, 241, 0.8)")
            .style("stroke-width", "2px");
            
        // Move SAN tags
        node.append("text")
            .attr("dy", ".35em")
            .attr("x", d => d.children ? -14 : 14)
            .attr("style", "font-family: 'Outfit', sans-serif; font-size: 11px; font-weight: 600; fill: #e2e8f0;")
            .attr("text-anchor", d => d.children ? "end" : "start")
            .text(d => d.data.name);
            
        // Highlight root node
        svg.select(".node circle").style("stroke", "#f59e0b").style("stroke-width", "4px");
    }

    function showNodeDetails(nodeData) {
        const detailsEl = document.getElementById("node-details");
        if (nodeData.name === "Start") {
            detailsEl.innerHTML = `<span style="color: var(--text-secondary); font-size: 0.95rem;">對局起點位置。所有 10 局對決皆由此開始。</span>`;
            return;
        }
        
        const gamesText = nodeData.games.map(g => `Game ${g}`).join(", ");
        detailsEl.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.95rem;">
                <div><span style="color: var(--text-secondary); font-weight: 500;">下子步數:</span> <span style="font-weight: 700; color: #ffffff;">${nodeData.name}</span></div>
                <div><span style="color: var(--text-secondary); font-weight: 500;">UCI 編碼:</span> <code style="font-family: 'JetBrains Mono', monospace; background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; color: var(--text-accent);">${nodeData.uci}</code></div>
                <div><span style="color: var(--text-secondary); font-weight: 500;">目前局面 FEN:</span> <code style="font-family: 'JetBrains Mono', monospace; background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; font-size: 11px; color: #cbd5e1; word-break: break-all;">${nodeData.fen}</code></div>
                <div><span style="color: var(--text-secondary); font-weight: 500;">涵蓋對局 (${nodeData.games.length} 局):</span> <span style="color: var(--warning); font-weight: 700;">${gamesText}</span></div>
            </div>
        `;
    }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
