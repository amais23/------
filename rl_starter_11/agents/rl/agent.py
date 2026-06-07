"""
ML Arena — Chess Agent: MaskablePPO + Rule Engine Safety Net
Environment: PettingZoo chess_v6 (2-player)

Architecture:
  1. Rebuild relative chess.Board (from observation)
  2. Rule A: Checkmate in 1 detection (immediate win)
  3. Rule B: Immediate checkmate avoidance (anti-suicide filtering)
  4. MaskablePPO prediction over the safe action set (via custom action mask)
  5. Try/Except fallback wrapper to ensure 100% reliability in sandbox
"""

import os
import numpy as np
import chess
import pettingzoo.classic.chess.chess_utils as cu

try:
    from model import ALGORITHM
except ImportError:
    from .model import ALGORITHM

# ────────────────────────────────────────────────────
# Tools: Action & Board Reconstruction (Relative)
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
    """Rebuild a chess.Board from observation where the active player is ALWAYS White."""
    # If the history planes are empty (e.g. step 0), initialize standard starting board
    if obs[:, :, 7:19].sum() == 0:
        return chess.Board()

    b = chess.Board(fen=None)
    b.clear()
    
    # Rebuild our pieces (White)
    for ch, pt in _PIECES:
        layer = obs[:, :, ch]
        for r in range(8):
            for c in range(8):
                if layer[r, c]:
                    # Exclude White pawns on rank 1 (row 7 in obs), handled by EP
                    if pt == chess.PAWN and r == 7:
                        continue
                    b.set_piece_at(chess.square(c, 7 - r), chess.Piece(pt, chess.WHITE))
                    
    # Rebuild their pieces (Black)
    for ch, pt in _OPP_PIECES:
        layer = obs[:, :, ch]
        for r in range(8):
            for c in range(8):
                if layer[r, c]:
                    # Exclude Black pawns on rank 8 (row 0 in obs), handled by EP
                    if pt == chess.PAWN and r == 0:
                        continue
                    b.set_piece_at(chess.square(c, 7 - r), chess.Piece(pt, chess.BLACK))
                    
    # Turn is always White's turn in relative board representation
    b.turn = chess.WHITE
    
    # Castling rights
    cr = 0
    if obs[0, 0, 0]: cr |= chess.BB_H1   # White kingside rook (H1)
    if obs[0, 0, 1]: cr |= chess.BB_A1   # White queenside rook (A1)
    if obs[0, 0, 2]: cr |= chess.BB_H8   # Black kingside rook (H8)
    if obs[0, 0, 3]: cr |= chess.BB_A8   # Black queenside rook (A8)
    b.castling_rights = cr
    
    # Fix en passant pawns and set ep_square based on raw observation
    # 1. White pawns on rank 1 (row 7 in obs, channel 7)
    for col in range(8):
        if obs[7, col, 7]:
            b.set_piece_at(chess.square(col, 3), chess.Piece(chess.PAWN, chess.WHITE))
            b.ep_square = chess.square(col, 2)
            
    # 2. Black pawns on rank 8 (row 0 in obs, channel 13)
    for col in range(8):
        if obs[0, col, 13]:
            b.set_piece_at(chess.square(col, 4), chess.Piece(chess.PAWN, chess.BLACK))
            b.ep_square = chess.square(col, 5)
            
    return b

def _m2a(move: chess.Move) -> int:
    """Relative chess.Move -> action index (always White perspective)"""
    col = move.from_square % 8
    row = move.from_square // 8
    return (col * 8 + row) * 73 + cu.get_move_plane(move)

# ────────────────────────────────────────────────────
# Agent Implementation
# ────────────────────────────────────────────────────
class Agent:
    def __init__(self):
        weights_path = os.path.join(os.path.dirname(__file__), "model.zip")
        # Sandbox running always uses cpu
        self.model = ALGORITHM.load(weights_path, device="cpu")

    def act(self, observation: np.ndarray, action_mask: np.ndarray) -> int:
        try:
            return self._act_enhanced(observation, action_mask)
        except Exception:
            # Fallback to pure RL prediction on any exception (guarantees agent never crashes)
            return self._act_rl(observation, action_mask)

    def _act_rl(self, observation: np.ndarray, action_mask: np.ndarray) -> int:
        """Standard model inference fallback."""
        obs_flat = observation.flatten().astype(np.float32)
        action, _ = self.model.predict(
            obs_flat,
            action_masks=action_mask.astype(bool),
            deterministic=True,
        )
        return int(action)

    def _act_enhanced(self, observation: np.ndarray, action_mask: np.ndarray) -> int:
        # 1. Rebuild the relative chess board
        board = _rebuild_relative(observation)

        # 2. Map legal actions to moves
        a2m = {}
        for m in board.legal_moves:
            a = _m2a(m)
            if 0 <= a < 4672 and action_mask[a] == 1:
                a2m[a] = m

        if not a2m:
            return self._act_rl(observation, action_mask)

        # ═══ Rule A: Checkmate in 1 (Immediate Win) ═══
        for action, move in a2m.items():
            board.push(move)
            is_mate = board.is_checkmate()
            board.pop()
            if is_mate:
                return int(action)

        # ═══ Rule B: Checkmate Avoidance (Anti-suicide filtering) ═══
        safe_actions = []
        for action, move in a2m.items():
            board.push(move)
            opponent_can_mate = False
            # Check if opponent has an immediate checkmate response
            for opp_move in board.legal_moves:
                board.push(opp_move)
                is_opp_mate = board.is_checkmate()
                board.pop()
                if is_opp_mate:
                    opponent_can_mate = True
                    break
            board.pop()

            if not opponent_can_mate:
                safe_actions.append(action)

        # 3. Model inference using the safest possible moves
        if safe_actions:
            # Pass custom mask containing only safe moves to model.predict
            safe_mask = np.zeros_like(action_mask)
            for a in safe_actions:
                safe_mask[a] = 1
            return self._act_rl(observation, safe_mask)
        else:
            # No moves avoid immediate checkmate (e.g. lost position), fallback to original mask
            return self._act_rl(observation, action_mask)
