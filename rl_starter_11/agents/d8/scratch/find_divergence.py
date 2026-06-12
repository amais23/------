import struct
import numpy as np
import chess

# Paste code from debug_forward_pass
def debug_run(path, board):
    with open(path, 'rb') as f:
        file_data = f.read()
    friend_bias = np.frombuffer(file_data[189 : 189 + 512], dtype=np.int16)
    friend_weights = np.frombuffer(file_data[705 : 705 + 49216 * 256 * 2], dtype=np.int16).reshape(49216, 256)
    enemy_bias = np.frombuffer(file_data[25199293 : 25199293 + 512], dtype=np.int16)
    enemy_weights = np.frombuffer(file_data[25199809 : 25199809 + 43840 * 256 * 2], dtype=np.int16).reshape(43840, 256)
    
    start_l1 = 47703833
    l1_bias = np.frombuffer(file_data[start_l1+4 : start_l1+68], dtype=np.int32)
    l1_weights = np.frombuffer(file_data[start_l1+68 : start_l1+16452], dtype=np.int8).reshape(16, 1024)
    l2_bias = np.frombuffer(file_data[start_l1+16452 : start_l1+16452+128], dtype=np.int32)
    l2_weights = np.frombuffer(file_data[start_l1+16580 : start_l1+16580+1024], dtype=np.int8).reshape(32, 32)
    l3_bias = struct.unpack('<i', file_data[start_l1+17604 : start_l1+17608])[0]
    l3_weights = np.frombuffer(file_data[start_l1+17608 : start_l1+17640], dtype=np.int8)
    
    from scratch.check_monotonicity_options import get_piece_features, get_enemy_features
    us_indices = get_piece_features(board, True)
    acc_us = friend_bias.astype(np.int32).copy()
    for idx in us_indices:
        acc_us += friend_weights[idx].astype(np.int32)
        
    enemy_indices = get_enemy_features(board, True, 1)
    acc_them = enemy_bias.astype(np.int32).copy()
    for idx in enemy_indices:
        acc_them += enemy_weights[idx].astype(np.int32)
        
    def dual_clipped_relu(acc):
        acc_scaled = acc // 127
        x_pos = np.clip(acc_scaled, 0, 127).astype(np.int8)
        x_neg = np.clip(-acc_scaled, 0, 127).astype(np.int8)
        return np.concatenate([x_pos, x_neg])
        
    in_l1 = np.concatenate([dual_clipped_relu(acc_us), dual_clipped_relu(acc_them)])
    print("DEBUG RUN acc_us mean:", np.mean(acc_us), "sum:", np.sum(acc_us))
    print("DEBUG RUN acc_them mean:", np.mean(acc_them), "sum:", np.sum(acc_them))
    print("DEBUG RUN in_l1 sum:", np.sum(in_l1))
    
    out_l1 = np.dot(l1_weights.astype(np.int32), in_l1.astype(np.int32)) + l1_bias
    out_l1_scaled = out_l1 // 64
    in_l2 = np.concatenate([np.clip(out_l1_scaled, 0, 127).astype(np.int8), np.clip(-out_l1_scaled, 0, 127).astype(np.int8)])
    print("DEBUG RUN out_l1:", out_l1)
    print("DEBUG RUN in_l2:", in_l2)
    
    out_l2 = np.dot(l2_weights.astype(np.int32), in_l2.astype(np.int32)) + l2_bias
    out_l2_scaled = out_l2 // 64
    in_l3 = np.clip(out_l2_scaled, 0, 127).astype(np.int8)
    print("DEBUG RUN out_l2:", out_l2)
    print("DEBUG RUN in_l3:", in_l3)
    
    out_l3 = np.dot(l3_weights.astype(np.int32), in_l3.astype(np.int32)) + l3_bias
    return out_l3

# Paste code from check_monotonicity_options
from scratch.check_monotonicity_options import run_forward

def test():
    positions = {
        "Start": chess.Board(),
        "Won (Up Queen)": chess.Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        "Lost (Down Queen)": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1")
    }
    for name, board in positions.items():
        v_debug = debug_run('agents/d8/weights/nn.nnue', board)
        print(f"{name}: {v_debug}")

if __name__ == '__main__':
    test()
