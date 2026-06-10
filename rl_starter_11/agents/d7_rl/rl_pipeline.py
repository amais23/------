import os
import re
import time
import subprocess
import multiprocessing
import chess
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# ═══════════════════════════════════════════
# 系統與訓練超參數配置
# ═══════════════════════════════════════════
NUM_CORES = 10             # 使用全部 10 核心（4 效能 + 6 節能）加速自對弈；每代共 250 局，約是 4 核心的 2.5 倍資料量
GAMES_PER_CORE = 10        # 10 核心每核 10 局，每代共 100 盤，與原 4 核心版本資料量相同但速度快 2.5 倍
GENERATIONS = 4            # 總共進化 4 代
MAX_MOVES_PER_GAME = 120   # 避免無限期對局
SCALE_FACTOR = 4.028981    # 權重放大基準

# ═══════════════════════════════════════════
# 階段 1: Self-Play 工作函數 (在獨立進程中執行)
# ═══════════════════════════════════════════
def worker_self_play(worker_id):
    # 子進程動態載入，確保使用最新編譯的 C++ 模組
    import chess_engine_d7_han as ce

    board = chess.Board()
    engine_w = ce.SearchEngine()
    engine_b = ce.SearchEngine()
    
    # 初始化引擎 (可不傳參數或傳開局庫，這裡預設空)
    engine_w.init("")
    engine_b.init("")
    engine_w.new_game()
    engine_b.new_game()
    
    game_history = []
    
    # 隨機化一些隨機開局庫或初始步，避免每次走一模一樣的棋
    # 在前 4 步白黑方進行隨機合法移動
    for _ in range(4):
        if board.is_game_over():
            break
        moves = list(board.legal_moves)
        board.push(np.random.choice(moves))

    # 用於對戰的 action_mask (固定大小為 4672)
    mask = np.ones(4672, dtype=np.int8)

    while not board.is_game_over() and board.fullmove_number < MAX_MOVES_PER_GAME:
        fen = board.fen()
        
        # 只在 quiet 局面收集資料 (非將軍、非吃子)
        is_quiet = True
        if len(board.move_stack) > 0:
            last_move = board.pop()
            is_capture = board.is_capture(last_move)
            board.push(last_move)
            is_quiet = not board.is_check() and not is_capture
            
        if is_quiet:
            # 只收集 FEN 字串，之後再統一使用 C++ 做批次特徵提取
            game_history.append(fen)

        try:
            # 重建 gym observation 格式 (8, 8, 111)
            obs = fen_to_obs(board)
            
            # 使用目前的 SearchEngine 求解的最佳 move index (0..4671)
            if board.turn == chess.WHITE:
                action = engine_w.solve(obs, mask, -1)
            else:
                action = engine_b.solve(obs, mask, -1)
                
            move = action_to_move(board, action)
            if move in board.legal_moves:
                board.push(move)
            else:
                # 若引擎選出非法步，隨機選一步合法步
                board.push(np.random.choice(list(board.legal_moves)))
        except Exception as e:
            # 捕捉任何搜尋超時或異常，直接中斷
            break

    # 判定勝負結果並給予 reward
    res = board.result()
    if res == "1-0":
        # 白勝，對歷史中的白方局面是 1.0，黑方局面是 0.0
        # 由於特徵提取器 extract_features 提取的特徵是「以白方視角為正」
        # （在 engine.cpp 的特徵向量中：白子為 +1.0，黑子為 -1.0）
        # 所以白勝的盤面，我們對該 FEN 的預測目標就是 1.0 (白勝機率)；黑勝則為 0.0，和棋為 0.5
        reward = 1.0
    elif res == "0-1":
        reward = 0.0
    else:
        reward = 0.5
    
    return [(fen, reward) for fen in game_history]

# ═══════════════════════════════════════════
# 輔助觀測與步轉換函數
# ═══════════════════════════════════════════
import pettingzoo.classic.chess.chess_utils as cu

