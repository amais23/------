import struct
import numpy as np

def print_l2(path):
    with open(path, 'rb') as f:
        f.seek(47645885)
        data = f.read()
        
    # Stack 0 starts at 5028.
    # L1 bias starts at 5032 (64 bytes).
    # L1 weights starts at 5096.
    # L1 weights size = 16 * 510 = 8160.
    # L2 bias should start at 5096 + 8160 = 13256.
    l2_bias_offset = 13256
    
    print(f"L2 bias offset: {l2_bias_offset}")
    l2_bias = np.frombuffer(data[l2_bias_offset : l2_bias_offset + 128], dtype=np.int32)
    print("L2 bias candidate (32 int32s):")
    print(l2_bias)
    
    # Let's print the first 32 bytes of L2 weights (starting after L2 bias)
    # If L2 bias is 16 elements (64 bytes), weights start at 13256 + 64 = 13320.
    weights = np.frombuffer(data[13320 : 13320 + 32], dtype=np.int8)
    print("L2 weights (first 32 bytes if L2 bias size is 16):")
    print(weights)
    
    # If L2 bias is 32 elements (128 bytes), weights start at 13256 + 128 = 13384.
    weights_32 = np.frombuffer(data[13384 : 13384 + 32], dtype=np.int8)
    print("L2 weights (first 32 bytes if L2 bias size is 32):")
    print(weights_32)

if __name__ == '__main__':
    print_l2('nn.nnue')
