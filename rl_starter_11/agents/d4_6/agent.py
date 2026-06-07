"""
ML Arena — Chess Agent: Pure Alpha-Beta Search Engine (Relative Board)
Environment: PettingZoo chess_v6 (2-player)
"""

import time
import zipfile
import os
import numpy as np
import chess
import chess.polyglot
import chess.syzygy
import pettingzoo.classic.chess.chess_utils as cu

BOOK_READER = None
TABLEBASE = None

# ────────────────────────────────────────────────────
# Alpha-Beta Search Engine Configuration
# ────────────────────────────────────────────────────
try:
    from model import SEARCH_DEPTH, PIECE_VALUES, PIECE_SQUARE_TABLES  # 從 model.py 載入所有搜尋設定與評估表
except ImportError:
    from .model import SEARCH_DEPTH, PIECE_VALUES, PIECE_SQUARE_TABLES  # 從 model.py 載入所有搜尋設定與評估表

# ────────────────────────────────────────────────────
# Relative Board Reconstruction Tools
# ────────────────────────────────────────────────────
_PIECES = [
    (7, chess.PAWN), (8, chess.KNIGHT), (9, chess.BISHOP),
    (10, chess.ROOK), (11, chess.QUEEN), (12, chess.KING)
]
_OPP_PIECES = [
    (13, chess.PAWN), (14, chess.KNIGHT), (15, chess.BISHOP),
    (16, chess.ROOK), (17, chess.QUEEN), (18, chess.KING)
]

def _rebuild_relative(obs: np.ndarray) -> chess.Board:
    """從觀察值重建相對棋盤，我方永遠是白方。"""
    if obs[:, :, 7:19].sum() == 0:
        return chess.Board()

    b = chess.Board(fen=None)
    b.clear()
    
    # 重建我方棋子 (白方)
    for ch, pt in _PIECES:
        layer = obs[:, :, ch]
        for r in range(8):
            for c in range(8):
                if layer[r, c]:
                    if pt == chess.PAWN and r == 7:
                        continue
                    b.set_piece_at(chess.square(c, 7 - r), chess.Piece(pt, chess.WHITE))
                    
    # 重建對方棋子 (黑方)
    for ch, pt in _OPP_PIECES:
        layer = obs[:, :, ch]
        for r in range(8):
            for c in range(8):
                if layer[r, c]:
                    if pt == chess.PAWN and r == 0:
                        continue
                    b.set_piece_at(chess.square(c, 7 - r), chess.Piece(pt, chess.BLACK))
                    
    b.turn = chess.WHITE
    
    # 王車易位權限
    cr = 0
    if obs[0, 0, 0]: cr |= chess.BB_H1   # 我方短易位 (相對 H1)
    if obs[0, 0, 1]: cr |= chess.BB_A1   # 我方長易位 (相對 A1)
    if obs[0, 0, 2]: cr |= chess.BB_H8   # 對手短易位 (相對 H8)
    if obs[0, 0, 3]: cr |= chess.BB_A8   # 對手長易位 (相對 A8)
    b.castling_rights = cr
    
    # 處理吃過路兵 (En Passant) 標記
    for col in range(8):
        if obs[7, col, 7]:
            b.set_piece_at(chess.square(col, 3), chess.Piece(chess.PAWN, chess.WHITE))
            b.ep_square = chess.square(col, 2)
            
    for col in range(8):
        if obs[0, col, 13]:
            b.set_piece_at(chess.square(col, 4), chess.Piece(chess.PAWN, chess.BLACK))
            b.ep_square = chess.square(col, 5)
            
    return b

def _m2a(move: chess.Move) -> int:
    """相對 Move 轉為 action index。"""
    col = move.from_square % 8
    row = move.from_square // 8
    return (col * 8 + row) * 73 + cu.get_move_plane(move)

# ────────────────────────────────────────────────────
# Evaluation Function
# ────────────────────────────────────────────────────
PST_KING_END = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50,
]

# ────────────────────────────────────────────────────
# Precomputed Passed Pawn Bitwise Masks
# ────────────────────────────────────────────────────
PASSED_PAWN_MASKS = {chess.WHITE: [0]*64, chess.BLACK: [0]*64}

