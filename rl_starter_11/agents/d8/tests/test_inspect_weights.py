import numpy as np

def inspect(path):
    with open(path, 'rb') as f:
        file_data = f.read()
        
    weights = np.frombuffer(file_data[705 : 705 + 49216 * 256 * 2], dtype=np.int16).reshape(49216, 256)
    
    # White Queen on d1 is index 3592
    q_weights = weights[3592]
    print(f"White Queen on d1 (index 3592) weights:")
    print(f"  Min/Max/Mean: {q_weights.min()}, {q_weights.max()}, {q_weights.mean():.4f}")
    print(f"  Abs sum: {np.abs(q_weights).sum()}")
    print(f"  First 20 elements: {list(q_weights[:20])}")
    
    # White Pawn on a2 is index 3085
    p_weights = weights[3085]
    print(f"\nWhite Pawn on a2 (index 3085) weights:")
    print(f"  Min/Max/Mean: {p_weights.min()}, {p_weights.max()}, {p_weights.mean():.4f}")
    print(f"  Abs sum: {np.abs(p_weights).sum()}")
    
    # White King on e1 is index 3721
    k_weights = weights[3721]
    print(f"\nWhite King on e1 (index 3721) weights:")
    print(f"  Min/Max/Mean: {k_weights.min()}, {k_weights.max()}, {k_weights.mean():.4f}")
    print(f"  Abs sum: {np.abs(k_weights).sum()}")

if __name__ == '__main__':
    inspect('weights/nn.nnue')
