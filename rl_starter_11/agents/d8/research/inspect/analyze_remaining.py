import struct
import numpy as np

def analyze(path):
    with open(path, 'rb') as f:
        f.seek(47645885)
        data = f.read()
    
    print(f"Remaining bytes: {len(data)}")
    
    # In Stockfish NNUE, the layers are written using:
    # write_layer(f)
    # Let's inspect if there are headers.
    # A layer header is typically 4 bytes type, 4 bytes hash (or similar).
    # Let's look at the data as signed 8-bit integers, 16-bit integers, and 32-bit integers.
    # Let's print out the first 64 bytes as hex and as various types
    print("First 64 bytes hex:")
    print(data[:64].hex())
    
    # Let's look at where the data becomes zero or has high/low values.
    # Let's see if we can find any pattern.
    # What if the remaining 75588 bytes contains:
    # 1. Something else?
    # Let's check if there are 4 subnetworks of L1:
    # L1: 4 * (128 + 16384) = 66,048 bytes
    # L2: 4 * (128 + 1024) = 4,608 bytes
    # L3: 4 * (4 + 32) = 144 bytes
    # Total = 66048 + 4608 + 144 = 70,800 bytes.
    # Plus some headers?
    # If there are 4 subnetworks, then we have 70,800 bytes of weights/biases.
    # What if there are 4 subnetworks?
    # Let's check if the total size 75,588 is close to that!
    # Let's write a script to plot or show statistics of the bytes.
    
    # Let's compute mean and variance of 8-bit blocks:
    print("\n--- Statistics of blocks of size 16384 (as int8) ---")
    for i in range(4):
        offset = i * 16384
        if offset + 16384 <= len(data):
            block = np.frombuffer(data[offset:offset+16384], dtype=np.int8)
            print(f"Block {i} (offset {offset}): min={block.min()}, max={block.max()}, mean={block.mean():.4f}, std={block.std():.4f}")
            
if __name__ == '__main__':
    analyze('nn.nnue')
