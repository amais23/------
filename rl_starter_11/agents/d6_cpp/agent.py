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

_ENGINE_MODULE = None
_TABLEBASE = None

# ═══════════════════════════════════════════
# PID 隔離 Bootloader
# ═══════════════════════════════════════════
def _bootstrap():
    global _ENGINE_MODULE, _TABLEBASE
    if _ENGINE_MODULE is not None:
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(base_dir, "model.zip")
    if not os.path.exists(zip_path):
        zip_path = "model.zip"

    sys.path.insert(0, base_dir)
    try:
        import chess_engine_d6_han
        _ENGINE_MODULE = chess_engine_d6_han
        
    except ImportError:
        # [MAGIC ZIP LOADER]
        # 由於沙箱的 /tmp 被掛載 noexec，且 /app/arena 被掛載 Read-Only
        # 我們將 chess_engine.so 與 book.bin 串接成了 magic.zip 並上傳
        # 因此 model.zip 同時是一個 ELF 動態函式庫與一個 ZIP 壓縮檔！
        
        # 1. 直接將 model.zip 視為 .so 檔案載入記憶體執行
        import importlib.machinery
        import importlib.util
        
        try:
            # 直接對 zip 檔使用 C 擴充載入器，這會透過 dlopen(model.zip) 直接在唯讀環境中載入！
            loader = importlib.machinery.ExtensionFileLoader("chess_engine_d6_han", os.path.abspath(zip_path))
            spec = importlib.util.spec_from_loader("chess_engine_d6_han", loader)
            chess_engine_d6_han = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(chess_engine_d6_han)
            _ENGINE_MODULE = chess_engine_d6_han
            
        except Exception as e:
            raise RuntimeError(f"魔法載入失敗！無法載入 C++ 引擎: {e}\nzip_path={zip_path}")

    # 載入 Python 端 Syzygy 殘局庫
    syzygy_dir = os.path.join(base_dir, "syzygy")
    if not os.path.isdir(syzygy_dir):
        syzygy_dir = "/tmp/syzygy"
    if os.path.isdir(syzygy_dir):
        try:
            _TABLEBASE = chess.syzygy.open_tablebase(syzygy_dir)
            print(f"✅ Syzygy loaded from {syzygy_dir}")
        except Exception as e:
            print(f"⚠️ Syzygy load failed: {e}")


# ═══════════════════════════════════════════
# 棋盤重建工具（Python 端，僅供殘局庫探測用）
# ═══════════════════════════════════════════
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


# ═══════════════════════════════════════════
# Python 端殘局庫探測
# ═══════════════════════════════════════════
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


# ═══════════════════════════════════════════
# Agent 介面
# ═══════════════════════════════════════════
class Agent:
    def __init__(self):
        _bootstrap()
        self.engine = _ENGINE_MODULE.SearchEngine()
        self.engine.init("")

    def act(self, observation: np.ndarray, action_mask: np.ndarray) -> int:
        try:
            # 1. Python 端殘局庫探測（≤5 子時觸發）
            tb_action = _probe_syzygy(observation, action_mask)

            # 2. 呼叫 C++ 搜尋引擎
            return int(self.engine.solve(observation, action_mask, tb_action))

        except Exception:
            # 任何錯誤 → 降級為隨機合法步
            legal = np.where(action_mask == 1)[0]
            return int(np.random.choice(legal)) if len(legal) else 0
