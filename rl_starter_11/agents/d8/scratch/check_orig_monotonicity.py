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
    them_king_sq = orient(them_pov, board.king(them_pov))
    enemy_indices = []
    for sq, p in board.piece_map().items():
        if p.piece_type == chess.KING and p.color == is_white_pov:
            continue
        oriented_sq = orient(them_pov, sq)
        if p.piece_type == chess.PAWN:
            pawn_plane = 0 if p.color == them_pov else 1
            plane_offset = 1 + pawn_plane * 48 + (oriented_sq - 8)
        else:
            pt_idx = (p.piece_type - 2) * 2 + (p.color != them_pov)
            plane_offset = 1 + 96 + pt_idx * 64 + oriented_sq
        idx = plane_offset + them_king_sq * 685
        enemy_indices.append(idx)
    return enemy_indices

def run_forward(path, board, divide_by_127):
    with open(path, 'rb') as f:
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
    start_stack = 47650913 + stack_idx * 17640
    
    l1_bias = np.frombuffer(file_data[start_stack+4 : start_stack+68], dtype=np.int32)
    l1_weights = np.frombuffer(file_data[start_stack+68 : start_stack+16452], dtype=np.int8).reshape(16, 1024)
    
    if bucket_us < 4:
        iso_start = fc_start + bucket_us * 1192
        l2_bias = np.frombuffer(file_data[iso_start+4 : iso_start + 132], dtype=np.int32)
        l2_weights = np.frombuffer(file_data[iso_start + 132 : iso_start + 1156], dtype=np.int8).reshape(32, 32)
        l3_bias = struct.unpack('<i', file_data[iso_start + 1156 : iso_start + 1160])[0]
        l3_weights = np.frombuffer(file_data[iso_start + 1160 : iso_start + 1192], dtype=np.int8)
    else:
        l2_bias = np.frombuffer(file_data[start_stack+16452 : start_stack+16580], dtype=np.int32)
        l2_weights = np.frombuffer(file_data[start_stack+16580 : start_stack+17604], dtype=np.int8).reshape(32, 32)
        l3_bias = struct.unpack('<i', file_data[start_stack+17604 : start_stack+17608])[0]
        l3_weights = np.frombuffer(file_data[start_stack+17608 : start_stack+17640], dtype=np.int8)
        
    us_indices = get_piece_features(board, board.turn == chess.WHITE)
    acc_us = friend_bias.astype(np.int32).copy()
    for idx in us_indices:
        acc_us += friend_weights[idx].astype(np.int32)
        
    enemy_indices = get_enemy_features(board, board.turn == chess.WHITE)
    acc_them = enemy_bias.astype(np.int32).copy()
    for idx in enemy_indices:
        acc_them += enemy_weights[idx].astype(np.int32)
        
    def activate(acc):
        if divide_by_127:
            # Floor division by 127
            acc_scaled = acc // 127
            return np.clip(acc_scaled, 0, 127).astype(np.int8)
        else:
            return np.clip(acc, 0, 127).astype(np.int8)
        
    in_l1 = np.concatenate([activate(acc_us), activate(-acc_us), activate(acc_them), activate(-acc_them)])
    
    out_l1 = np.dot(l1_weights.astype(np.int32), in_l1.astype(np.int32)) + l1_bias
    out_l1_scaled = out_l1 // 64
    in_l2 = np.concatenate([np.clip(out_l1_scaled, 0, 127).astype(np.int8), np.clip(-out_l1_scaled, 0, 127).astype(np.int8)])
    
    out_l2 = np.dot(l2_weights.astype(np.int32), in_l2.astype(np.int32)) + l2_bias
    out_l2_scaled = out_l2 // 64
    in_l3 = np.clip(out_l2_scaled, 0, 127).astype(np.int8)
    
    out_l3 = np.dot(l3_weights.astype(np.int32), in_l3.astype(np.int32)) + l3_bias
    return out_l3

def test():
    positions = {
        "Start": chess.Board(),
        "Up Pawn (d7)": chess.Board("rnbqkbnr/ppp1pppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        "Down Pawn (d2)": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPP1PPPP/RNBQKBNR w KQkq - 0 1"),
        "Up Knight (g8)": chess.Board("rnbqkb1r/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        "Down Knight (g1)": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKB1R w KQkq - 0 1"),
        "Up Queen (d8)": chess.Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        "Down Queen (d1)": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1"),
        "K+Q vs K": chess.Board("k7/8/8/8/8/8/8/K1Q5 w - - 0 1"),
        "K+R vs K": chess.Board("k7/8/8/8/8/8/8/K1R5 w - - 0 1"),
        "KvK": chess.Board("k7/8/8/8/8/8/8/K7 w - - 0 1"),
        "K vs K+R": chess.Board("k7/8/8/8/8/8/8/K1R5 b - - 0 1")
    }
    
    for divide in [True, False]:
        print(f"\n================ Divide by 127 = {divide} ================")
        print(f"{'Position':<20} | {'Score':<8} | {'Diff':<8}")
        print("-" * 40)
        start_score = None
        for name, b in positions.items():
            score = run_forward('weights/nn.nnue.orig', b, divide)
            if start_score is None:
                start_score = score
                diff = 0
            else:
                diff = score - start_score
            print(f"{name:<20} | {score:<8} | {diff:<8}")

if __name__ == '__main__':
    test()