for sq in range(64):
    f = sq & 7
    r = sq >> 3
    
    # White passed pawn mask (ranks above r, files f-1, f, f+1)
    white_mask = 0
    for file_check in range(max(0, f-1), min(8, f+2)):
        for rank_check in range(r + 1, 8):
            white_mask |= (1 << (rank_check * 8 + file_check))
    PASSED_PAWN_MASKS[chess.WHITE][sq] = white_mask
    
    # Black passed pawn mask (ranks below r, files f-1, f, f+1)
    black_mask = 0
    for file_check in range(max(0, f-1), min(8, f+2)):
        for rank_check in range(0, r):
            black_mask |= (1 << (rank_check * 8 + file_check))
    PASSED_PAWN_MASKS[chess.BLACK][sq] = black_mask

def evaluate_relative_board(board: chess.Board, depth: int = 0) -> int:
    """對相對棋盤進行評估 (我方為白方，分數越高越好)。加入殘局自適應與 Checkmate 距離懲罰。"""
    if board.is_checkmate():
        # 若輪到白方 (我方) 且被將死 -> 極低分 (減去 depth 鼓勵掙扎)；若輪到黑方被將死 -> 極高分 (加上 depth 鼓勵最快將死)
        return -999999 - depth if board.turn == chess.WHITE else 999999 + depth
    if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition(2):
        return 0

    # 計算 Game Phase (0 到 24)，利用 bitboard 位數與位移加速
    knight_count = len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.BLACK))
    bishop_count = len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.BLACK))
    rook_count = len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK))
    queen_count = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
    
    # 用位移與加法計算 phase (Knight=1, Bishop=1, Rook=2, Queen=4)
    phase = knight_count + bishop_count + (rook_count << 1) + (queen_count << 2)
    phase = 24 if phase > 24 else phase
    opp_phase = 24 - phase

    score_pieces = 0
    # 遍歷所有棋子類型與顏色 (基於位元棋盤，極快)
    for pt in (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING):
        val = PIECE_VALUES.get(pt, 0)
        pst_mg = PIECE_SQUARE_TABLES.get(pt)
        pst_eg = PST_KING_END if pt == chess.KING else pst_mg
        
        if pst_mg:
            # 我方棋子 (白方)
            for sq in board.pieces(pt, chess.WHITE):
                idx = (7 - (sq >> 3)) * 8 + (sq & 7)
                val_mg = val + pst_mg[idx]
                val_eg = val + pst_eg[idx]
                score_pieces += val_mg * phase + val_eg * opp_phase
                
            # 對手棋子 (黑方)
            for sq in board.pieces(pt, chess.BLACK):
                idx = (sq >> 3) * 8 + (sq & 7)
                val_mg = val + pst_mg[idx]
                val_eg = val + pst_eg[idx]
                score_pieces -= val_mg * phase + val_eg * opp_phase

    # 使用整數除法代替浮點數除法，只在最後執行一次
    score = score_pieces // 24

    # ────────────────────────────────────────────────────
    # 西洋棋大師戰術評估特徵注入 (Chess Knowledge)
    # ────────────────────────────────────────────────────
    
    # A. 雙主教優勢 (+50)
    if len(board.pieces(chess.BISHOP, chess.WHITE)) == 2:
        score += 50
    if len(board.pieces(chess.BISHOP, chess.BLACK)) == 2:
        score -= 50

    # B. 國王易位安全獎勵 (+30)
    if board.king(chess.WHITE) in (chess.C1, chess.G1, chess.B1):
        score += 30
    if board.king(chess.BLACK) in (chess.C8, chess.G8, chess.B8):
        score -= 30

    # C. 車佔開直列/半開直列 (+20)
    for sq in board.pieces(chess.ROOK, chess.WHITE):
        f = sq & 7
        white_pawns_on_file = board.pieces(chess.PAWN, chess.WHITE) & chess.BB_FILES[f]
        if not white_pawns_on_file: # 至少是半開檔
            score += 20
            
    for sq in board.pieces(chess.ROOK, chess.BLACK):
        f = sq & 7
        black_pawns_on_file = board.pieces(chess.PAWN, chess.BLACK) & chess.BB_FILES[f]
        if not black_pawns_on_file: # 至少是半開檔
            score -= 20

    # D. 通路兵加分 (Passed Pawns) - 完全消滅巢狀迴圈，改用極速的位元與運算
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)
    for sq in board.pieces(chess.PAWN, chess.WHITE):
        if not (black_pawns & PASSED_PAWN_MASKS[chess.WHITE][sq]):
            score += 10 * (sq >> 3)

    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    for sq in board.pieces(chess.PAWN, chess.BLACK):
        if not (white_pawns & PASSED_PAWN_MASKS[chess.BLACK][sq]):
            score -= 10 * (7 - (sq >> 3))

    return score

