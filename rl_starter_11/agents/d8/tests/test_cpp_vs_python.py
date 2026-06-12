import sys
import os
import struct
import numpy as np
import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import chess_engine_d8_han

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

def py_evaluate(board: chess.Board, weights_path='weights/nn.nnue'):
    with open(weights_path, 'rb') as f:
        file_data = f.read()
    
    # 1. Load FT Layers
    friend_bias = np.frombuffer(file_data[193 : 193 + 512], dtype=np.int16)
    friend_weights = np.frombuffer(file_data[705 : 705 + 49216 * 256 * 2], dtype=np.int16).reshape(49216, 256)
    enemy_bias = np.frombuffer(file_data[25199297 : 25199297 + 512], dtype=np.int16)
    enemy_weights = np.frombuffer(file_data[25199809 : 25199809 + 43840 * 256 * 2], dtype=np.int16).reshape(43840, 256)
    
    # 2. Get oriented King square & bucket
    side_pov = 0 if board.turn == chess.WHITE else 1
    oriented_king_us = orient(side_pov == 0, board.king(board.turn))
    bucket_us = 7 - (oriented_king_us // 8)
    
    fc_start = 47645889
    stack_idx = bucket_us % 4
    start_stack = fc_start + 272 + 4 * 1188 + stack_idx * 17640
    
    l1_bias = np.frombuffer(file_data[start_stack+4 : start_stack+68], dtype=np.int32)
    l1_weights = np.frombuffer(file_data[start_stack+68 : start_stack+16452], dtype=np.int8).reshape(16, 1024)
    
    # Load L2/L3 weights based on bucket_us
    if bucket_us < 4:
        iso_start = fc_start + 272 + bucket_us * 1188
        l2_bias = np.frombuffer(file_data[iso_start : iso_start + 128], dtype=np.int32)
        l2_weights = np.frombuffer(file_data[iso_start + 128 : iso_start + 1152], dtype=np.int8).reshape(32, 32)
        l3_bias = struct.unpack('<i', file_data[iso_start + 1152 : iso_start + 1156])[0]
        l3_weights = np.frombuffer(file_data[iso_start + 1156 : iso_start + 1188], dtype=np.int8)
    else:
        l2_bias = np.frombuffer(file_data[start_stack+16452 : start_stack+16580], dtype=np.int32)
        l2_weights = np.frombuffer(file_data[start_stack+16580 : start_stack+17604], dtype=np.int8).reshape(32, 32)
        l3_bias = struct.unpack('<i', file_data[start_stack+17604 : start_stack+17608])[0]
        l3_weights = np.frombuffer(file_data[start_stack+17608 : start_stack+17640], dtype=np.int8)
        
    # 4. Compute Us Accumulator
    us_indices = get_piece_features(board, board.turn == chess.WHITE)
    acc_us = friend_bias.astype(np.int32).copy()
    for idx in us_indices:
        acc_us += friend_weights[idx].astype(np.int32)
        
    # 5. Compute Them Accumulator
    enemy_indices = get_enemy_features(board, board.turn == chess.WHITE)
    acc_them = enemy_bias.astype(np.int32).copy()
    for idx in enemy_indices:
        acc_them += enemy_weights[idx].astype(np.int32)
        
    # 6. Clipped ReLU Activations (Division Factor 1)
    def activate(acc):
        x_pos = np.clip(acc, 0, 127).astype(np.int8)
        x_neg = np.clip(-acc, 0, 127).astype(np.int8)
        return np.concatenate([x_pos, x_neg])
        
    in_l1 = np.concatenate([activate(acc_us), activate(acc_them)])
    
    # 7. L1 Propagation
    out_l1 = np.dot(l1_weights.astype(np.int32), in_l1.astype(np.int32)) + l1_bias
    out_l1_scaled = out_l1 // 64
    in_l2 = np.concatenate([np.clip(out_l1_scaled, 0, 127).astype(np.int8), np.clip(-out_l1_scaled, 0, 127).astype(np.int8)])
    
    # 8. L2 Propagation
    out_l2 = np.dot(l2_weights.astype(np.int32), in_l2.astype(np.int32)) + l2_bias
    out_l2_scaled = out_l2 // 64
    in_l3 = np.clip(out_l2_scaled, 0, 127).astype(np.int8)
    
    # 9. L3 Propagation
    out_l3 = np.dot(l3_weights.astype(np.int32), in_l3.astype(np.int32)) + l3_bias
    return out_l3

def test():
    engine = chess_engine_d8_han.SearchEngineD8()
    engine.init("")
    
    positions = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", # Start
        "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", # Won (missing Black Queen)
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1", # Lost (missing White Queen)
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1", # After 1. e4
        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3", # Open game
        "rnb1kbnr/ppp2ppp/3p4/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3", # Fool's mate position
    ]
    
    print("Comparing Python and C++ evaluations...")
    for i, fen in enumerate(positions):
        board = chess.Board(fen)
        py_val = py_evaluate(board)
        cpp_val = engine.evaluate_nnue_direct(fen)
        print(f"FEN {i+1}: {fen}")
        print(f"  Python: {py_val}")
        print(f"  C++:    {cpp_val}")
        assert py_val == cpp_val, f"Mismatch at FEN {i+1}! Python={py_val}, C++={cpp_val}"
        print(f"  ✅ Matches exactly!")

    print("🎉 All Python vs C++ direct comparisons match exactly!")

if __name__ == '__main__':
    test()
