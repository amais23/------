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
_NODE_COUNT = 0
_LAST_NPS = 0.0
_LAST_SCORE = 0

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
    global _NODE_COUNT
    _NODE_COUNT += 1
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
    global _NODE_COUNT
    _NODE_COUNT += 1
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
    global _SEARCH_START_TIME, _SEARCH_TIME_LIMIT, _NODE_COUNT, _LAST_NPS, _LAST_SCORE
    _SEARCH_START_TIME = time.time()
    _NODE_COUNT = 0
    
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
                    _LAST_NPS = 0.0
                    _LAST_SCORE = 0
                    # 轉回黑方的相對 move
                    return chess.Move(
                        from_square=abs_move.from_square ^ 56,
                        to_square=abs_move.to_square ^ 56,
                        promotion=abs_move.promotion
                    )
            else:
                entry = BOOK_READER.weighted_choice(board)
                _LAST_NPS = 0.0
                _LAST_SCORE = 0
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
                try:
                    wdl = -TABLEBASE.probe_wdl(board)
                    dtz = -TABLEBASE.probe_dtz(board)
                finally:
                    board.pop()
                
                score = wdl * 10000
                if wdl > 0: score -= abs(dtz) # 贏：步數越少越好
                elif wdl < 0: score += abs(dtz) # 輸：步數越多越好
                
                if score > best_tb_score:
                    best_tb_score = score
                    best_tb_move = move
                    
            if best_tb_move:
                _LAST_NPS = 0.0
                _LAST_SCORE = best_tb_score
                return best_tb_move
        except chess.syzygy.MissingTableError:
            pass
            
    # 動態時間分配 (Dynamic Time Allocation) - 針對 600s/20場 的極限賽制
    phase = sum(1 for pt in board.piece_map().values() if pt.piece_type != chess.PAWN and pt.piece_type != chess.KING)
    if phase >= 8:      # 中局前期
        _SEARCH_TIME_LIMIT = 0.6
    elif phase >= 4:    # 中局後期
        _SEARCH_TIME_LIMIT = 0.3
    else:               # 殘局
        _SEARCH_TIME_LIMIT = 0.15
        
    # 保險機制：不超過環境給定的 time_limit
    _SEARCH_TIME_LIMIT = min(_SEARCH_TIME_LIMIT, time_limit)
    
    best_move = None
    last_depth_score = 0
    
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
            last_depth_score = current_best_val
            
    except SearchTimeout:
        pass
        
    # 如果第一層都沒搜完，則保證回傳至少一個合法著法
    if best_move is None:
        if board.legal_moves:
            best_move = list(board.legal_moves)[0]
            
    elapsed = time.time() - _SEARCH_START_TIME
    _LAST_NPS = _NODE_COUNT / elapsed if elapsed > 0 else 0.0
    _LAST_SCORE = last_depth_score

    return best_move

# ────────────────────────────────────────────────────
# Agent Interface
# ────────────────────────────────────────────────────
class Agent:
    def __init__(self):
        self.depth = SEARCH_DEPTH
        self.my_real_color = None
        self.real_game_history = {}  # 💡 新增：記錄真實對局的 Zobrist Hash 次數
        self.last_nps = 0.0
        self.last_score = 0
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
            best_move = search_best_move(board, self.depth, time_limit=4.5, my_real_color=self.my_real_color, search_history=search_history)

            # 3. 轉回 action index
            if best_move is not None:
                action = _m2a(best_move)
                if 0 <= action < 4672 and action_mask[action] == 1:
                    self.last_nps = float(_LAST_NPS)
                    self.last_score = int(_LAST_SCORE)
                    return int(action)

            # 4. Fallback: 隨機合法步 (理論上不會觸發，除非無合法步)
            self.last_nps = 0.0
            self.last_score = 0
            legal = np.where(action_mask == 1)[0]
            return int(np.random.choice(legal)) if len(legal) else 0

        except Exception:
            # 發生 any 錯誤時降級為隨機合法步
            self.last_nps = 0.0
            self.last_score = 0
            legal = np.where(action_mask == 1)[0]
            return int(np.random.choice(legal)) if len(legal) else 0
