import struct
import numpy as np
import chess
from itertools import permutations

def orient(is_white_pov: bool, sq: int):
    return sq ^ 56 if not is_white_pov else sq

def get_piece_features_custom(board: chess.Board, is_white_pov: bool, pt_order, invert_us_color):
    king_sq = orient(is_white_pov, board.king(is_white_pov))
    us_indices = []
    for sq, p in board.piece_map().items():
        is_enemy = (p.color != is_white_pov)
        if invert_us_color:
            is_enemy = not is_enemy
        p_idx = pt_order[p.piece_type] * 2 + int(is_enemy)
        oriented_sq = orient(is_white_pov, sq)
        idx = 1 + oriented_sq + p_idx * 64 + king_sq * 769
        us_indices.append(idx)
    return us_indices

def get_enemy_features_custom(board: chess.Board, is_white_pov: bool, pt_order, invert_them_color, invert_pawn_plane):
    them_pov = not is_white_pov
    king_sq = orient(them_pov, board.king(them_pov))
    enemy_indices = []
    for sq, p in board.piece_map().items():
        if p.piece_type == chess.KING and p.color == is_white_pov:
            continue
        oriented_sq = orient(them_pov, sq)
        if p.piece_type == chess.PAWN:
            pawn_plane = 0 if p.color == them_pov else 1
            if invert_pawn_plane:
                pawn_plane = 1 - pawn_plane
            plane_offset = 1 + pawn_plane * 48 + (oriented_sq - 8)
        else:
            pt_idx = (pt_order[p.piece_type] - 1) * 2 + (p.color != them_pov)
            if invert_them_color:
                pt_idx = (pt_order[p.piece_type] - 1) * 2 + (p.color == them_pov)
            plane_offset = 1 + 96 + pt_idx * 64 + oriented_sq
        idx = plane_offset + king_sq * 685
        enemy_indices.append(idx)
    return enemy_indices

