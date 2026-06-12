import struct
import numpy as np

def search_l2(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    total_size = len(file_data)
    
    # Let's search in the last 50KB of the file
    print("=== Searching for 32 int32 bias arrays in last 50KB ===")
    for offset in range(total_size - 50000, total_size - 128, 4):
        bias = np.frombuffer(file_data[offset:offset+128], dtype=np.int32)
        if np.all(np.abs(bias) < 20000):
            print(f"Offset {offset} (from end {offset - total_size}): min={bias.min()}, max={bias.max()}, mean={bias.mean():.2f}")

if __name__ == '__main__':
    search_l2('nn.nnue')
