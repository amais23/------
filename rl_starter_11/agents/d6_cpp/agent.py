"""
D6 C++ Engine — Python Bootloader
PID 隔離解壓 + Python 端 Syzygy 殘局庫探測
"""
import os
import sys
import zipfile
import shutil
import errno
import numpy as np

# ──── Python 端殘局庫（保持穩定性） ────
import chess
import chess.polyglot
import chess.syzygy

_ENGINE = None
_TABLEBASE = None

# ════════════════════════════════════════════
# PID 隔離 Bootloader
# ════════════════════════════════════════════
def _bootstrap():
    global _ENGINE, _TABLEBASE

    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(base_dir, "model.zip")
    if not os.path.exists(zip_path):
        zip_path = "model.zip"

    # 1. 優先透過 os.walk 搜尋整個 base_dir，尋找平台預先解壓的 .so 檔案
    extract_dir = None
    engine_found = False
    
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if "chess_engine" in f and f.endswith(".so"):
                # 找到平台可能預先解壓的引擎了！
                sys.path.insert(0, root)
                try:
                    import chess_engine
                    extract_dir = root
                    engine_found = True
                    break
                except ImportError:
                    # 雖然找到了檔名，但載入失敗，移除路徑並繼續找下一個
                    sys.path.remove(root)
        if engine_found:
            break

    if not engine_found:
        # 2. 如果在整個 base_dir 內翻箱倒櫃都找不到，才嘗試解壓到其他暫存目錄
        pid = os.getpid()
        writable_dirs = ["/dev/shm", "/tmp", "/var/tmp", os.path.expanduser("~")]
        
        extract_dir = None
        for d in writable_dirs:
            try:
                test_dir = os.path.join(d, f"chess_assets_{pid}")
                os.makedirs(test_dir, exist_ok=True)
                
                # 解壓
                if os.path.exists(zip_path):
                    with zipfile.ZipFile(zip_path, 'r') as z:
                        z.extractall(test_dir)
                
                # 嘗試 Import
                sys.path.insert(0, test_dir)
                import chess_engine
                
                extract_dir = test_dir
                break  # 成功載入！
                
            except Exception as e:
                # 清理失敗的路徑並嘗試下一個
                if test_dir and os.path.exists(test_dir):
                    shutil.rmtree(test_dir, ignore_errors=True)
                if test_dir in sys.path:
                    sys.path.remove(test_dir)
                continue

    if not extract_dir:
        raise RuntimeError("無法在任何目錄中解壓縮並執行 C++ 引擎 (.so)，可能全被限制為 noexec 或是唯讀")

    # 載入開局庫
    book_file = os.path.join(extract_dir, "book.bin")
    chess_engine.init(book_path=book_file if os.path.exists(book_file) else "")
    _ENGINE = chess_engine

    # 載入 Python 端 Syzygy 殘局庫
    syzygy_dir = os.path.join(extract_dir, "syzygy")
    if not os.path.isdir(syzygy_dir):
        syzygy_dir = "/tmp/syzygy"
    if os.path.isdir(syzygy_dir):
        try:
            _TABLEBASE = chess.syzygy.open_tablebase(syzygy_dir)
            print(f"✅ Syzygy loaded from {syzygy_dir}")
        except Exception as e:
            print(f"⚠️ Syzygy load failed: {e}")


# ════════════════════════════════════════════
# 棋盤重建工具（Python 端，僅供殘局庫探測用）
# ════════════════════════════════════════════
_PIECES = [
    (7, chess.PAWN), (8, chess.KNIGHT), (9, chess.BISHOP),
    (10, chess.ROOK), (11, chess.QUEEN), (12, chess.KING)
]
_OPP_PIECES = [
    (13, chess.PAWN), (14, chess.KNIGHT), (15, chess.BISHOP),
    (16, chess.ROOK), (17, chess.QUEEN), (18, chess.KING)
]

def _rebuild_relative(obs):
    """從 observation 重建相對棋盤（僅用於殘局庫探測）"""
    if obs[:, :, 7:19].sum() == 0:
        return chess.Board()
    b = chess.Board(fen=None)
    b.clear()
    for ch, pt in _PIECES:
        layer = obs[:, :, ch]
        for r in range(8):
            for c in range(8):
                if layer[r, c]:
                    if pt == chess.PAWN and r == 7: continue
                    b.set_piece_at(chess.square(c, 7 - r),
                                   chess.Piece(pt, chess.WHITE))
    for ch, pt in _OPP_PIECES:
        layer = obs[:, :, ch]
        for r in range(8):
            for c in range(8):
                if layer[r, c]:
                    if pt == chess.PAWN and r == 0: continue
                    b.set_piece_at(chess.square(c, 7 - r),
                                   chess.Piece(pt, chess.BLACK))
    b.turn = chess.WHITE
    cr = 0
    if obs[0, 0, 0]: cr |= chess.BB_H1
    if obs[0, 0, 1]: cr |= chess.BB_A1
    if obs[0, 0, 2]: cr |= chess.BB_H8
    if obs[0, 0, 3]: cr |= chess.BB_A8
    b.castling_rights = cr
    for col in range(8):
        if obs[7, col, 7]:
            b.set_piece_at(chess.square(col, 3),
                           chess.Piece(chess.PAWN, chess.WHITE))
            b.ep_square = chess.square(col, 2)
    for col in range(8):
        if obs[0, col, 13]:
            b.set_piece_at(chess.square(col, 4),
                           chess.Piece(chess.PAWN, chess.BLACK))
            b.ep_square = chess.square(col, 5)
    return b

import pettingzoo.classic.chess.chess_utils as cu

def _m2a(move):
    col = move.from_square % 8
    row = move.from_square // 8
    return (col * 8 + row) * 73 + cu.get_move_plane(move)


# ════════════════════════════════════════════
# Python 端殘局庫探測
# ════════════════════════════════════════════
def _probe_syzygy(obs, action_mask):
    """如果局面 ≤5 子，查詢 Syzygy 殘局庫，回傳 action index 或 -1"""
    if _TABLEBASE is None:
        return -1
    try:
        board = _rebuild_relative(obs)
        if board.occupied.bit_count() > 5:
            return -1

        best_move = None
        best_score = -999999999

        for move in board.legal_moves:
            board.push(move)
            try:
                wdl = -_TABLEBASE.probe_wdl(board)
                try:
                    dtz = -_TABLEBASE.probe_dtz(board)
                except Exception:
                    dtz = 0
            finally:
                board.pop()

            score = wdl * 10000000
            if wdl > 0:   score -= abs(dtz)
            elif wdl < 0: score += abs(dtz)

            if score > best_score:
                best_score = score
                best_move = move

        if best_move:
            action = _m2a(best_move)
            if 0 <= action < 4672 and action_mask[action] == 1:
                return action
    except Exception:
        pass
    return -1


# ════════════════════════════════════════════
# Agent 介面
# ════════════════════════════════════════════
class Agent:
    def __init__(self):
        _bootstrap()

    def act(self, observation: np.ndarray, action_mask: np.ndarray) -> int:
        try:
            # 1. Python 端殘局庫探測（≤5 子時觸發）
            tb_action = _probe_syzygy(observation, action_mask)

            # 2. 呼叫 C++ 搜尋引擎
            return int(_ENGINE.solve(observation, action_mask, tb_action))

        except Exception:
            # 任何錯誤 → 降級為隨機合法步
            legal = np.where(action_mask == 1)[0]
            return int(np.random.choice(legal)) if len(legal) else 0
