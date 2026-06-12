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

def get_enemy_features(board: chess.Board, is_white_pov: bool, option=1):
    king_sq = orient(is_white_pov, board.king(is_white_pov))
    
    enemy_indices = []
    for sq, p in board.piece_map().items():
        them_pov = not is_white_pov
        
        if p.piece_type == chess.KING and p.color == is_white_pov:
            continue
            
        them_king_sq = orient(them_pov, board.king(them_pov))
        p_idx = (p.piece_type - 1) * 2 + (p.color != them_pov)
        oriented_sq = orient(them_pov, sq)
        
        if option == 1:
            # Pawn squares mapped to 0-47, starts at 1
            if p.piece_type == chess.PAWN:
                pawn_plane = 0 if p.color == them_pov else 1
                plane_offset = 1 + pawn_plane * 48 + (oriented_sq - 8)
            else:
                pt_idx = (p.piece_type - 2) * 2 + (p.color != them_pov)
                plane_offset = 1 + 96 + pt_idx * 64 + oriented_sq
                
            idx = plane_offset + them_king_sq * 685
            enemy_indices.append(idx)
            
        elif option == 2:
            pt_idx = (p.piece_type - 1) * 2 + (p.color != them_pov)
            if pt_idx > 10:
                continue
            plane_offset = 1 + pt_idx * 64 + oriented_sq
            idx = plane_offset + them_king_sq * 685
            enemy_indices.append(idx)
            
    return enemy_indices

def run_forward(path, board, option=1):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    # 1. Load Feature Transformers
    friend_bias = np.frombuffer(file_data[189 : 189 + 512], dtype=np.int16)
    friend_weights = np.frombuffer(file_data[705 : 705 + 49216 * 256 * 2], dtype=np.int16).reshape(49216, 256)
    
    enemy_bias = np.frombuffer(file_data[25199293 : 25199293 + 512], dtype=np.int16)
    enemy_weights = np.frombuffer(file_data[25199809 : 25199809 + 43840 * 256 * 2], dtype=np.int16).reshape(43840, 256)
    
    # 2. Load FC Layers (Main Stack 3 / Bucket 7)
    # L1: Main Stack 3 (starts at 47703833)
    start_l1 = 47703833
    l1_bias = np.frombuffer(file_data[start_l1+4 : start_l1+68], dtype=np.int32)
    l1_weights = np.frombuffer(file_data[start_l1+68 : start_l1+16452], dtype=np.int8).reshape(16, 1024)
    
    # L2+L3: Main Stack 3 (starts at 47703833)
    l2_bias = np.frombuffer(file_data[start_l1+16452 : start_l1+16452+128], dtype=np.int32)
    l2_weights = np.frombuffer(file_data[start_l1+16580 : start_l1+16580+1024], dtype=np.int8).reshape(32, 32)
    l3_bias = struct.unpack('<i', file_data[start_l1+17604 : start_l1+17608])[0]
    l3_weights = np.frombuffer(file_data[start_l1+17608 : start_l1+17640], dtype=np.int8)
    
    # 3. Compute Us Accumulator
    us_indices = get_piece_features(board, True)
    acc_us = friend_bias.astype(np.int32).copy()
    for idx in us_indices:
        acc_us += friend_weights[idx].astype(np.int32)
        
    # 4. Compute Them Accumulator
    enemy_indices = get_enemy_features(board, True, option)
    acc_them = enemy_bias.astype(np.int32).copy()
    for idx in enemy_indices:
        acc_them += enemy_weights[idx].astype(np.int32)
        
    print(f"\n--- DEBUG Option {option} (Bucket 7) ---")
    print(f"acc_us: min={acc_us.min()}, max={acc_us.max()}, mean={acc_us.mean():.2f}")
    print(f"acc_them: min={acc_them.min()}, max={acc_them.max()}, mean={acc_them.mean():.2f}")
    
    # 5. Dual-sided Clipped ReLU on Us and Them
    def dual_clipped_relu(acc):
        acc_scaled = acc // 127
        x_pos = np.clip(acc_scaled, 0, 127).astype(np.int8)
        x_neg = np.clip(-acc_scaled, 0, 127).astype(np.int8)
        return np.concatenate([x_pos, x_neg])
        
    in_l1 = np.concatenate([dual_clipped_relu(acc_us), dual_clipped_relu(acc_them)])
    print(f"in_l1: min={in_l1.min()}, max={in_l1.max()}, mean={in_l1.mean():.2f}, sum={in_l1.sum()}")
    
    # 6. L1 Forward Pass
    out_l1 = np.dot(l1_weights.astype(np.int32), in_l1.astype(np.int32)) + l1_bias
    print(f"out_l1: min={out_l1.min()}, max={out_l1.max()}, mean={out_l1.mean():.2f}")
    
    # Scale down L1 output by 64 and apply dual-sided Clipped ReLU
    out_l1_scaled = out_l1 // 64
    in_l2 = np.concatenate([np.clip(out_l1_scaled, 0, 127).astype(np.int8), np.clip(-out_l1_scaled, 0, 127).astype(np.int8)])
    
    # 7. L2 Forward Pass
    out_l2 = np.dot(l2_weights.astype(np.int32), in_l2.astype(np.int32)) + l2_bias
    print(f"out_l2: min={out_l2.min()}, max={out_l2.max()}, mean={out_l2.mean():.2f}")
    
    # Scale down L2 output by 64 and apply standard Clipped ReLU (no dual-sided)
    out_l2_scaled = out_l2 // 64
    in_l3 = np.clip(out_l2_scaled, 0, 127).astype(np.int8)
    
    # 8. L3 Forward Pass
    out_l3 = np.dot(l3_weights.astype(np.int32), in_l3.astype(np.int32)) + l3_bias
    
    print(f"Raw output={out_l3}, in centipawns (divided by 600)={out_l3 / 600.0:.2f} cp")
    return out_l3

if __name__ == '__main__':
    board = chess.Board()
    run_forward('nn.nnue', board, option=1)
    run_forward('nn.nnue', board, option=2)
