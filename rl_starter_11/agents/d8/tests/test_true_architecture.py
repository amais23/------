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

def run_forward(path, board, divide_mode='floor'):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    # 1. FT Layers (with corrected offsets 193 and 25199297)
    friend_bias = np.frombuffer(file_data[193 : 193 + 512], dtype=np.int16)
    friend_weights = np.frombuffer(file_data[705 : 705 + 49216 * 256 * 2], dtype=np.int16).reshape(49216, 256)
    enemy_bias = np.frombuffer(file_data[25199297 : 25199297 + 512], dtype=np.int16)
    enemy_weights = np.frombuffer(file_data[25199809 : 25199809 + 43840 * 256 * 2], dtype=np.int16).reshape(43840, 256)
    
    # Bucket 7 is Large Stack 3. Starts at fc_start + 4768 + 3 * 17704
    fc_start = 47645889
    start_stack = fc_start + 4768 + 3 * 17704
    
    # L1: bias (32 int32 = 128 bytes), weights (32 * 512 int8 = 16384 bytes)
    l1_bias = np.frombuffer(file_data[start_stack+4 : start_stack+132], dtype=np.int32)
    l1_weights = np.frombuffer(file_data[start_stack+132 : start_stack+16516], dtype=np.int8).reshape(32, 512)
    
    # L2: bias (32 int32 = 128 bytes), weights (32 * 32 int8 = 1024 bytes)
    l2_bias = np.frombuffer(file_data[start_stack+16516 : start_stack+16644], dtype=np.int32)
    l2_weights = np.frombuffer(file_data[start_stack+16644 : start_stack+17668], dtype=np.int8).reshape(32, 32)
    
    # L3: bias (1 int32 = 4 bytes), weights (32 int8 = 32 bytes)
    l3_bias = struct.unpack('<i', file_data[start_stack+17668 : start_stack+17672])[0]
    l3_weights = np.frombuffer(file_data[start_stack+17672 : start_stack+17704], dtype=np.int8)
    
    # Compute Us Accumulator
    us_indices = get_piece_features(board, True)
    acc_us = friend_bias.astype(np.int32).copy()
    for idx in us_indices:
        acc_us += friend_weights[idx].astype(np.int32)
        
    # Compute Them Accumulator
    enemy_indices = get_enemy_features(board, True)
    acc_them = enemy_bias.astype(np.int32).copy()
    for idx in enemy_indices:
        acc_them += enemy_weights[idx].astype(np.int32)
        
    # Feature Transformer Activation (standard Clipped ReLU, size 256 each, total 512)
    def clipped_relu(acc):
        if isinstance(divide_mode, int):
            if divide_mode == 1:
                acc_scaled = acc
            else:
                acc_scaled = acc // divide_mode
        elif divide_mode == 'floor':
            acc_scaled = acc // 127
        elif divide_mode == 'trunc':
            acc_scaled = np.trunc(acc / 127.0).astype(np.int32)
        else:
            acc_scaled = acc
        return np.clip(acc_scaled, 0, 127).astype(np.int8)
        
    in_l1 = np.concatenate([clipped_relu(acc_us), clipped_relu(acc_them)])
    
    # L1 Propagation
    out_l1 = np.dot(l1_weights.astype(np.int32), in_l1.astype(np.int32)) + l1_bias
    out_l1_scaled = out_l1 // 64
    
    # L1 Activation (standard Clipped ReLU, size 32)
    in_l2 = np.clip(out_l1_scaled, 0, 127).astype(np.int8)
    
    # L2 Propagation
    out_l2 = np.dot(l2_weights.astype(np.int32), in_l2.astype(np.int32)) + l2_bias
    out_l2_scaled = out_l2 // 64
    
    # L2 Activation (standard Clipped ReLU, size 32)
    in_l3 = np.clip(out_l2_scaled, 0, 127).astype(np.int8)
    
    # L3 Propagation
    out_l3 = np.dot(l3_weights.astype(np.int32), in_l3.astype(np.int32)) + l3_bias
    
    return out_l3

if __name__ == '__main__':
    positions = {
        "Start": chess.Board(),
        "Won (White up Queen)": chess.Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        "Lost (White down Queen)": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1")
    }
    
    for div_factor in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]:
        print(f"\n================ Division Factor: {div_factor} ================")
        results = {}
        for name, b in positions.items():
            # Implement custom division factor in run_forward inline or pass it
            out = run_forward('agents/d8/weights/nn.nnue', b, divide_mode=div_factor)
            results[name] = out
            
        print(f"  Start: {results['Start']} ({results['Start']/600.0:.2f} cp)")
        print(f"  Won:   {results['Won (White up Queen)']} ({results['Won (White up Queen)']/600.0:.2f} cp)")
        print(f"  Lost:  {results['Lost (White down Queen)']} ({results['Lost (White down Queen)']/600.0:.2f} cp)")
        
        diff_won = results['Won (White up Queen)'] - results['Start']
        diff_lost = results['Start'] - results['Lost (White down Queen)']
        print(f"  Won - Start: {diff_won}, Start - Lost: {diff_lost}")
