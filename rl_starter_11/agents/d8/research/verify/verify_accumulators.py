import struct
import numpy as np
import chess

def orient(is_white_pov: bool, sq: int):
    return sq ^ 56 if not is_white_pov else sq

def get_piece_features(board: chess.Board, is_white_pov: bool):
    king_sq = orient(is_white_pov, board.king(is_white_pov))
    us_indices = []
    for sq, p in board.piece_map().items():
        p_idx = (p.piece_type - 1) * 2 + (p.color != is_white_pov)
        oriented_sq = orient(is_white_pov, sq)
        idx = 1 + oriented_sq + p_idx * 64 + king_sq * 769
        us_indices.append(idx)
    return us_indices

def verify(path):
    with open(path, 'rb') as f:
        file_data = f.read()
        
    friend_bias = np.frombuffer(file_data[189 : 189 + 512], dtype=np.int16)
    friend_weights = np.frombuffer(file_data[705 : 705 + 49216 * 256 * 2], dtype=np.int16).reshape(49216, 256)
    
    board = chess.Board()
    us_indices = get_piece_features(board, True)
    
    # 1. As int32 (no overflow)
    acc_32 = friend_bias.astype(np.int32).copy()
    for idx in us_indices:
        acc_32 += friend_weights[idx].astype(np.int32)
        
    # 2. As int16 (with overflow/wrapping)
    acc_16 = friend_bias.copy()
    for idx in us_indices:
        acc_16 = acc_16 + friend_weights[idx]  # numpy does standard addition, which can promote or clip. Let's make sure it wraps.
        
    # Let's force int16 wrapping:
    acc_wrap = friend_bias.astype(np.int16).copy()
    for idx in us_indices:
        acc_wrap = (acc_wrap.astype(np.int32) + friend_weights[idx].astype(np.int32)).astype(np.int16)
        
    print("acc_32 stats: min/max/mean", acc_32.min(), acc_32.max(), acc_32.mean())
    print("acc_wrap stats: min/max/mean", acc_wrap.min(), acc_wrap.max(), acc_wrap.mean())
    
    print("\nFirst 10 values of acc_32:")
    print(list(acc_32[:10]))
    print("First 10 values of acc_wrap:")
    print(list(acc_wrap[:10]))

if __name__ == '__main__':
    verify('nn.nnue')
