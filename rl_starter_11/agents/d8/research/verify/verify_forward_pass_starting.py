import struct
import numpy as np
import chess

def orient(is_white_pov: bool, sq: int):
    return sq ^ 56 if not is_white_pov else sq

def get_piece_features(board: chess.Board, is_white_pov: bool):
    # Us Features (Friend FT, 49216 size, 769 planes)
    # 769 planes = 1 dummy + 12 piece types * 64 squares
    king_sq = orient(is_white_pov, board.king(is_white_pov))
    
    us_indices = []
    for sq, p in board.piece_map().items():
        # p_idx = (piece_type - 1) * 2 + (color != is_white_pov)
        p_idx = (p.piece_type - 1) * 2 + (p.color != is_white_pov)
        
        # Orient the piece square
        oriented_sq = orient(is_white_pov, sq)
        
        # Us index starts at 1
        idx = 1 + oriented_sq + p_idx * 64 + king_sq * 769
        us_indices.append(idx)
        
    return us_indices

def get_enemy_features(board: chess.Board, is_white_pov: bool, option=1):
    # Them Features (Enemy FT, 43840 size, 685 planes)
    # We test different options for mapping the 685 planes.
    king_sq = orient(is_white_pov, board.king(is_white_pov))
    
    enemy_indices = []
    for sq, p in board.piece_map().items():
        # Exclude the opponent's king (Us King from Them PoV)?
        # From Them PoV, the side to move is is_white_pov (since we evaluate Us and Them for the same state? No, Us is side to move, Them is opponent).
        # Wait, the perspective for Them is NOT is_white_pov, it is NOT is_white_pov!
        # Yes! Them POV is the opponent's color!
        them_pov = not is_white_pov
        
        # From Them PoV:
        # Them King is board.king(them_pov)
        # Us King is board.king(is_white_pov) -> Excluded!
        if p.piece_type == chess.KING and p.color == is_white_pov:
            continue
            
        them_king_sq = orient(them_pov, board.king(them_pov))
        
        # p_idx from Them PoV:
        # own piece: p.color == them_pov
        # enemy piece: p.color != them_pov
        p_idx = (p.piece_type - 1) * 2 + (p.color != them_pov)
        
        # Orient piece square from Them PoV
        oriented_sq = orient(them_pov, sq)
        
        if option == 1:
            # Pawn squares mapped to 0-47, starts at 1
            if p.piece_type == chess.PAWN:
                # pawn plane index: 0 for own Pawn, 1 for enemy Pawn
                pawn_plane = 0 if p.color == them_pov else 1
                plane_offset = 1 + pawn_plane * 48 + (oriented_sq - 8)
            else:
                # other pieces plane offset starts at 1 + 96
                # piece types: knight=2, bishop=3, rook=4, queen=5, king=6
                # own piece is 2 * (pt - 2), enemy piece is 2 * (pt - 2) + 1
                # wait:
                # knight own=0, knight enemy=1, bishop own=2, etc.
                # king own=8. (king enemy is excluded!).
                pt_idx = (p.piece_type - 2) * 2 + (p.color != them_pov)
                plane_offset = 1 + 96 + pt_idx * 64 + oriented_sq
                
            idx = plane_offset + them_king_sq * 685
            enemy_indices.append(idx)
            
        elif option == 2:
            # Pawn squares not mapped (all planes have size 64), starts at 1
            # 11 piece types (king enemy is excluded)
            # pawn own=0, pawn enemy=1, ..., king own=10
            pt_idx = (p.piece_type - 1) * 2 + (p.color != them_pov)
            if pt_idx > 10: # king enemy
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
    
    # 2. Load FC Layers (Main Stack 3, which is for King bucket 3? Or whichever bucket matches the king square!)
    # Let's find the king bucket for the starting position:
    # White King is at E1 (square 4).
    # Since side to move is White, king square is 4.
    # L2+L3 bucket index: i = king_square / 8 = 4 / 8 = 0.
    # L1 bucket index: k = i % 4 = 0.
    # Since i < 4:
    # - L1 parameters are from Main Stack 0! (starts at 47650913)
    # - L2+L3 parameters are from Isolated Bucket 0! (starts at 47646161)
    
    # Let's load L1 parameters from Main Stack 0
    start_l1 = 47650913
    l1_bias = np.frombuffer(file_data[start_l1+4 : start_l1+68], dtype=np.int32)
    l1_weights = np.frombuffer(file_data[start_l1+68 : start_l1+16452], dtype=np.int8).reshape(16, 1024)
    
    # Let's load L2+L3 parameters from Isolated Bucket 0
    start_l2 = 47646161
    l2_bias = np.frombuffer(file_data[start_l2 : start_l2+128], dtype=np.int32)
    l2_weights = np.frombuffer(file_data[start_l2+128 : start_l2+1152], dtype=np.int8).reshape(32, 32)
    l3_bias = struct.unpack('<i', file_data[start_l2+1152 : start_l2+1156])[0]
    l3_weights = np.frombuffer(file_data[start_l2+1156 : start_l2+1188], dtype=np.int8)
    
    # 3. Compute Us Accumulator
    us_indices = get_piece_features(board, True)
    acc_us = friend_bias.astype(np.int32).copy()
    for idx in us_indices:
        acc_us += friend_weights[idx]
        
    # 4. Compute Them Accumulator
    enemy_indices = get_enemy_features(board, True, option)
    acc_them = enemy_bias.astype(np.int32).copy()
    for idx in enemy_indices:
        acc_them += enemy_weights[idx]
        
    # 5. Dual-sided Clipped ReLU on Us and Them
    def dual_clipped_relu(acc):
        # Scale down? No, accumulator is int16 but stored in int32, we scale/clip:
        # standard NNUE Clipped ReLU on accumulator:
        # min(max(0, x), 127)
        # But wait! For dual-sided, we separate positive and negative parts:
        x_pos = np.clip(acc, 0, 127).astype(np.int8)
        x_neg = np.clip(-acc, 0, 127).astype(np.int8)
        return np.concatenate([x_pos, x_neg])
        
    in_l1 = np.concatenate([dual_clipped_relu(acc_us), dual_clipped_relu(acc_them)])
    
    # 6. L1 Forward Pass
    out_l1 = np.dot(l1_weights.astype(np.int32), in_l1.astype(np.int32)) + l1_bias
    
    # Scale down L1 output by 64 and apply dual-sided Clipped ReLU
    out_l1_scaled = out_l1 // 64
    in_l2 = np.concatenate([np.clip(out_l1_scaled, 0, 127).astype(np.int8), np.clip(-out_l1_scaled, 0, 127).astype(np.int8)])
    
    # 7. L2 Forward Pass
    out_l2 = np.dot(l2_weights.astype(np.int32), in_l2.astype(np.int32)) + l2_bias
    
    # Scale down L2 output by 64 and apply standard Clipped ReLU (no dual-sided)
    out_l2_scaled = out_l2 // 64
    in_l3 = np.clip(out_l2_scaled, 0, 127).astype(np.int8)
    
    # 8. L3 Forward Pass
    out_l3 = np.dot(l3_weights.astype(np.int32), in_l3.astype(np.int32)) + l3_bias
    
    # Convert to centipawns. The final score is out_l3.
    # Let's print out_l3!
    print(f"Option {option}: Raw output={out_l3}, in centipawns (divided by 600)={out_l3 / 600.0:.2f} cp")
    return out_l3

if __name__ == '__main__':
    board = chess.Board() # Starting position
    run_forward('nn.nnue', board, option=1)
    run_forward('nn.nnue', board, option=2)
