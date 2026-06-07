#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Chess Web Application: Play Against D3 Agent
Runs a local server on port 8080 and opens the browser.
No external Python dependencies (uses standard http.server + python-chess).
"""
import http.server
import socketserver
import json
import urllib.parse
import webbrowser
import sys
import os

# Set search path to load the agent
sys.path.append("/Users/liuchiahan/Documents/課程/人工智慧導論/rl_starter_11/agents/d4_pro")
try:
    import chess
    import agent
except ImportError as e:
    print(f"Error: Missing required library '{e.name}'. Please make sure 'chess' is installed in your python environment.")
    sys.exit(1)

PORT = 8080

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>挑戰 D3 西洋棋 AI 代理人</title>
    <!-- CSS and Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/chessboard-js/1.0.0/chessboard-1.0.0.min.css">
    
    <style>
        body {
            margin: 0;
            padding: 0;
            background: radial-gradient(circle at center, #1b263b 0%, #0d1b2a 100%);
            font-family: 'Outfit', sans-serif;
            color: #e0e1dd;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow-x: hidden;
        }

        .container {
            display: flex;
            flex-direction: row;
            gap: 40px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 30px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
            max-width: 1000px;
            width: 90%;
            align-items: stretch;
            transition: all 0.3s ease;
        }

        .board-container {
            flex: 1.2;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        #my-board {
            width: 480px;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            border: 4px solid #415a77;
        }

        .controls-container {
            flex: 0.8;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.02);
            border-left: 1px solid rgba(255, 255, 255, 0.08);
            padding-left: 30px;
        }

        h1 {
            font-weight: 800;
            font-size: 2.2rem;
            margin-top: 0;
            background: linear-gradient(45deg, #00b4d8, #90e0ef);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 4px 10px rgba(0, 180, 216, 0.2);
            letter-spacing: 1px;
        }

        .status-box {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            padding: 15px 20px;
            font-size: 1.1rem;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            min-height: 50px;
            display: flex;
            align-items: center;
        }

        .status-active {
            color: #00b4d8;
            font-weight: 600;
        }

        .settings-group {
            margin-bottom: 25px;
        }

        .settings-label {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #a3b18a;
            margin-bottom: 10px;
            display: block;
        }

        .btn-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        button {
            background: #415a77;
            color: #e0e1dd;
            border: none;
            padding: 12px 24px;
            border-radius: 80px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        button:hover {
            background: #778da9;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 180, 216, 0.3);
        }

        button:active {
            transform: translateY(0);
        }

        button.primary {
            background: linear-gradient(135deg, #0077b6, #00b4d8);
        }

        button.primary:hover {
            background: linear-gradient(135deg, #0096c7, #48cae4);
        }

        button.secondary {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        button.secondary:hover {
            background: rgba(255, 255, 255, 0.15);
        }

        .color-choice {
            display: flex;
            gap: 15px;
            margin-top: 5px;
        }

        .color-btn {
            flex: 1;
            padding: 10px;
            text-align: center;
            border-radius: 80px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            cursor: pointer;
            transition: all 0.2s ease;
            font-weight: 600;
        }

        .color-btn.selected {
            background: #00b4d8;
            color: #0d1b2a;
            box-shadow: 0 0 15px rgba(0, 180, 216, 0.5);
            border-color: #00b4d8;
        }

        .slider-container {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        input[type=range] {
            flex: 1;
            background: #415a77;
            height: 6px;
            border-radius: 5px;
            outline: none;
            -webkit-appearance: none;
        }

        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #00b4d8;
            cursor: pointer;
            box-shadow: 0 0 8px rgba(0, 180, 216, 0.8);
        }

        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #00b4d8;
            animation: spin 1s ease-in-out infinite;
            margin-right: 10px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @media (max-width: 800px) {
            .container {
                flex-direction: column;
            }
            .controls-container {
                border-left: none;
                border-top: 1px solid rgba(255, 255, 255, 0.08);
                padding-left: 0;
                padding-top: 30px;
                margin-top: 20px;
            }
            #my-board {
                width: 320px;
            }
        }
    </style>
</head>
<body>

<div class="container">
    <!-- Left panel: Board -->
    <div class="board-container">
        <div id="my-board"></div>
    </div>
    
    <!-- Right panel: Controls -->
    <div class="controls-container">
        <div>
            <h1>D3 AI 西洋棋對局</h1>
            
            <div class="status-box" id="status-box">
                準備就緒，選擇您的顏色並開始對局！
            </div>
            
            <div class="settings-group">
                <span class="settings-label">選擇您的顏色</span>
                <div class="color-choice">
                    <div class="color-btn selected" id="play-white" onclick="selectColor('w')">執白 (先手)</div>
                    <div class="color-btn" id="play-black" onclick="selectColor('b')">執黑 (後手)</div>
                </div>
            </div>
            
            <div class="settings-group">
                <span class="settings-label">AI 搜尋深度 (Depth)</span>
                <div class="slider-container">
                    <input type="range" id="depth-slider" min="1" max="4" value="3" oninput="updateDepthVal(this.value)">
                    <span id="depth-val" style="font-weight: 600; font-size: 1.1rem; color: #00b4d8;">3</span>
                </div>
            </div>
        </div>
        
        <div>
            <div class="btn-group">
                <button class="primary" onclick="restartGame()">開始新局 / 重新開始</button>
            </div>
            <p style="font-size: 0.8rem; color: #778da9; margin: 0; text-align: center;">
                後端載入 <b>agent.py</b> 運算核心
            </p>
        </div>
    </div>
</div>

<!-- JS Imports -->
<script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chessboard-js/1.0.0/chessboard-1.0.0.min.js"></script>

<script>
    var board = null;
    var game = new Chess();
    var playerColor = 'w';
    var aiThinking = false;
    var searchDepth = 3;

    function selectColor(color) {
        if (game.history().length > 0) {
            if (!confirm("對局已經開始，更換顏色將會重新開始遊戲。確定嗎？")) return;
        }
        playerColor = color;
        $('.color-btn').removeClass('selected');
        if (color === 'w') {
            $('#play-white').addClass('selected');
        } else {
            $('#play-black').addClass('selected');
        }
        restartGame();
    }

    function updateDepthVal(val) {
        searchDepth = parseInt(val);
        $('#depth-val').text(val);
    }

    function updateStatus() {
        var status = '';

        var moveColor = '白方';
        if (game.turn() === 'b') {
            moveColor = '黑方';
        }

        // Checkmate?
        if (game.in_checkmate()) {
            status = '遊戲結束，' + moveColor + ' 被將死！';
        }
        // Draw?
        else if (game.in_draw()) {
            status = '遊戲結束，平局！';
        }
        // Game still active
        else {
            if (aiThinking) {
                status = '<div class="spinner"></div> D3 正在精算最佳著法中...';
            } else {
                var isPlayersTurn = (game.turn() === playerColor);
                if (isPlayersTurn) {
                    status = '<span class="status-active">換您下棋！</span>';
                } else {
                    status = '換 D3 下棋...';
                }
                
                if (game.in_check()) {
                    status += ' (被將軍！)';
                }
            }
        }

        $('#status-box').html(status);
    }

    // Handle drag-and-drop actions
    function onDragStart(source, piece, position, orientation) {
        // Do not pick up pieces if the game is over
        if (game.game_over() || aiThinking) return false;

        // Only pick up pieces for the player's side
        if (playerColor === 'w' && piece.search(/^b/) !== -1) return false;
        if (playerColor === 'b' && piece.search(/^w/) !== -1) return false;
        if (game.turn() !== playerColor) return false;
    }

    function makeAIMove() {
        if (game.game_over()) return;

        aiThinking = true;
        updateStatus();

        $.ajax({
            url: '/move',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                fen: game.fen(),
                depth: searchDepth,
                ai_color: playerColor === 'w' ? 'b' : 'w'
            }),
            success: function(response) {
                aiThinking = false;
                if (response.move) {
                    var move = game.move({
                        from: response.move.substring(0, 2),
                        to: response.move.substring(2, 4),
                        promotion: response.move.substring(4) || undefined
                    });
                    
                    if (move === null) {
                        console.error("AI returned illegal move: " + response.move);
                        // Make a random move as fallback on frontend
                        var moves = game.moves();
                        game.move(moves[Math.floor(Math.random() * moves.length)]);
                    }
                    
                    board.position(game.fen());
                } else {
                    console.error("No move returned from AI: ", response);
                }
                updateStatus();
            },
            error: function(err) {
                aiThinking = false;
                console.error("Error communicating with AI server: ", err);
                updateStatus();
            }
        });
    }

    function onDrop(source, target) {
        // See if the move is legal
        var move = game.move({
            from: source,
            to: target,
            promotion: 'q' // Always promote to queen for simplicity on drag-and-drop
        });

        // Illegal move
        if (move === null) return 'snapback';

        updateStatus();
        
        // Trigger AI move after a small delay
        window.setTimeout(makeAIMove, 250);
    }

    // Update the board position after the piece snap
    // for castling, en passant, pawn promotion
    function onSnapEnd() {
        board.position(game.fen());
    }

    function restartGame() {
        game.reset();
        board.orientation(playerColor === 'w' ? 'white' : 'black');
        board.position('start');
        aiThinking = false;
        updateStatus();
        
        // If AI is white, trigger first move
        if (playerColor === 'b') {
            window.setTimeout(makeAIMove, 500);
        }
    }

    var config = {
        draggable: true,
        position: 'start',
        onDragStart: onDragStart,
        onDrop: onDrop,
        onSnapEnd: onSnapEnd,
        pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png'
    };
    board = Chessboard('my-board', config);
    restartGame();
</script>

</body>
</html>
"""

class CustomChessHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Mute console request logging to keep terminal clean
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/move":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                params = json.loads(post_data.decode("utf-8"))
                fen = params.get("fen")
                depth = params.get("depth", 3)
                ai_color = params.get("ai_color", "b") # 'w' or 'b'
                
                board = chess.Board(fen)
                
                print(f"Calculated for FEN: {fen} (AI color: {ai_color}, Depth: {depth})")
                
                best_move = None
                
                # IMPORTANT LOGIC FOR SYMMETRY:
                # agent.py assumes the active player is ALWAYS WHITE (relativity).
                # If D3 is playing Black (ai_color == 'b') in the standard chess board,
                # then when it's Black's turn (board.turn == chess.BLACK), 
                # we mirror the board so that D3 thinks it is White playing on a mirrored board.
                if ai_color == "b":
                    mirrored_board = board.mirror()
                    # Perform search on mirrored board
                    mirrored_move = agent.search_best_move(mirrored_board, depth)
                    if mirrored_move:
                        # Translate mirrored move coordinates back to standard coordinates
                        orig_from = chess.square_mirror(mirrored_move.from_square)
                        orig_to = chess.square_mirror(mirrored_move.to_square)
                        best_move = chess.Move(orig_from, orig_to, promotion=mirrored_move.promotion)
                else:
                    # D3 plays White (ai_color == 'w'), board.turn == chess.WHITE. We can search directly.
                    best_move = agent.search_best_move(board, depth)

                if best_move:
                    move_str = best_move.uci()
                    print(f" -> AI selected move: {move_str}")
                    response = {"move": move_str}
                else:
                    response = {"move": None}
                    
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode("utf-8"))
            except Exception as e:
                print("Error calculating best move:", e)
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def main():
    print(f"==================================================")
    print(f"   D3 西洋棋 AI 圖形對局伺服器 (Local Web GUI)")
    print(f"==================================================")
    print(f" * 搜尋核心: {os.path.basename(agent.__file__)}")
    print(f" * 伺服器啟動於: http://localhost:{PORT}")
    print(f" * 提示: 此伺服器在本地單獨運行，絕對不影響背景掛機的 D3 比賽！")
    print(f"==================================================")
    
    server_address = ('', PORT)
    
    # Threading or standard server? A standard server is fine since chess moves are sequential.
    # However, to avoid blocking the socket if the browser drops connection, reuse address is set.
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(server_address, CustomChessHandler) as httpd:
            # Automatically open browser
            webbrowser.open(f"http://localhost:{PORT}")
            print("瀏覽器已自動開啟。請開始與您的 D3 模型下棋！")
            print("按下 Ctrl+C 可停止本地對戰伺服器。")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已停止。感謝遊玩！")

if __name__ == "__main__":
    main()
