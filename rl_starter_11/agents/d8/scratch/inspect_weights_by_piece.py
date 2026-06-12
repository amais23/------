import numpy as np

def inspect():
    with open('agents/d8/weights/nn.nnue', 'rb') as f:
        file_data = f.read()
        
    friend_weights = np.frombuffer(file_data[705 : 705 + 49216 * 256 * 2], dtype=np.int16).reshape(49216, 256)
    enemy_weights = np.frombuffer(file_data[25199809 : 25199809 + 43840 * 256 * 2], dtype=np.int16).reshape(43840, 256)
    
    piece_names = ["Pawn", "Knight", "Bishop", "Rook", "Queen", "King"]
    
    print("=== Friend Weights (Us) ===")
    # For a fixed king square, say e1 (square 4)
    king_sq = 4
    for pt in range(1, 7):
        for is_enemy in [0, 1]:
            p_idx = (pt - 1) * 2 + is_enemy
            # Sum of weights over all 64 squares
            weights_sum = 0.0
            for sq in range(64):
                idx = 1 + sq + p_idx * 64 + king_sq * 769
                weights_sum += np.mean(friend_weights[idx])
            name = f"{'Enemy' if is_enemy else 'Own'} {piece_names[pt-1]}"
            print(f"  {name:15}: Mean weight sum = {weights_sum:.4f}")
            
    print("\n=== Enemy Weights (Them) ===")
    # For a fixed king square, say e8 (square 60 oriented to 4)
    king_sq = 4
    for pt in range(1, 7):
        for is_enemy in [0, 1]:
            if pt == 6 and not is_enemy: # Opponent's King is excluded from Enemy FT
                continue
            weights_sum = 0.0
            for sq in range(64):
                if pt == 1:
                    pawn_plane = 0 if not is_enemy else 1
                    # Pawn only exists on ranks 2-7 (squares 8 to 55)
                    for pawn_sq in range(8, 56):
                        plane_offset = 1 + pawn_plane * 48 + (pawn_sq - 8)
                        idx = plane_offset + king_sq * 685
                        weights_sum += np.mean(enemy_weights[idx])
                    weights_sum = weights_sum * (64.0 / 48.0) # normalize
                    break
                else:
                    pt_idx = (pt - 2) * 2 + is_enemy
                    plane_offset = 1 + 96 + pt_idx * 64 + sq
                    idx = plane_offset + king_sq * 685
                    weights_sum += np.mean(enemy_weights[idx])
            name = f"{'Enemy' if is_enemy else 'Own'} {piece_names[pt-1]}"
            print(f"  {name:15}: Mean weight sum = {weights_sum:.4f}")

if __name__ == '__main__':
    inspect()
