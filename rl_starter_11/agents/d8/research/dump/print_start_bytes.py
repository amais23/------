import struct
import numpy as np

def print_start(path):
    with open(path, 'rb') as f:
        f.seek(47645885)
        data = f.read(300)
        
    print("First 300 bytes of remaining section:")
    # Print as int32
    int32s = np.frombuffer(data[:280], dtype=np.int32)
    for i, val in enumerate(int32s[:20]):
        print(f"Int32 {i} (offset {47645885 + i*4}): {val} (hex: 0x{val:08x})")
        
    print("\nFirst 40 bytes as hex:")
    print(data[:40].hex())

if __name__ == '__main__':
    print_start('nn.nnue')
