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
import concurrent.futures
import multiprocessing

try:
    CPU_CORES = multiprocessing.cpu_count()
except:
    CPU_CORES = 1

WORKER_COUNT = max(1, CPU_CORES - 1)
_EXECUTOR = None

def get_executor():
    global _EXECUTOR
    if _EXECUTOR is None and WORKER_COUNT > 1:
        _EXECUTOR = concurrent.futures.ProcessPoolExecutor(max_workers=WORKER_COUNT)
    return _EXECUTOR

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

def evaluate_relative_board(board: chess.Board, depth: int = 0) -> int:
    """對相對棋盤進行評估 (我方為白方，分數越高越好)。加入殘局自適應與 Checkmate 距離懲罰。"""
    if board.is_checkmate():
        # 若輪到白方 (我方) 且被將死 -> 極低分 (減去 depth 鼓勵掙扎)；若輪到黑方被將死 -> 極高分 (加上 depth 鼓勵最快將死)
        return -999999 - depth if board.turn == chess.WHITE else 999999 + depth
    if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition(2):
        return 0

    # 計算 Game Phase (0 到 24)
    phase = 0
    for sq, piece in board.piece_map().items():
        pt = piece.piece_type
        if pt == chess.KNIGHT or pt == chess.BISHOP: phase += 1
        elif pt == chess.ROOK: phase += 2
        elif pt == chess.QUEEN: phase += 4
    
    phase = min(phase, 24)
    mg_weight = phase / 24.0
    eg_weight = 1.0 - mg_weight

    score = 0
    for sq, piece in board.piece_map().items():
        pt = piece.piece_type
        val = PIECE_VALUES.get(pt, 0)
        
        pst_mg = PIECE_SQUARE_TABLES.get(pt)
        pst_eg = pst_mg
        if pt == chess.KING:
            pst_eg = PST_KING_END

        if pst_mg:
            if piece.color == chess.WHITE:
                idx = (7 - chess.square_rank(sq)) * 8 + chess.square_file(sq)
                val_mg = val + pst_mg[idx]
                val_eg = val + pst_eg[idx]
            else:
                idx = chess.square_rank(sq) * 8 + chess.square_file(sq)
                val_mg = val + pst_mg[idx]
                val_eg = val + pst_eg[idx]
            
            final_val = val_mg * mg_weight + val_eg * eg_weight
            score += final_val if piece.color == chess.WHITE else -final_val

    return int(score)

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

def _has_major_pieces(board: chess.Board, color: chess.Color) -> bool:
    """檢查某方是否還有大子 (非兵、非王) 以免在殘局因 Zugzwang 誤判。"""
    for pt in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        if board.pieces(pt, color):
            return True
    return False

def quiescence_minimax(board: chess.Board, alpha: int, beta: int, maximizing: bool, qdepth: int = 0) -> int:
    """靜態搜尋：在搜尋深度用盡後繼續搜尋吃子步，直到局面安靜。"""
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
            score = quiescence_minimax(board, alpha, beta, False, qdepth + 1)
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
            score = quiescence_minimax(board, alpha, beta, True, qdepth + 1)
            board.pop()
            
            if score <= alpha:
                return alpha
            beta = min(beta, score)
        return beta

def alpha_beta(board: chess.Board, depth: int, alpha: int, beta: int, maximizing: bool, extensions: int = 0, search_history = None) -> int:
    if time.time() - _SEARCH_START_TIME > _SEARCH_TIME_LIMIT:
        raise SearchTimeout()
        
    key = chess.polyglot.zobrist_hash(board)

    # 💡 0. 升級版重複局面偵測：結合真實歷史與模擬路徑
    if search_history is not None and search_history.get(key, 0) >= 2:
        return 0

    # 1. 查詢置換表
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
            return quiescence_minimax(board, alpha, beta, maximizing)

    original_alpha = alpha
    original_beta = beta

    # 3. 空步剪枝 (Null Move Pruning)
    R = 2
    if depth >= R + 1 and not is_check and _has_major_pieces(board, board.turn):
        board.push(chess.Move.null())
        val = alpha_beta(board, depth - 1 - R, alpha, beta, not maximizing, extensions, search_history)
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
                
                is_quiet = not board.is_capture(move) and not move.promotion
                
                move_is_check = board.is_check()
                ext = 1 if move_is_check and extensions < 3 else 0
                new_depth = depth - 1 + ext
                new_ext = extensions + ext
                
                # Late Move Reductions (LMR)
                if new_depth >= 3 and i >= 3 and is_quiet and not move_is_check and not is_check:
                    val = alpha_beta(board, new_depth - 1, alpha, beta, False, new_ext, search_history)
                    if val > alpha: # 淺搜若成功，重新完整搜尋
                        val = alpha_beta(board, new_depth, alpha, beta, False, new_ext, search_history)
                else:
                    val = alpha_beta(board, new_depth, alpha, beta, False, new_ext, search_history)
                    
                board.pop()
                
                if val > max_eval:
                    max_eval = val
                    best_move = move
                alpha = max(alpha, val)
                if beta <= alpha:
                    # 記錄殺手著法
                    if is_quiet and depth < 64:
                        if move != KILLER_MOVES[depth][0]:
                            KILLER_MOVES[depth][1] = KILLER_MOVES[depth][0]
                            KILLER_MOVES[depth][0] = move
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
                
                is_quiet = not board.is_capture(move) and not move.promotion
                
                move_is_check = board.is_check()
                ext = 1 if move_is_check and extensions < 3 else 0
                new_depth = depth - 1 + ext
                new_ext = extensions + ext
                
                # Late Move Reductions (LMR)
                if new_depth >= 3 and i >= 3 and is_quiet and not move_is_check and not is_check:
                    val = alpha_beta(board, new_depth - 1, alpha, beta, True, new_ext, search_history)
                    if val < beta: # 淺搜若成功，重新完整搜尋
                        val = alpha_beta(board, new_depth, alpha, beta, True, new_ext, search_history)
                else:
                    val = alpha_beta(board, new_depth, alpha, beta, True, new_ext, search_history)
                    
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
                    break
            
            # 儲存至置換表
            if len(TT) < TT_MAX_SIZE:
                flag = FLAG_ALPHA if min_eval <= alpha else (FLAG_BETA if min_eval >= original_beta else FLAG_EXACT)
                TT[key] = (depth, min_eval, flag, best_move)
            return min_eval
    finally:
        # 💡 關鍵：無論搜尋是正常結束還是觸發剪枝，回溯時一定要將當前節節點移出模擬路徑
        if search_history is not None:
            search_history[key] -= 1
            if search_history[key] == 0:
                del search_history[key]