def run_forward_custom(file_data, board, pt_order, invert_us_color, invert_them_color, invert_pawn_plane):
    # Load weights
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
    
    if bucket_us < 4:
        iso_start = fc_start + 272 + bucket_us * 1192
        l2_bias = np.frombuffer(file_data[iso_start : iso_start + 128], dtype=np.int32)
        l2_weights = np.frombuffer(file_data[iso_start + 128 : iso_start + 1152], dtype=np.int8).reshape(32, 32)
        l3_bias = struct.unpack('<i', file_data[iso_start + 1152 : iso_start + 1156])[0]
        l3_weights = np.frombuffer(file_data[iso_start + 1156 : iso_start + 1188], dtype=np.int8)
    else:
        l2_bias = np.frombuffer(file_data[start_stack+16516 : start_stack+16644], dtype=np.int32)
        l2_weights = np.frombuffer(file_data[start_stack+16644 : start_stack+17668], dtype=np.int8).reshape(32, 32)
        l3_bias = struct.unpack('<i', file_data[start_stack+17604 : start_stack+17608])[0]
        l3_weights = np.frombuffer(file_data[start_stack+17608 : start_stack+17640], dtype=np.int8)
        
    us_indices = get_piece_features_custom(board, board.turn == chess.WHITE, pt_order, invert_us_color)
    acc_us = friend_bias.astype(np.int32).copy()
    for idx in us_indices:
        acc_us += friend_weights[idx].astype(np.int32)
        
    enemy_indices = get_enemy_features_custom(board, board.turn == chess.WHITE, pt_order, invert_them_color, invert_pawn_plane)
    acc_them = enemy_bias.astype(np.int32).copy()
    for idx in enemy_indices:
        acc_them += enemy_weights[idx].astype(np.int32)
        
    def activate(acc):
        return np.clip(acc // 8, 0, 127).astype(np.int8)
        
    in_l1 = np.concatenate([activate(acc_us), activate(acc_them)])
    
    out_l1 = np.dot(l1_weights.astype(np.int32), in_l1.astype(np.int32)) + l1_bias
    out_l1_scaled = out_l1 // 64
    in_l2 = np.clip(out_l1_scaled, 0, 127).astype(np.int8)
    
    out_l2 = np.dot(l2_weights.astype(np.int32), in_l2.astype(np.int32)) + l2_bias
    out_l2_scaled = out_l2 // 64
    in_l3 = np.clip(out_l2_scaled, 0, 127).astype(np.int8)
    
    out_l3 = np.dot(l3_weights.astype(np.int32), in_l3.astype(np.int32)) + l3_bias
    return out_l3

def test():
    with open('agents/d8/weights/nn.nnue', 'rb') as f:
        file_data = f.read()
        
    positions = {
        "Start": chess.Board(),
        "Up Pawn (d7)": chess.Board("rnbqkbnr/ppp1pppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        "Down Pawn (d2)": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPP1PPPP/RNBQKBNR w KQkq - 0 1"),
        "Up Knight (g8)": chess.Board("rnbqkb1r/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        "Down Knight (g1)": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKB1R w KQkq - 0 1"),
        "Up Bishop (f8)": chess.Board("rnbqk1nr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        "Down Bishop (f1)": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK1NR w KQkq - 0 1"),
        "Up Rook (a8)": chess.Board("1nbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        "Down Rook (a1)": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBNR w KQkq - 0 1"),
        "Up Queen (d8)": chess.Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        "Down Queen (d1)": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1")
    }
    
    # Let's search over all permutations of Pawn(1), Knight(2), Bishop(3), Rook(4), Queen(5), King(6)
    # Pawn is 0 (first plane), and other 5 pieces map to 1-5.
    other_pieces = [2, 3, 4, 5, 6]
    
    print("Searching permutations...")
    count = 0
    for perm in permutations(other_pieces):
        pt_order = {
            chess.PAWN: 0,
            perm[0]: 1,
            perm[1]: 2,
            perm[2]: 3,
            perm[3]: 4,
            perm[4]: 5
        }
        for invert_us in [False, True]:
            for invert_them in [False, True]:
                for invert_pawn in [False, True]:
                    # Test monotonicity
                    start = run_forward_custom(file_data, positions["Start"], pt_order, invert_us, invert_them, invert_pawn)
                    up_p = run_forward_custom(file_data, positions["Up Pawn (d7)"], pt_order, invert_us, invert_them, invert_pawn)
                    dn_p = run_forward_custom(file_data, positions["Down Pawn (d2)"], pt_order, invert_us, invert_them, invert_pawn)
                    up_n = run_forward_custom(file_data, positions["Up Knight (g8)"], pt_order, invert_us, invert_them, invert_pawn)
                    dn_n = run_forward_custom(file_data, positions["Down Knight (g1)"], pt_order, invert_us, invert_them, invert_pawn)
                    up_b = run_forward_custom(file_data, positions["Up Bishop (f8)"], pt_order, invert_us, invert_them, invert_pawn)
                    dn_b = run_forward_custom(file_data, positions["Down Bishop (f1)"], pt_order, invert_us, invert_them, invert_pawn)
                    up_r = run_forward_custom(file_data, positions["Up Rook (a8)"], pt_order, invert_us, invert_them, invert_pawn)
                    dn_r = run_forward_custom(file_data, positions["Down Rook (a1)"], pt_order, invert_us, invert_them, invert_pawn)
                    up_q = run_forward_custom(file_data, positions["Up Queen (d8)"], pt_order, invert_us, invert_them, invert_pawn)
                    dn_q = run_forward_custom(file_data, positions["Down Queen (d1)"], pt_order, invert_us, invert_them, invert_pawn)
                    
                    is_monotonic = (
                        abs(start) < 20000 and
                        up_p > start and dn_p < start and
                        up_n > start and dn_n < start and
                        up_b > start and dn_b < start and
                        up_r > start and dn_r < start and
                        up_q > start and dn_q < start
                    )
                    
                    if is_monotonic:
                        print(f"FOUND MONOTONIC CONFIGURATION:")
                        print(f"  perm: {perm}")
                        print(f"  invert_us: {invert_us}")
                        print(f"  invert_them: {invert_them}")
                        print(f"  invert_pawn: {invert_pawn}")
                        print(f"  Start  : {start}")
                        print(f"  Pawn   : Up={up_p - start:+}, Down={dn_p - start:+}")
                        print(f"  Knight : Up={up_n - start:+}, Down={dn_n - start:+}")
                        print(f"  Bishop : Up={up_b - start:+}, Down={dn_b - start:+}")
                        print(f"  Rook   : Up={up_r - start:+}, Down={dn_r - start:+}")
                        print(f"  Queen  : Up={up_q - start:+}, Down={dn_q - start:+}")
                        return
                    count += 1
                    if count % 1000 == 0:
                        pass
                        
    print("Exhausted all configurations. No monotonic configuration found.")

if __name__ == '__main__':
    test()
