import struct
import numpy as np

def print_biases(path):
    with open(path, 'rb') as f:
        f.seek(47645885)
        data = f.read()
        
    offsets = [5028, 22668, 40308, 57948]
    
    for i, offset in enumerate(offsets):
        print(f"\n--- Stack {i} at offset {offset} ---")
        fc_hash = struct.unpack('<I', data[offset:offset+4])[0]
        print(f"fc_hash: 0x{fc_hash:08x}")
        
        # Interpret 32 int32s after fc_hash
        bias = np.frombuffer(data[offset+4 : offset+4+128], dtype=np.int32)
        print("L1 bias candidate (32 int32s):")
        print(bias)
        
        # Interpret next 32 int32s (just to see if they continue to be small or not)
        next_ints = np.frombuffer(data[offset+4+128 : offset+4+256], dtype=np.int32)
        print("Next 32 int32s:")
        print(next_ints)

if __name__ == '__main__':
    print_biases('nn.nnue')