def fen_to_obs(board):
    """將 chess.Board 轉換為符合 C++ 重建規格 of (8,8,111) 觀測值"""
    obs = np.zeros((8, 8, 111), dtype=np.int8)
    
    # 判斷當前是誰的局，因為觀測空間總是相對於當前玩家的視角
    is_white = (board.turn == chess.WHITE)
    
    # 1. 易位權 (channels 0..3)
    # 相對視角下，頻道 0..1 是當前玩家的易位權，頻道 2..3 是對手的易位權
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
    
    # 2. 棋子擺放 (channels 7..12 當前玩家的棋子, 13..18 對手的棋子)
    # 注意：在 C++ 的 rebuild_fen_from_observation 中：
    # 白子映射順序為 P, N, B, R, Q, K
    # 黑子映射順序為 p, n, b, r, q, k
    # 這裡的 piece_map 對應關係：
    # PAWN=1, KNIGHT=2, BISHOP=3, ROOK=4, QUEEN=5, KING=6 (自 python-chess 模組導入的常數值)
    # 所以我們不能隨意定義 piece_map，必須根據棋子類型常數對應：
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
            # 如果是白棋視角，第 7 橫列 (Rank 8) 對應 row 0，第 0 橫列 (Rank 1) 對應 row 7
            # 如果是黑棋視角，第 0 橫列 (Rank 1) 對應 row 0，第 7 橫列 (Rank 8) 對應 row 7
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
        # 注意：在 C++ 的 rebuild_fen_from_observation 中：
        # 如果 obs(7, col, 7) = 1，表示 row 7 (底線) 有白兵 (這裡表示為白過路兵)
        # 如果 obs(0, col, 13) = 1，表示 row 0 (底線) 有黑兵
        # 對應原本 python-chess 重建代碼：
        # if obs[7, col, 7] -> 在 row 7, col 的過路兵觸發，白方過路兵 (ep_square = col, 2) (a3/b3...)
        # if obs[0, col, 13] -> 在 row 0, col 的過路兵觸發，黑方過路兵 (ep_square = col, 5) (a6/b6...)
        if is_white:
            # 輪到白棋走，過路兵格在黑棋後方 (第 6 橫列，索引 5，如 a6)
            obs[0, ep_col, 13] = 1
        else:
            # 輪到黑棋走，過路兵格在白棋後方 (第 3 橫列，索引 2，如 a3)
            obs[7, ep_col, 7] = 1
            
    return obs


def action_to_move(board, action):
    """將 action index 轉換回 chess.Move 物件"""
    is_white = (board.turn == chess.WHITE)
    for move in board.legal_moves:
        # 如果是黑棋，將絕對著法轉為相對著法以計算正確的 action index
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
    # 預防萬一
    return list(board.legal_moves)[0]

# ═══════════════════════════════════════════
# 階段 2: PyTorch 訓練與特徵提取
# ═══════════════════════════════════════════
class RLDataset(Dataset):
    def __init__(self, data):
        import chess_engine_d7_han as ce
        self.features = []
        self.targets = []
        # 進度顯示
        print("提取局面特徵中...")
        for fen, target in data:
            feat = ce.extract_features(fen)
            self.features.append(feat)
            self.targets.append(target)
            
    def __len__(self): return len(self.targets)
    
    def __getitem__(self, idx):
        return (torch.tensor(self.features[idx], dtype=torch.float32), 
                torch.tensor([self.targets[idx]], dtype=torch.float32))

class LinearEvalModel(nn.Module):
    def __init__(self, initial_weights=None):
        super().__init__()
        # 459 維特徵權重
        self.fc = nn.Linear(459, 1, bias=False)
        
        if initial_weights is not None:
            self.fc.weight.data = torch.tensor(initial_weights, dtype=torch.float32).unsqueeze(0)
        else:
            # 初始化為標準子力值
            with torch.no_grad():
                self.fc.weight.fill_(0.0)
                self.fc.weight[0, 0] = 100.0 / SCALE_FACTOR  # Pawn
                self.fc.weight[0, 1] = 320.0 / SCALE_FACTOR  # Knight
                self.fc.weight[0, 2] = 330.0 / SCALE_FACTOR  # Bishop
                self.fc.weight[0, 3] = 500.0 / SCALE_FACTOR  # Rook
                self.fc.weight[0, 4] = 900.0 / SCALE_FACTOR  # Queen

    def forward(self, x):
        # 預測勝率 MSE 的 Sigmoid 映射
        return torch.sigmoid(self.fc(x) / 400.0)

