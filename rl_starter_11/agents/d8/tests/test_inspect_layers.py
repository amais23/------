import sys
import os
import struct
import numpy as np
import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

def get_enemy_features(board: chess.Board, is_white_pov: bool):
    them_pov = not is_white_pov
    king_sq = orient(them_pov, board.king(them_pov))
    enemy_indices = []
    for sq, p in board.piece_map().items():
        if p.piece_type == chess.KING and p.color == is_white_pov:
            continue
        p_idx = (p.piece_type - 1) * 2 + (p.color != them_pov)
        oriented_sq = orient(them_pov, sq)
        if p.piece_type == chess.PAWN:
            pawn_plane = 0 if p.color == them_pov else 1
            plane_offset = 1 + pawn_plane * 48 + (oriented_sq - 8)
        else:
            pt_idx = (p.piece_type - 2) * 2 + (p.color != them_pov)
            plane_offset = 1 + 96 + pt_idx * 64 + oriented_sq
        idx = plane_offset + king_sq * 685
        enemy_indices.append(idx)
    return enemy_indices

def inspect_layers(board: chess.Board, weights_path='weights/nn.nnue'):
    with open(weights_path, 'rb') as f:
        file_data = f.read()
    
    friend_bias = np.frombuffer(file_data[193 : 193 + 512], dtype=np.int16)
    friend_weights = np.frombuffer(file_data[705 : 705 + 49216 * 256 * 2], dtype=np.int16).reshape(49216, 256)
    enemy_bias = np.frombuffer(file_data[25199297 : 25199297 + 512], dtype=np.int16)
    enemy_weights = np.frombuffer(file_data[25199809 : 25199809 + 43840 * 256 * 2], dtype=np.int16).reshape(43840, 256)
    
    side_pov = 0 if board.turn == chess.WHITE else 1
    oriented_king_us = orient(side_pov == 0, board.king(board.turn))
    bucket_us = 7 - (oriented_king_us // 8)
    
    fc_start = 47645889
    stack_idx = bucket_us % 4
    start_stack = fc_start + 4768 + stack_idx * 17704
    
    l1_bias = np.frombuffer(file_data[start_stack+4 : start_stack+132], dtype=np.int32)
    l1_weights = np.frombuffer(file_data[start_stack+132 : start_stack+16516], dtype=np.int8).reshape(32, 512)
    l2_bias = np.frombuffer(file_data[start_stack+16516 : start_stack+16644], dtype=np.int32)
    l2_weights = np.frombuffer(file_data[start_stack+16644 : start_stack+17668], dtype=np.int8).reshape(32, 32)
    l3_bias = struct.unpack('<i', file_data[start_stack+17668 : start_stack+17672])[0]
    l3_weights = np.frombuffer(file_data[start_stack+17672 : start_stack+17704], dtype=np.int8)
        
    us_indices = get_piece_features(board, True)
    acc_us = friend_bias.astype(np.int32).copy()
    for idx in us_indices:
        acc_us += friend_weights[idx].astype(np.int32)
        
    enemy_indices = get_enemy_features(board, True)
    acc_them = enemy_bias.astype(np.int32).copy()
    for idx in enemy_indices:
        acc_them += enemy_weights[idx].astype(np.int32)
        
    def activate(acc):
        acc_scaled = acc // 8
        return np.clip(acc_scaled, 0, 127).astype(np.int8)
        
    in_l1 = np.concatenate([activate(acc_us), activate(acc_them)])
    
    out_l1 = np.dot(l1_weights.astype(np.int32), in_l1.astype(np.int32)) + l1_bias
    out_l1_scaled = out_l1 // 64
    in_l2 = np.clip(out_l1_scaled, 0, 127).astype(np.int8)
    
    out_l2 = np.dot(l2_weights.astype(np.int32), in_l2.astype(np.int32)) + l2_bias
    out_l2_scaled = out_l2 // 64
    in_l3 = np.clip(out_l2_scaled, 0, 127).astype(np.int8)
    
    out_l3 = np.dot(l3_weights.astype(np.int32), in_l3.astype(np.int32)) + l3_bias
    
    print("  Accumulator US:   min =", acc_us.min(), "max =", acc_us.max(), "sum =", acc_us.sum())
    print("  Accumulator THEM: min =", acc_them.min(), "max =", acc_them.max(), "sum =", acc_them.sum())
    print("  L1 Input activated features count (non-zero):", np.sum(in_l1 > 0))
    print("  L1 Output:        min =", out_l1.min(), "max =", out_l1.max(), "sum =", out_l1.sum())
    print("  L2 Input activated features count (non-zero):", np.sum(in_l2 > 0))
    print("  L2 Output:        min =", out_l2.min(), "max =", out_l2.max(), "sum =", out_l2.sum())
    print("  L3 Input activated features count (non-zero):", np.sum(in_l3 > 0))
    print("  L3 Output (Raw):", out_l3)

def test():
    print("--- START POSITION ---")
    inspect_layers(chess.Board())
    
    print("\n--- OPEN GAME ---")
    inspect_layers(chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"))

if __name__ == '__main__':
    test()
