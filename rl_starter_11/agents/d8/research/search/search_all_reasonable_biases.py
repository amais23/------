import struct
import numpy as np

def search(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    total_size = len(file_data)
    print(f"Total size: {total_size}")
    
    # 1. Search for 256-sized int16 bias arrays (512 bytes)
    # The bias values should be small (e.g., between -32768 and 32767, but typically between -2000 and 20000).
    print("\n=== Searching for 256-sized int16 bias arrays ===")
    for offset in range(0, total_size - 512, 2):
        bias = np.frombuffer(file_data[offset:offset+512], dtype=np.int16)
        if np.all(np.abs(bias) < 30000):
            # To avoid printing consecutive matches, let's only print if standard deviation is substantial
            std = bias.std()
            if std > 5.0 and std < 5000.0:
                # Print only if it's the start of a block
                # Let's check if the previous offset was not matching
                print(f"Offset {offset} (from end {offset - total_size}): min={bias.min()}, max={bias.max()}, mean={bias.mean():.2f}, std={std:.2f}")

    # 2. Search for 32-sized int32 bias arrays (128 bytes)
    # The bias values should be small (e.g., between -100000 and 100000).
    print("\n=== Searching for 32-sized int32 bias arrays ===")
    for offset in range(0, total_size - 128, 4):
        bias = np.frombuffer(file_data[offset:offset+128], dtype=np.int32)
        if np.all(np.abs(bias) < 500000):
            std = bias.std()
            if std > 5.0:
                print(f"Offset {offset} (from end {offset - total_size}): min={bias.min()}, max={bias.max()}, mean={bias.mean():.2f}, std={std:.2f}")

if __name__ == '__main__':
    search('nn.nnue')
