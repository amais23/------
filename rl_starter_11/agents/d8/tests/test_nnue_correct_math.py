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

def run_forward(path, board):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    # 1. FT Layers
    friend_bias = np.frombuffer(file_data[193 : 193 + 512], dtype=np.int16)
    friend_weights = np.frombuffer(file_data[705 : 705 + 49216 * 256 * 2], dtype=np.int16).reshape(49216, 256)
    enemy_bias = np.frombuffer(file_data[25199297 : 25199297 + 512], dtype=np.int16)
    enemy_weights = np.frombuffer(file_data[25199809 : 25199809 + 43840 * 256 * 2], dtype=np.int16).reshape(43840, 256)
    
    # Starting Position: E1 king -> bucket 7. Use Main Stack 3 (starts at 47650913 + 3 * 17640)
    start_stack = 47650913 + 3 * 17640
    
    # Correct offsets for 16<-1024 layer:
    l1_bias = np.frombuffer(file_data[start_stack+4 : start_stack+68], dtype=np.int32)
    l1_weights = np.frombuffer(file_data[start_stack+68 : start_stack+16452], dtype=np.int8).reshape(16, 1024)
    l2_bias = np.frombuffer(file_data[start_stack+16452 : start_stack+16580], dtype=np.int32)
    l2_weights = np.frombuffer(file_data[start_stack+16580 : start_stack+17604], dtype=np.int8).reshape(32, 32)
    l3_bias = struct.unpack('<i', file_data[start_stack+17604 : start_stack+17608])[0]
    l3_weights = np.frombuffer(file_data[start_stack+17608 : start_stack+17640], dtype=np.int8)
    
    # Compute Us Accumulator
    us_indices = get_piece_features(board, True)
    print("Python us_indices:", sorted(us_indices))
    acc_us = friend_bias.astype(np.int32).copy()
    for idx in us_indices:
        acc_us += friend_weights[idx].astype(np.int32)
    print("Python acc_us sum:", np.sum(acc_us))
    print("Python acc_us first 10:", list(acc_us[:10]))
        
    # Compute Them Accumulator
    enemy_indices = get_enemy_features(board, True)
    print("Python enemy_indices:", sorted(enemy_indices))
    acc_them = enemy_bias.astype(np.int32).copy()
    for idx in enemy_indices:
        acc_them += enemy_weights[idx].astype(np.int32)
    print("Python acc_them sum:", np.sum(acc_them))
    print("Python acc_them first 10:", list(acc_them[:10]))
        
    # Dual-sided Clipped ReLU (no scale down by 127 in this file? Wait, verify_forward_pass_correct scaled by 127, but debug_forward_pass or others? Let's check.)
    # In verify_forward_pass_starting.py:
    # "x_pos = np.clip(acc, 0, 127)" (no division!)
    # Let's check if we divide or not.
    # In standard NNUE, accumulator values are clipped directly between 0 and 127.
    # Let's run with and without division by 127!
    
    for divide_mode in ['floor', 'trunc', 'none']:
        if divide_mode == 'floor':
            in_l1 = np.concatenate([
                np.clip(acc_us // 127, 0, 127).astype(np.int8),
                np.clip(-(acc_us // 127), 0, 127).astype(np.int8),
                np.clip(acc_them // 127, 0, 127).astype(np.int8),
                np.clip(-(acc_them // 127), 0, 127).astype(np.int8)
            ])
        elif divide_mode == 'trunc':
            in_l1 = np.concatenate([
                np.clip(np.trunc(acc_us / 127.0).astype(np.int32), 0, 127).astype(np.int8),
                np.clip(np.trunc(-acc_us / 127.0).astype(np.int32), 0, 127).astype(np.int8),
                np.clip(np.trunc(acc_them / 127.0).astype(np.int32), 0, 127).astype(np.int8),
                np.clip(np.trunc(-acc_them / 127.0).astype(np.int32), 0, 127).astype(np.int8)
            ])
        else:
            in_l1 = np.concatenate([
                np.clip(acc_us, 0, 127).astype(np.int8),
                np.clip(-acc_us, 0, 127).astype(np.int8),
                np.clip(acc_them, 0, 127).astype(np.int8),
                np.clip(-acc_them, 0, 127).astype(np.int8)
            ])
            
        # L1 Propagation
        out_l1 = np.dot(l1_weights.astype(np.int32), in_l1.astype(np.int32)) + l1_bias
        out_l1_scaled = out_l1 // 64
        
        # L1 Activation (dual-sided Clipped ReLU)
        in_l2 = np.concatenate([np.clip(out_l1_scaled, 0, 127).astype(np.int8), np.clip(-out_l1_scaled, 0, 127).astype(np.int8)])
        
        # L2 Propagation
        out_l2 = np.dot(l2_weights.astype(np.int32), in_l2.astype(np.int32)) + l2_bias
        out_l2_scaled = out_l2 // 64
        
        # L2 Activation (standard Clipped ReLU)
        in_l3 = np.clip(out_l2_scaled, 0, 127).astype(np.int8)
        
        # L3 Propagation
        out_l3 = np.dot(l3_weights.astype(np.int32), in_l3.astype(np.int32)) + l3_bias
        
        print(f"DivideMode={divide_mode}: Raw output={out_l3}, cp={out_l3 / 600.0:.2f}")

if __name__ == '__main__':
    board = chess.Board()
    run_forward('weights/nn.nnue', board)
