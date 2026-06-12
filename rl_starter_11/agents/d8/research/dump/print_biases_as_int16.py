import struct
import numpy as np

def print_int16(path):
    with open(path, 'rb') as f:
        f.seek(47645885)
        data = f.read()
        
    offsets = [5028, 22668, 40308, 57948]
    
    for i, offset in enumerate(offsets):
        print(f"\n--- Stack {i} at offset {offset} ---")
        # Read 64 bytes after fc_hash
        bias_bytes = data[offset+4 : offset+4+64]
        bias_int16 = np.frombuffer(bias_bytes, dtype=np.int16)
        print("As 32 int16s:")
        print(bias_int16)
        
        # Let's also print them as 16 int32s to compare
        bias_int32 = np.frombuffer(bias_bytes, dtype=np.int32)
        print("As 16 int32s:")
        print(bias_int32)

if __name__ == '__main__':
    print_int16('nn.nnue')