def train_network(dataset_tuples, initial_weights):
    print(f"啟動 PyTorch 訓練，訓練集大小: {len(dataset_tuples)} FENs...")
    dataset = RLDataset(dataset_tuples)
    dataloader = DataLoader(dataset, batch_size=2048, shuffle=True)
    
    model = LinearEvalModel(initial_weights)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model.to(device)
    
    optimizer = optim.Adam(model.parameters(), lr=0.05)  # 較小的學習率進行微調
    criterion = nn.MSELoss()
    
    model.train()
    for epoch in range(5):  # 微調 5 個 Epoch
        total_loss = 0
        for x, y in dataloader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            pred = model(x)
            loss = criterion(pred, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * x.size(0)
        print(f"  Epoch {epoch+1} Loss: {total_loss/len(dataset):.6f}")
        
    new_weights = model.fc.weight.data.cpu().numpy()[0]
    np.save("FEN_data/latest_rl_weights.npy", new_weights)
    return new_weights

# ═══════════════════════════════════════════
# 階段 3: 自動回填 C++ 原始碼與重新編譯
# ═══════════════════════════════════════════
def update_cpp_and_recompile(raw_weights):
    print("正在將新權重寫回 C++ 並重新編譯...")
    
    # 放大權重
    scaled_w = raw_weights * SCALE_FACTOR
    
    # 解析各參數
    piece_values = np.round(scaled_w[0:5]).astype(int)
    piece_val_str = f"static constexpr int PIECE_VAL[7] = {{{piece_values[0]}, {piece_values[1]}, {piece_values[2]}, {piece_values[3]}, {piece_values[4]}, 20000, 0}};"

    def fmt_array(arr, name):
        rounded = np.round(arr).astype(int)
        lines = []
        for i in range(0, len(rounded), 16):
            chunk = rounded[i:i+16]
            chunk_str = ", ".join(map(str, chunk))
            lines.append("    " + chunk_str)
        inner = ",\n".join(lines)
        return f"static constexpr int16_t {name}[64] = {{\n{inner}}};"

    pst_pawn_str = fmt_array(scaled_w[5:69], "PST_PAWN")
    pst_knight_str = fmt_array(scaled_w[69:133], "PST_KNIGHT")
    pst_bishop_str = fmt_array(scaled_w[133:197], "PST_BISHOP")
    pst_rook_str = fmt_array(scaled_w[197:261], "PST_ROOK")
    pst_queen_str = fmt_array(scaled_w[261:325], "PST_QUEEN")
    pst_king_mid_str = fmt_array(scaled_w[325:389], "PST_KING_MID")
    pst_king_end_str = fmt_array(scaled_w[389:453], "PST_KING_END")

    bp_val = int(round(scaled_w[453]))
    kc_val = int(round(scaled_w[454]))
    ro_val = int(round(scaled_w[455]))
    pp_val = int(round(scaled_w[456]))
    dp_val = int(round(scaled_w[457]))
    ip_val = int(round(scaled_w[458]))

    # 讀取 engine.cpp
    with open("engine.cpp", "r") as f:
        content = f.read()

    # 1. 替換基礎 PIECE_VAL 與 PST 陣列
    start_idx = content.find("static constexpr int PIECE_VAL[7]")
    end_idx = content.find("};", content.find("static constexpr int16_t PST_KING_END[64]"))
    if start_idx == -1 or end_idx == -1:
        print("無法在 engine.cpp 中找到靜態陣列位置！")
        return
    
    end_idx += 2
    old_block = content[start_idx:end_idx]
    
    new_block = "\n".join([
        piece_val_str, "",
        pst_pawn_str, "",
        pst_knight_str, "",
        pst_bishop_str, "",
        pst_rook_str, "",
        pst_queen_str, "",
        pst_king_mid_str, "",
        pst_king_end_str
    ])
    
    content = content.replace(old_block, new_block)

    # 2. 替換特徵評估值常數 (使用 Regex 全域替換原本的數值)
    # Bishop Pair
    content = re.sub(
        r"if \(board\.pieces\(PieceType::BISHOP, Color::WHITE\)\.count\(\) == 2\)\s*score \+=\s*[-]?\d+;",
        f"if (board.pieces(PieceType::BISHOP, Color::WHITE).count() == 2)\n      score += {bp_val};",
        content
    )
    content = re.sub(
        r"if \(board\.pieces\(PieceType::BISHOP, Color::BLACK\)\.count\(\) == 2\)\s*score -=\s*[-]?\d+;",
        f"if (board.pieces(PieceType::BISHOP, Color::BLACK).count() == 2)\n      score -= {bp_val};",
        content
    )

    # King Castled — 分兩步替換，避免在 rf-string 裡嵌套反斜線引號導致 C++ 語法錯誤
    # Step 1: 替換白王分數
    content = re.sub(
        r"(Square ksq_w = board\.kingSq\(Color::WHITE\);\s*if \(ksq_w == Square\(\"c1\"\) \|\| ksq_w == Square\(\"g1\"\) \|\| ksq_w == Square\(\"b1\"\)\)\s*score \+=\s*)[-]?\d+;",
        lambda m: m.group(1) + f"{kc_val};",
        content
    )
    # Step 2: 替換黑王分數
    content = re.sub(
        r"(Square ksq_b = board\.kingSq\(Color::BLACK\);\s*if \(ksq_b == Square\(\"c8\"\) \|\| ksq_b == Square\(\"g8\"\) \|\| ksq_b == Square\(\"b8\"\)\)\s*score -=\s*)[-]?\d+;",
        lambda m: m.group(1) + f"{kc_val};",
        content
    )

    # Rook Open Files
    content = re.sub(
        r"if \(!\(board\.pieces\(PieceType::PAWN, Color::WHITE\)\.getBits\(\) & file_mask\)\) \{\s*score \+=\s*[-]?\d+;\s*\}",
        f"if (!(board.pieces(PieceType::PAWN, Color::WHITE).getBits() & file_mask)) {{\n        score += {ro_val};\n      }}",
        content
    )
    content = re.sub(
        r"if \(!\(board\.pieces\(PieceType::PAWN, Color::BLACK\)\.getBits\(\) & file_mask\)\) \{\s*score -=\s*[-]?\d+;\s*\}",
        f"if (!(board.pieces(PieceType::PAWN, Color::BLACK).getBits() & file_mask)) {{\n        score -= {ro_val};\n      }}",
        content
    )

    # Passed Pawns
    content = re.sub(
        r"if \(!\(pawns_b_bits_v & m_passed_pawn_masks\[0\]\[sq\.index\(\)\]\)\) \{\s*score \+=\s*\d+ \* \(sq\.index\(\) / 8\);\s*\}",
        f"if (!(pawns_b_bits_v & m_passed_pawn_masks[0][sq.index()])) {{\n        score += {pp_val} * (sq.index() / 8);\n      }}",
        content
    )
    content = re.sub(
        r"if \(!\(pawns_w_bits_v & m_passed_pawn_masks\[1\]\[sq\.index\(\)\]\)\) \{\s*score -=\s*\d+ \* \(7 - \(sq\.index\(\) / 8\)\);\s*\}",
        f"if (!(pawns_w_bits_v & m_passed_pawn_masks[1][sq.index()])) {{\n        score -= {pp_val} * (7 - (sq.index() / 8));\n      }}",
        content
    )

    # Doubled & Isolated Pawns
    # 直接用簡單的 replace 整區替換
    old_pawn_structure_pattern = re.compile(
        r"// Doubled pawns.*?// Isolated pawns.*?score -=\s*[-]?\d+;\s*\}", re.DOTALL
    )
    new_pawn_structure = f"""// Doubled pawns
      int count_w = (pawns_w_bits_v & file_mask) ? Bitboard(pawns_w_bits_v & file_mask).count() : 0;
      if (count_w > 1) {{
        score += {dp_val} * (count_w - 1);
      }}
      int count_b = (pawns_b_bits_v & file_mask) ? Bitboard(pawns_b_bits_v & file_mask).count() : 0;
      if (count_b > 1) {{
        score -= {dp_val} * (count_b - 1);
      }}

      // Isolated pawns
      if ((pawns_w_bits_v & file_mask) && !(pawns_w_bits_v & adj_mask)) {{
        score += {ip_val};
      }}
      if ((pawns_b_bits_v & file_mask) && !(pawns_b_bits_v & adj_mask)) {{
        score -= {ip_val};
      }}"""
      
    content = old_pawn_structure_pattern.sub(new_pawn_structure, content)

    # 寫回檔案
    with open("engine.cpp", "w") as f:
        f.write(content)

    # 重新編譯
    print("正在執行 C++ 引擎模組重新編譯...")
    result = subprocess.run(
        ["../../../.venv/bin/python", "setup.py", "build_ext", "--inplace"],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print("❌ 編譯失敗！錯誤資訊如下：")
        print(result.stderr)
        sys.exit(1)
    print("✅ 編譯成功！新一代權重已部署至 chess_engine_d7_han")

# ═══════════════════════════════════════════
# 主管線流程 Orchestrator
# ═══════════════════════════════════════════
if __name__ == "__main__":
    import sys
    # 確保 FEN_data 目錄存在
    os.makedirs("FEN_data", exist_ok=True)
    
    # 優先載入 Gen 1 已儲存的 RL 權重，否則從預訓練基準起點開始
    if os.path.exists("FEN_data/latest_rl_weights.npy"):
        current_weights = np.load("FEN_data/latest_rl_weights.npy")
        start_gen = 2  # Gen 1 已完成自對弈與訓練，從 Gen 2 繼續
        print("載入 latest_rl_weights.npy（Gen 1 完成），從第 2 代繼續 RL 微調。")
    elif os.path.exists("FEN_data/optimized_weights.npy"):
        current_weights = np.load("FEN_data/optimized_weights.npy")
        start_gen = 1
        print("載入 optimized_weights.npy 作為 RL 微調起點。")
    else:
        # 兜底隨機初始化
        current_weights = np.zeros(459, dtype=np.float32)
        current_weights[0:5] = [100.0, 320.0, 330.0, 500.0, 900.0]
        current_weights /= SCALE_FACTOR
        start_gen = 1

    replay_buffer = []

    for gen in range(start_gen, GENERATIONS + 1):
        print(f"\n{'='*60}\n🚀 啟動 RL 自我對弈與進化管線 - 第 {gen} 代 / 共 {GENERATIONS} 代\n{'='*60}")
        
        # Phase 1: Self-Play (多進程)
        start_time = time.time()
        print(f"啟動 {NUM_CORES} 個進程，每個進程跑 {GAMES_PER_CORE} 局對局...")
        
        with multiprocessing.Pool(NUM_CORES) as pool:
            results = pool.map(worker_self_play, range(NUM_CORES * GAMES_PER_CORE))
            
        # 展開所有局面的特徵與對局結果
        gen_data = [item for sublist in results for item in sublist]
        replay_buffer.extend(gen_data)
        
        # 限制 Replay Buffer 大小在 15,000 筆，避免記憶體或計算負擔過重
        if len(replay_buffer) > 15000:
            replay_buffer = replay_buffer[-15000:]
            
        print(f"Self-Play 結束，本代共獲得 {len(gen_data)} 筆 Quiet 盤面，累計 Buffer {len(replay_buffer)} 筆，耗時: {time.time() - start_time:.1f} 秒")
        
        # Phase 2: PyTorch 訓練微調
        current_weights = train_network(replay_buffer, current_weights)
        
        # Phase 3: 自動回填與重新編譯部署
        update_cpp_and_recompile(current_weights)
        
    print("\n🎉 RL 微調管線全部執行完畢！所有權重皆已成功優化並重新部署！")