def worker_evaluate(fen: str, move_uci: str, depth: int, alpha: int, beta: int, time_limit: float, search_history = None) -> tuple:
    """供 ProcessPoolExecutor 使用的工作函式。"""
    global _SEARCH_START_TIME, _SEARCH_TIME_LIMIT
    _SEARCH_START_TIME = time.time()
    _SEARCH_TIME_LIMIT = time_limit
    
    board = chess.Board(fen)
    move = chess.Move.from_uci(move_uci)
    board.push(move)
    
    try:
        # 由於此引擎設定為相對於白方，worker_evaluate 總是被主進程以 maximizing=True 呼叫
        # 因此，當我們模擬走完一步後，下一層是 maximizing=False
        val = alpha_beta(board, depth - 1, alpha, beta, False, extensions=0, search_history=search_history)
    except SearchTimeout:
        val = -9999999
        
    return (move_uci, val)

def search_best_move(board: chess.Board, max_depth: int, time_limit: float = 4.5, disable_parallel: bool = False, my_real_color = chess.WHITE, search_history = None) -> chess.Move:
    """在當前棋盤狀態下尋找最佳著法 (我方永遠是白方，因此我們必定是 maximizing)。"""
    global _SEARCH_START_TIME, _SEARCH_TIME_LIMIT
    _SEARCH_START_TIME = time.time()
    
    # 0. 查詢開局庫
    if BOOK_READER:
        try:
            if my_real_color == chess.BLACK:
                # 建立絕對棋盤進行開局庫查詢 (對調白黑顏色並垂直翻轉)
                abs_board = chess.Board(fen=None)
                abs_board.clear()
                for sq, piece in board.piece_map().items():
                    abs_board.set_piece_at(sq ^ 56, chess.Piece(piece.piece_type, not piece.color))
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
    if TABLEBASE and len(board.piece_map()) <= 4:
        try:
            best_tb_move = None
            best_tb_score = -9999999
            for move in board.legal_moves:
                board.push(move)
                wdl = -TABLEBASE.probe_wdl(board)
                dtz = -TABLEBASE.probe_dtz(board)
                board.pop()
                
                score = wdl * 10000
                if wdl > 0: score -= abs(dtz) # 贏：步數越少越好
                elif wdl < 0: score += abs(dtz) # 輸：步數越多越好
                
                if score > best_tb_score:
                    best_tb_score = score
                    best_tb_move = move
                    
            if best_tb_move:
                return best_tb_move
        except chess.syzygy.MissingTableError:
            pass
            
    # 動態時間分配 (Dynamic Time Allocation) - 配合伺服器 60 秒 / 局 的限制
    # 假設平均一局 40 步，我們平均每步只能思考 1.5 秒
    phase = sum(1 for pt in board.piece_map().values() if pt.piece_type != chess.PAWN and pt.piece_type != chess.KING)
    if phase >= 8:      # 中局前期 (變化最多，最需要深搜)
        _SEARCH_TIME_LIMIT = 1.0
    elif phase >= 4:    # 中局後期
        _SEARCH_TIME_LIMIT = 0.8
    else:               # 殘局
        _SEARCH_TIME_LIMIT = 0.5
        
    # 保險機制：不超過環境給定的 time_limit (或伺服器的 15 秒硬限制)
    _SEARCH_TIME_LIMIT = min(_SEARCH_TIME_LIMIT, time_limit)
    
    best_move = None
    
    executor = get_executor()
    
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
                
            if not legal_moves:
                break
                
            # --- 主變異分割 (Root PVS 平行化) ---
            # 1. 於主執行緒同步搜尋第一步 (Move Ordering 後最有潛力的一步)，取得極佳的 Alpha 下界
            first_move = legal_moves[0]
            board.push(first_move)
            alpha = alpha_beta(board, depth - 1, -9999999, 9999999, False, extensions=0, search_history=search_history)
            board.pop()
            
            current_best_val = alpha
            current_best = first_move
            
            # 2. 將剩下的合法步交給 ProcessPool 平行搜尋
            candidate_moves = legal_moves[1:]
            
            if candidate_moves and executor is not None and depth >= 3 and not disable_parallel:
                # 只有深度夠深時，平行化才有意義 (太淺的搜尋，進程切換成本高於搜尋成本)
                fen = board.fen()
                time_rem = _SEARCH_TIME_LIMIT - (time.time() - _SEARCH_START_TIME)
                if time_rem <= 0:
                    raise SearchTimeout()
                    
                futures = []
                for m in candidate_moves:
                    f = executor.submit(worker_evaluate, fen, m.uci(), depth, alpha, 9999999, time_rem, search_history)
                    futures.append((m, f))
                
                # 收集結果
                for m, f in futures:
                    # 動態更新剩餘時間，避免時間洩漏
                    time_rem = _SEARCH_TIME_LIMIT - (time.time() - _SEARCH_START_TIME)
                    if time_rem <= 0:
                        raise SearchTimeout()
                    try:
                        _, val = f.result(timeout=time_rem)
                        if val > current_best_val:
                            current_best_val = val
                            current_best = m
                            alpha = max(alpha, current_best_val)
                    except (concurrent.futures.TimeoutError, SearchTimeout):
                        raise SearchTimeout()
            else:
                # 若無法平行處理或深度太淺，則序列處理
                for move in candidate_moves:
                    if time.time() - _SEARCH_START_TIME > _SEARCH_TIME_LIMIT:
                        raise SearchTimeout()
                    board.push(move)
                    val = alpha_beta(board, depth - 1, alpha, 9999999, False, extensions=0, search_history=search_history)
                    board.pop()
                    if val > current_best_val:
                        current_best_val = val
                        current_best = move
                        alpha = max(alpha, current_best_val)
            
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
        self.fallback_triggered = False
        self.my_real_color = None
        self.real_game_history = {}  # 💡 新增：記錄真實對局的 Zobrist Hash 次數
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

            # 判定我方真實顏色與新局重置
            if self.my_real_color is None:
                self.real_game_history.clear() # 💡 確保新局開始時清空
                if board == chess.Board():
                    self.my_real_color = chess.WHITE
                else:
                    self.my_real_color = chess.BLACK
            elif board.fullmove_number == 1: # 💡 如果回到第一步，代表新的一局開始了
                self.real_game_history.clear()

            # 💡 紀錄當前真實對局的局面
            current_hash = chess.polyglot.zobrist_hash(board)
            self.real_game_history[current_hash] = self.real_game_history.get(current_hash, 0) + 1

            # 💡 將真實歷史複製一份，傳入搜尋引擎
            search_history = self.real_game_history.copy()

            # 2. 搜尋最佳著法
            best_move = search_best_move(board, self.depth, time_limit=4.5, disable_parallel=self.fallback_triggered, my_real_color=self.my_real_color, search_history=search_history)

            # 3. 轉回 action index
            if best_move is not None:
                action = _m2a(best_move)
                if 0 <= action < 4672 and action_mask[action] == 1:
                    return int(action)

            # 4. Fallback: 隨機合法步 (理論上不會觸發，除非無合法步)
            legal = np.where(action_mask == 1)[0]
            return int(np.random.choice(legal)) if len(legal) else 0

        except Exception as e:
            # 發生任何錯誤時降級為單執行緒模式
            print(f"⚠️ D5 Pro error: {e}. Downgrading to single-thread mode.")
            self.fallback_triggered = True
            
            try:
                # 第一步走邊邊士兵作為降級信號
                board = _rebuild_relative(observation)
                edge_moves = ["h2h3", "h2h4", "a2a3", "a2a4", "h7h6", "a7a6"]
                for move_uci in edge_moves:
                    try:
                        m = chess.Move.from_uci(move_uci)
                        if m in board.legal_moves:
                            action = _m2a(m)
                            if 0 <= action < 4672 and action_mask[action] == 1:
                                return int(action)
                    except:
                        continue
                        
                # 若無合法的邊邊士兵，直接以單執行緒重新搜尋
                best_move = search_best_move(board, self.depth, time_limit=4.5, disable_parallel=True, my_real_color=self.my_real_color, search_history=search_history)
                if best_move is not None:
                    action = _m2a(best_move)
                    if 0 <= action < 4672 and action_mask[action] == 1:
                        return int(action)
                        
                legal = np.where(action_mask == 1)[0]
                return int(np.random.choice(legal)) if len(legal) else 0
            except Exception as e2:
                print(f"⚠️ D5 fallback also failed: {e2}")
                legal = np.where(action_mask == 1)[0]
                return int(np.random.choice(legal)) if len(legal) else 0