# ────────────────────────────────────────────────────
# Minimax with Alpha-Beta Pruning
# ────────────────────────────────────────────────────
def _get_move_score(board: chess.Board, move: chess.Move) -> int:
    """MVV-LVA 步法評分：吃子與升變優先。"""
    if move.promotion:
        return 15000
    if board.is_capture(move):
        victim_type = board.piece_type_at(move.to_square)
        victim_val = PIECE_VALUES.get(victim_type, 100) if victim_type else 100
        attacker_type = board.piece_type_at(move.from_square)
        attacker_val = PIECE_VALUES.get(attacker_type, 100) if attacker_type else 100
        return 10000 + victim_val - (attacker_val // 10)
    return 0

class SearchTimeout(Exception):
    """自訂異常，用於搜尋超時時立即中斷。"""
    pass

_SEARCH_START_TIME = 0.0
_SEARCH_TIME_LIMIT = 999999.0

# 置換表：{zobrist_hash: (depth, score, flag, best_move)}
# flag: 0=EXACT, 1=ALPHA (Upper Bound), 2=BETA (Lower Bound)
TT = {}
TT_MAX_SIZE = 5000000

FLAG_EXACT = 0
FLAG_ALPHA = 1
FLAG_BETA  = 2

# 殺手著法：{depth: [killer_1, killer_2]}
KILLER_MOVES = [[None, None] for _ in range(64)]

# 歷史啟發式表格：[from_square][to_square]
HISTORY_TABLE = [[0] * 64 for _ in range(64)]

# 節點計數器
NODE_COUNT = 0

def _has_major_pieces(board: chess.Board, color: chess.Color) -> bool:
    """檢查某方是否還有大子 (非兵、非王) 以免在殘局因 Zugzwang 誤判。"""
    for pt in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        if board.pieces(pt, color):
            return True
    return False

def quiescence_minimax(board: chess.Board, alpha: int, beta: int, maximizing: bool, qdepth: int = 0) -> int:
    """靜態搜尋：在搜尋深度用盡後繼續搜尋吃子步，直到局面安靜。"""
    global NODE_COUNT
    NODE_COUNT += 1
    if NODE_COUNT & 2047 == 0:
        if time.time() - _SEARCH_START_TIME > _SEARCH_TIME_LIMIT:
            raise SearchTimeout()

    if qdepth > 4 or board.is_game_over():
        return evaluate_relative_board(board, 0)

    stand_pat = evaluate_relative_board(board, 0)

    if maximizing:
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
        
        captures = list(board.generate_legal_captures())
        captures.sort(key=lambda m: _get_move_score(board, m), reverse=True)
        
        for move in captures:
            # Delta Pruning (增量剪枝)
            if not move.promotion:
                victim_type = board.piece_type_at(move.to_square)
                victim_val = PIECE_VALUES.get(victim_type, 100) if victim_type else 100
                if stand_pat + victim_val + 200 < alpha:
                    continue

            board.push(move)
            try:
                score = quiescence_minimax(board, alpha, beta, False, qdepth + 1)
            finally:
                board.pop()
            
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        return alpha
    else:
        if stand_pat <= alpha:
            return alpha
        beta = min(beta, stand_pat)
        
        captures = list(board.generate_legal_captures())
        captures.sort(key=lambda m: _get_move_score(board, m), reverse=True)
        
        for move in captures:
            # Delta Pruning (增量剪枝)
            if not move.promotion:
                victim_type = board.piece_type_at(move.to_square)
                victim_val = PIECE_VALUES.get(victim_type, 100) if victim_type else 100
                if stand_pat - victim_val - 200 > beta:
                    continue

            board.push(move)
            try:
                score = quiescence_minimax(board, alpha, beta, True, qdepth + 1)
            finally:
                board.pop()
            
            if score <= alpha:
                return alpha
            beta = min(beta, score)
        return beta

# 💡 修改函數簽名，加入 search_history
def alpha_beta(board: chess.Board, depth: int, alpha: int, beta: int, maximizing: bool, extensions: int = 0, search_history = None) -> int:
    global NODE_COUNT
    NODE_COUNT += 1
    if NODE_COUNT & 2047 == 0:
        if time.time() - _SEARCH_START_TIME > _SEARCH_TIME_LIMIT:
            raise SearchTimeout()
        
    key = chess.polyglot.zobrist_hash(board)

    # 💡 0. 升級版重複局面偵測：結合真實歷史與模擬路徑
    if search_history is not None and search_history.get(key, 0) >= 2:
        return 0

    # 1. 查詢置換表 (Transposition Table)
    tt_entry = TT.get(key)
    if tt_entry and tt_entry[0] >= depth:
        tt_depth, tt_score, tt_flag, tt_move = tt_entry
        if tt_flag == FLAG_EXACT:
            return tt_score
        elif tt_flag == FLAG_BETA and tt_score >= beta:
            return tt_score
        elif tt_flag == FLAG_ALPHA and tt_score <= alpha:
            return tt_score

    # 2. 終局與葉節點處理
    if board.is_game_over():
        return evaluate_relative_board(board, depth)
        
    is_check = board.is_check()
    
    if depth <= 0:
        if is_check and extensions < 3: # 將軍延展
            depth += 1
            extensions += 1
        else:
            # 💡 靜態搜尋通常不涉及長距離重複，直接計算即可
            return quiescence_minimax(board, alpha, beta, maximizing)

    original_alpha = alpha
    original_beta = beta

    # 3. 空步剪枝 (Null Move Pruning)
    # 💡 注意：Null Move 會改變 turn 導致 Hash 不同，不影響重複判定，維持原樣即可
    R = 2
    if depth >= R + 1 and not is_check and _has_major_pieces(board, board.turn):
        board.push(chess.Move.null())
        try:
            val = alpha_beta(board, depth - 1 - R, alpha, beta, not maximizing, extensions, search_history)
        finally:
            board.pop()
        if maximizing:
            if val >= beta:
                return beta
        else:
            if val <= alpha:
                return alpha

    # 4. 著法生成與排序
    legal_moves = list(board.legal_moves)
    
    def get_sort_score(m):
        score = _get_move_score(board, m)
        if score == 0 and depth < 64:  # 非吃子/升變
            if m == KILLER_MOVES[depth][0]: return 9000
            elif m == KILLER_MOVES[depth][1]: return 8000
            # 加入歷史啟發分數排序
            return min(HISTORY_TABLE[m.from_square][m.to_square], 7000)
        return score
        
    legal_moves.sort(key=get_sort_score, reverse=True)
    
    # TT 最佳步優先
    if tt_entry and tt_entry[3] is not None and tt_entry[3] in legal_moves:
        legal_moves.remove(tt_entry[3])
        legal_moves.insert(0, tt_entry[3])

    # 💡 在開始走訪子節點前，將當前節點記入 search_history 模擬路徑
    if search_history is not None:
        search_history[key] = search_history.get(key, 0) + 1

    best_move = None
    try:
        if maximizing:
            max_eval = -9999999
            for i, move in enumerate(legal_moves):
                board.push(move)
                try:
                    is_quiet = not board.is_capture(move) and not move.promotion
                    move_is_check = board.is_check()
                    ext = 1 if move_is_check and extensions < 3 else 0
                    new_depth = depth - 1 + ext
                    new_ext = extensions + ext
                    
                    # Late Move Reductions (LMR)
                    if new_depth >= 3 and i >= 3 and is_quiet and not move_is_check and not is_check:
                        val = alpha_beta(board, new_depth - 1, alpha, beta, False, new_ext, search_history)
                        if val > alpha:
                            val = alpha_beta(board, new_depth, alpha, beta, False, new_ext, search_history)
                    else:
                        val = alpha_beta(board, new_depth, alpha, beta, False, new_ext, search_history)
                finally:
                    board.pop()
                
                if val > max_eval:
                    max_eval = val
                    best_move = move
                alpha = max(alpha, val)
                if beta <= alpha:
                    if is_quiet and depth < 64:
                        if move != KILLER_MOVES[depth][0]:
                            KILLER_MOVES[depth][1] = KILLER_MOVES[depth][0]
                            KILLER_MOVES[depth][0] = move
                        # 更新歷史啟發式表格
                        HISTORY_TABLE[move.from_square][move.to_square] += depth * depth
                    break
            
            # 儲存至置換表
            if len(TT) < TT_MAX_SIZE:
                flag = FLAG_ALPHA if max_eval <= original_alpha else (FLAG_BETA if max_eval >= beta else FLAG_EXACT)
                TT[key] = (depth, max_eval, flag, best_move)
            return max_eval
        else:
            min_eval = 9999999
            for i, move in enumerate(legal_moves):
                board.push(move)
                try:
                    is_quiet = not board.is_capture(move) and not move.promotion
                    move_is_check = board.is_check()
                    ext = 1 if move_is_check and extensions < 3 else 0
                    new_depth = depth - 1 + ext
                    new_ext = extensions + ext
                    
                    if new_depth >= 3 and i >= 3 and is_quiet and not move_is_check and not is_check:
                        val = alpha_beta(board, new_depth - 1, alpha, beta, True, new_ext, search_history)
                        if val < beta: # 淺搜若成功，重新完整搜尋
                            val = alpha_beta(board, new_depth, alpha, beta, True, new_ext, search_history)
                    else:
                        val = alpha_beta(board, new_depth, alpha, beta, True, new_ext, search_history)
                finally:
                    board.pop()
                
                if val < min_eval:
                    min_eval = val
                    best_move = move
                beta = min(beta, val)
                if beta <= alpha:
                    # 記錄殺手著法
                    if is_quiet and depth < 64:
                        if move != KILLER_MOVES[depth][0]:
                            KILLER_MOVES[depth][1] = KILLER_MOVES[depth][0]
                            KILLER_MOVES[depth][0] = move
                        # 更新歷史啟發式表格
                        HISTORY_TABLE[move.from_square][move.to_square] += depth * depth
                    break
            
            # 儲存至置換表
            if len(TT) < TT_MAX_SIZE:
                flag = FLAG_ALPHA if min_eval <= alpha else (FLAG_BETA if min_eval >= original_beta else FLAG_EXACT)
                TT[key] = (depth, min_eval, flag, best_move)
            return min_eval

    finally:
        # 💡 關鍵：無論搜尋是正常結束還是觸發剪枝，回溯時一定要將當前節點移出模擬路徑
        if search_history is not None:
            search_history[key] -= 1
            if search_history[key] == 0:
                del search_history[key]

def search_best_move(board: chess.Board, max_depth: int, time_limit: float = 4.5, my_real_color = chess.WHITE, search_history = None) -> chess.Move:
    """在當前棋盤狀態下尋找最佳著法 (我方永遠是白方，因此我們必定是 maximizing)。"""
    global _SEARCH_START_TIME, _SEARCH_TIME_LIMIT, NODE_COUNT
    _SEARCH_START_TIME = time.time()
    NODE_COUNT = 0
    
    # 清空歷史啟發式表
    global HISTORY_TABLE
    for f in range(64):
        for t in range(64):
            HISTORY_TABLE[f][t] = 0

    # 0. 查詢開局庫
    if BOOK_READER:
        try:
            if my_real_color == chess.BLACK:
                # 建立絕對棋盤進行開局庫查詢 (對調白黑顏色並垂直翻轉)
                abs_board = chess.Board(fen=None)
                abs_board.clear()
                # 遍歷優化
                for pt in (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING):
                    for sq in board.pieces(pt, chess.WHITE):
                        abs_board.set_piece_at(sq ^ 56, chess.Piece(pt, chess.BLACK))
                    for sq in board.pieces(pt, chess.BLACK):
                        abs_board.set_piece_at(sq ^ 56, chess.Piece(pt, chess.WHITE))
                abs_board.turn = chess.BLACK
                cr = 0
                if board.castling_rights & chess.BB_H1: cr |= chess.BB_H8
                if board.castling_rights & chess.BB_A1: cr |= chess.BB_A8
                if board.castling_rights & chess.BB_H8: cr |= chess.BB_H1
                if board.castling_rights & chess.BB_A8: cr |= chess.BB_A1
                abs_board.castling_rights = cr
                if board.ep_square is not None:
                    abs_board.ep_square = board.ep_square ^ 56
                
                entry = BOOK_READER.weighted_choice(abs_board)
                if entry:
                    abs_move = entry.move
                    # 轉回黑方的相對 move
                    return chess.Move(
                        from_square=abs_move.from_square ^ 56,
                        to_square=abs_move.to_square ^ 56,
                        promotion=abs_move.promotion
                    )
            else:
                entry = BOOK_READER.weighted_choice(board)
                return entry.move
        except IndexError:
            pass # 沒有對應的開局庫著法
            
    # 0.5 查詢殘局庫 (Syzygy Tablebases)
    if TABLEBASE and board.occupied.bit_count() <= 4:
        try:
            best_tb_move = None
            best_tb_score = -999999999
            for move in board.legal_moves:
                board.push(move)
                try:
                    wdl = -TABLEBASE.probe_wdl(board)
                    try:
                        dtz = -TABLEBASE.probe_dtz(board)
                    except Exception:
                        dtz = 0
                    
                    # 判斷重複局面 (重複 3 次即判和)
                    new_key = chess.polyglot.zobrist_hash(board)
                    rep_count = search_history.get(new_key, 0) if search_history is not None else 0
                    
                    # 結合正常評估函數，避免無謂犧牲大子
                    normal_eval = evaluate_relative_board(board)
                finally:
                    board.pop()
                
                # 如果該步導致重複 3 次 (rep_count >= 2)，在此平台規則下強制視為和局 (WDL = 0, DTZ = 0)
                # 這可以實現：勝勢下「一票否決」避免和局；敗勢下「強行判和」起死回生
                if rep_count >= 2:
                    wdl = 0
                    dtz = 0
                
                # 基礎得分
                score = wdl * 10000000 + normal_eval * 100
                
                # 距離零著點 (DTZ) 調整
                if wdl > 0:
                    score -= abs(dtz)
                elif wdl < 0:
                    score += abs(dtz)
                
                # 輕微懲罰已經出現過一次的局面 (rep_count == 1)，避免無謂踱步，但仍保留為備選
                if rep_count == 1:
                    score -= 500000
                
                if score > best_tb_score:
                    best_tb_score = score
                    best_tb_move = move
                    
            if best_tb_move:
                return best_tb_move
        except chess.syzygy.MissingTableError:
            pass
            
    # 動態時間分配 (Dynamic Time Allocation) - 針對 600s/20場 的極限賽制
    # 遍歷優化計算 phase
    phase = (
        len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.BLACK)) +
        len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.BLACK)) +
        len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK)) +
        len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
    )
    if phase >= 8:      # 中局前期
        _SEARCH_TIME_LIMIT = 1.5
    elif phase >= 4:    # 中局後期
        _SEARCH_TIME_LIMIT = 0.8
    else:               # 殘局
        _SEARCH_TIME_LIMIT = 0.4
        
    # 保險機制：不超過環境給定的 time_limit
    _SEARCH_TIME_LIMIT = min(_SEARCH_TIME_LIMIT, time_limit)
    
    best_move = None
    
    try:
        for depth in range(1, max_depth + 1):
            current_best = None
            current_best_val = -9999999
            
            legal_moves = list(board.legal_moves)
            legal_moves.sort(key=lambda m: _get_move_score(board, m), reverse=True)
            
            # TT 最佳步優先
            key = chess.polyglot.zobrist_hash(board)
            tt_entry = TT.get(key)
            if tt_entry and tt_entry[3] is not None and tt_entry[3] in legal_moves:
                legal_moves.remove(tt_entry[3])
                legal_moves.insert(0, tt_entry[3])
                
            for move in legal_moves:
                # 每次搜尋前先檢查時間，避免無謂搜尋
                if time.time() - _SEARCH_START_TIME > _SEARCH_TIME_LIMIT:
                    raise SearchTimeout()
                
                board.push(move)
                try:
                    val = alpha_beta(board, depth - 1, -9999999, 9999999, False, extensions=0, search_history=search_history)
                finally:
                    board.pop()
                if val > current_best_val:
                    current_best_val = val
                    current_best = move
            
            # 完整搜完此深度才更新最佳步
            best_move = current_best
            
    except SearchTimeout:
        pass
        
    # 如果第一層都沒搜完，則保證回傳至少一個合法著法
    if best_move is None:
        if board.legal_moves:
            best_move = list(board.legal_moves)[0]
            
    return best_move

