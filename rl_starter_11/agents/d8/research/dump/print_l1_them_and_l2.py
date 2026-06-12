import struct
import numpy as np

def print_biases(path):
    with open(path, 'rb') as f:
        f.seek(47645885)
        data = f.read()
        
    stack_start = 5028
    
    # 1. L1_Them bias starts at:
    # stack_start + 4 (hash) + 64 (L1_Us bias) + 16 * 255 (L1_Us weights)
    # Let's assume M.L1 is 255. 16 * 255 = 4080.
    # Total offset = 5028 + 4 + 64 + 4080 = 9176.
    print("\n--- L1_Them bias candidate at relative offset 9176 ---")
    l1_them_bias = np.frombuffer(data[9176 : 9176 + 64], dtype=np.int32)
    print(l1_them_bias)
    
    # 2. L2 bias starts at:
    # stack_start + 4 + 64 + 4080 + 64 (L1_Them bias) + 4080 (L1_Them weights)
    # Total offset = 5028 + 4 + 64 + 4080 + 64 + 4080 = 13320.
    print("\n--- L2 bias candidate at relative offset 13320 ---")
    l2_bias = np.frombuffer(data[13320 : 13320 + 128], dtype=np.int32)
    print(l2_bias)

if __name__ == '__main__':
    print_biases('nn.nnue')
