import struct
import numpy as np

def check():
    with open('weights/nn.nnue', 'rb') as f:
        file_data = f.read()
        
    fc_start = 47645889
    main_start = fc_start + 4768 + 256 # 47650913
    
    for i in range(4):
        stack_offset = main_start + i * 17640
        print(f"\nMain Stack {i} (offset {stack_offset}):")
        
        # Load L1 bias (16 int32 = 64 bytes)
        l1_bias = np.frombuffer(file_data[stack_offset+4 : stack_offset+68], dtype=np.int32)
        # Load L2 bias (32 int32 = 128 bytes)
        l2_bias = np.frombuffer(file_data[stack_offset+68+16384 : stack_offset+68+16384+128], dtype=np.int32)
        # Load L3 bias (1 int32 = 4 bytes)
        l3_bias = struct.unpack('<i', file_data[stack_offset+68+16384+128+1024 : stack_offset+68+16384+128+1024+4])[0]
        
        print(f"  L1 bias: min={l1_bias.min()}, max={l1_bias.max()}, mean={l1_bias.mean():.2f}")
        print(f"  L1 bias values: {l1_bias}")
        print(f"  L2 bias: min={l2_bias.min()}, max={l2_bias.max()}, mean={l2_bias.mean():.2f}")
        print(f"  L2 bias values: {l2_bias[:8]}")
        print(f"  L3 bias: {l3_bias}")

if __name__ == '__main__':
    check()