# ────────────────────────────────────────────────────
# Agent Interface
# ────────────────────────────────────────────────────
class Agent:
    def __init__(self):
        self.depth = SEARCH_DEPTH
        self.my_real_color = None
        self.real_game_history = {}  # 💡 新增：記錄真實對局的 Zobrist Hash 次數
        self.previous_board = None   # 💡 用於安全地偵測新對局起點
        TT.clear()  # 每局開始時清空置換表
        for i in range(64):
            KILLER_MOVES[i] = [None, None]
            
        global BOOK_READER, TABLEBASE
        if BOOK_READER is None or TABLEBASE is None:
            if os.path.exists("model.zip"):
                try:
                    with zipfile.ZipFile("model.zip", 'r') as zip_ref:
                        zip_ref.extractall("/tmp")
                    
                    if os.path.exists("/tmp/book.bin"):
                        BOOK_READER = chess.polyglot.open_reader("/tmp/book.bin")
                        print("✅ Successfully loaded PolyGlot book from model.zip")
                        
                    if os.path.exists("/tmp/syzygy") and os.path.isdir("/tmp/syzygy"):
                        TABLEBASE = chess.syzygy.open_tablebase("/tmp/syzygy")
                        print("✅ Successfully loaded Syzygy tablebases from model.zip")
                except Exception as e:
                    print(f"⚠️ Failed to load book/tablebases: {e}")

    def act(self, observation: np.ndarray, action_mask: np.ndarray) -> int:
        try:
            # 1. 重建相對棋盤
            board = _rebuild_relative(observation)

            # 💡 判斷新局重置與清理 (取代有陷阱的 board.fullmove_number)
            is_new_game = False
            if self.my_real_color is None:
                is_new_game = True
            else:
                piece_count = board.occupied.bit_count()
                prev_piece_count = self.previous_board.occupied.bit_count() if self.previous_board is not None else 32
                if board == chess.Board() or piece_count > prev_piece_count:
                    is_new_game = True

            if is_new_game:
                self.real_game_history.clear()
                self.previous_board = None
                if board == chess.Board():
                    self.my_real_color = chess.WHITE
                else:
                    self.my_real_color = chess.BLACK

            self.previous_board = board.copy()
            TT.clear()  # 💡 確保每回合開始搜尋前清空置換表，徹底防止跨回合與重複局面的 TT 快取污染

            # 💡 紀錄當前真實對局的局面
            current_hash = chess.polyglot.zobrist_hash(board)
            self.real_game_history[current_hash] = self.real_game_history.get(current_hash, 0) + 1

            # 💡 將真實歷史複製一份，傳入搜尋引擎
            search_history = self.real_game_history.copy()

            # 2. 搜尋最佳著法
            best_move = search_best_move(board, self.depth, time_limit=4.5, my_real_color=self.my_real_color, search_history=search_history)

            # 3. 轉回 action index
            if best_move is not None:
                # 💡 紀錄我方下完棋後的局面 (此時為對手的 turn)，確保對手回合的 Hash 也被完整紀錄
                board.push(best_move)
                after_move_hash = chess.polyglot.zobrist_hash(board)
                self.real_game_history[after_move_hash] = self.real_game_history.get(after_move_hash, 0) + 1
                board.pop()
                
                action = _m2a(best_move)
                if 0 <= action < 4672 and action_mask[action] == 1:
                    return int(action)

            # 4. Fallback: 隨機合法步 (理論上不會觸發，除非無合法步)
            legal = np.where(action_mask == 1)[0]
            return int(np.random.choice(legal)) if len(legal) else 0

        except Exception:
            # 發生任何錯誤時降級為隨機合法步
            legal = np.where(action_mask == 1)[0]
            return int(np.random.choice(legal)) if len(legal) else 0
