import struct
import numpy as np

def print_first_l2(path):
    with open(path, 'rb') as f:
        f.seek(47645885)
        data = f.read(5028)
        
    offsets = [0, 1188, 2376, 3564]
    for i, offset in enumerate(offsets):
        print(f"\n--- Bucket {i} L2 bias candidate at relative offset {offset} ---")
        bias = np.frombuffer(data[offset : offset + 128], dtype=np.int32)
        print(f"Bias: min={bias.min()}, max={bias.max()}, mean={bias.mean():.2f}")
        print(f"Values: {bias[:8]}")

if __name__ == '__main__':
    print_first_l2('nn.nnue')
