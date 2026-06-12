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
        
        # Load L1 bias as 32 int16_t (64 bytes)
        l1_bias = np.frombuffer(file_data[stack_offset+4 : stack_offset+68], dtype=np.int16)
        # Load L1 weights as 32x512 int8 (16384 bytes)
        l1_weights = np.frombuffer(file_data[stack_offset+68 : stack_offset+16452], dtype=np.int8).reshape(32, 512)
        
        print(f"  L1 bias: min={l1_bias.min()}, max={l1_bias.max()}, mean={l1_bias.mean():.2f}")
        print(f"  L1 bias values: {l1_bias[:16]}")
        print(f"  L1 weights: min={l1_weights.min()}, max={l1_weights.max()}, mean={l1_weights.mean():.4f}")

if __name__ == '__main__':
    check()
