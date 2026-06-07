import sys
import os
import time
import importlib.util
import numpy as np
import chess
import pettingzoo.classic.chess.chess_utils as cu

def load_agent(agent_dir, name):
    orig_path = sys.path.copy()
    sys.path.insert(0, agent_dir)
    spec = importlib.util.spec_from_file_location(name, os.path.join(agent_dir, "agent.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    sys.path = orig_path
    return module.Agent()

def make_pettingzoo_obs(board: chess.Board) -> np.ndarray:
    working_board = board.mirror() if board.turn == chess.BLACK else board.copy()
    obs = np.zeros((8, 8, 111), dtype=np.int8)
    if working_board.has_kingside_castling_rights(chess.WHITE):  obs[0, 0, 0] = 1
    if working_board.has_queenside_castling_rights(chess.WHITE): obs[0, 0, 1] = 1
    if working_board.has_kingside_castling_rights(chess.BLACK):  obs[0, 0, 2] = 1
    if working_board.has_queenside_castling_rights(chess.BLACK): obs[0, 0, 3] = 1

    piece_map = {
        chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 2,
        chess.ROOK: 3, chess.QUEEN: 4, chess.KING: 5
    }

    for square in chess.SQUARES:
        piece = working_board.piece_at(square)
        if piece is not None:
            file_idx = chess.square_file(square)
            rank_idx = 7 - chess.square_rank(square)
            
            is_my_piece = (piece.color == chess.WHITE)
            base_channel = 7 if is_my_piece else 13
            channel = base_channel + piece_map[piece.piece_type]
            
            obs[rank_idx, file_idx, channel] = 1

    if working_board.has_legal_en_passant():
        ep_sq = working_board.ep_square
        file_idx = chess.square_file(ep_sq)
        obs[0, file_idx, 13] = 1
    return obs

def get_action_mask(board: chess.Board) -> np.ndarray:
    mask = np.zeros(4672, dtype=np.int8)
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
        if 0 <= act < 4672:
            mask[act] = 1
    return mask

def action_to_move(board: chess.Board, action: int) -> chess.Move:
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

def main():
    print("Loading Agents...")
    
    # 建立臨時 extract 軟連結，以便 C++ 引擎能被 Python import 找到
    # 在本機，我們可以直接在 rl_starter_11/agents/d6_cpp 底下運行，
    # 但為了完全模擬生產環境的 bootloader 加壓後載入，我們可以直接調用 agent.py 內部的 _bootstrap 機制。
    # 我們的 agent.py 會自動從本機 /tmp/chess_assets_{PID} 加載，
    # 由於我們沒有打包好 model.zip，它會嘗試在同目錄下找 model.zip。
    # 為了讓 agent 成功 import 本地的 .so，我們已經把當前目錄加到 sys.path，
    # 但 agent.py 在 _bootstrap 時會從 extract_dir 導入。
    # 為了讓本地測試更順利，我們可以先製作一個 model.zip，或者在 Python 中把 .so 複製到 /tmp/chess_assets_{PID}。
    # 我們的 pack.sh 自動會將 macOS 與 Linux 的 .so、book.bin 打包成 model.zip。
    # 只要 pack.sh 運行成功，就會有 model.zip，那 agent.py 就會完美運作！
    
    d6_cpp_dir = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d6_cpp"
    d4_7_dir = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d4_7"
    
    # 確保 model.zip 存在於 d6_cpp_dir 底下
    if not os.path.exists(os.path.join(d6_cpp_dir, "model.zip")):
        print("Warning: model.zip not found. Building it locally for macOS test...")
        # 暫時打包一個給 macOS 本機測試用的 zip 檔
        import zipfile
        with zipfile.ZipFile(os.path.join(d6_cpp_dir, "model.zip"), "w") as z:
            z.write(os.path.join(d6_cpp_dir, "agent.py"), "agent.py")
            z.write(os.path.join(d6_cpp_dir, "model.py"), "model.py")
            # 找到本地 macOS 的 .so 檔並寫入
            for name in os.listdir(d6_cpp_dir):
                if name.startswith("chess_engine") and name.endswith(".so"):
                    z.write(os.path.join(d6_cpp_dir, name), name)
            # 複製一個開局庫當作 book.bin
            z.write("/Users/Shared/西洋棋代理人/Lichess_51_Books/Books/AlPhAbEtACeta.bin", "book.bin")
            print("Temporary model.zip created for local testing.")

    agent_cpp = load_agent(d6_cpp_dir, "d6_cpp_agent")
    agent_py = load_agent(d4_7_dir, "d4_7_agent")

    print("\n=== Agent Battle: D6 C++ (White) vs D4.7 Python (Black) ===")
    run_battle(agent_cpp, agent_py)
    
    print("\n=== Agent Battle: D4.7 Python (White) vs D6 C++ (Black) ===")
    run_battle(agent_py, agent_cpp)

def run_battle(white_agent, black_agent):
    board = chess.Board()
    move_count = 0
    
    white_times = []
    black_times = []
    
    while not board.is_game_over() and move_count < 100:
        obs = make_pettingzoo_obs(board)
        mask = get_action_mask(board)
        
        t0 = time.time()
        if board.turn == chess.WHITE:
            action = white_agent.act(obs, mask)
            dt = time.time() - t0
            white_times.append(dt)
            player_name = "White"
        else:
            action = black_agent.act(obs, mask)
            dt = time.time() - t0
            black_times.append(dt)
            player_name = "Black"
            
        move = action_to_move(board, action)
        if move is None:
            print(f"Error: {player_name} returned illegal action {action}!")
            break
            
        board.push(move)
        move_count += 1
        print(f"Move {move_count:02d}: {player_name} played {move.uci()} (took {dt:.3f}s)")
        
    print(f"\nGame Over! Result: {board.result()}")
    if white_times:
        print(f"White Avg Time: {np.mean(white_times):.3f}s | Max Time: {np.max(white_times):.3f}s")
    if black_times:
        print(f"Black Avg Time: {np.mean(black_times):.3f}s | Max Time: {np.max(black_times):.3f}s")

if __name__ == "__main__":
    main()
