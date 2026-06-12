import struct
import numpy as np

def search(path):
    with open(path, 'rb') as f:
        f.seek(47645885)
        data = f.read()
    
    total_size = len(data)
    print(f"Total remaining size: {total_size}")
    
    # Search for L1/L2 biases: 32 int32s (128 bytes)
    # The bias values should be small, e.g., |val| < 30000, and std > 5.0
    print("\n=== Searching for 32 int32 bias arrays ===")
    matches = []
    offset = 0
    while offset <= total_size - 128:
        bias = np.frombuffer(data[offset:offset+128], dtype=np.int32)
        if np.all(np.abs(bias) < 50000) and bias.std() > 5.0:
            print(f"Found reasonable bias at relative offset {offset} (absolute {47645885 + offset}, from end {offset - total_size}):")
            print(f"  min={bias.min()}, max={bias.max()}, mean={bias.mean():.2f}, std={bias.std():.2f}")
            print(f"  values: {bias[:8]}")
            matches.append(offset)
            # Skip past this bias to avoid printing overlapping candidates
            offset += 128
        else:
            offset += 4

if __name__ == '__main__':
    search('nn.nnue')
