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
        
        # Load L1 bias as 32 int32_t (128 bytes)
        l1_bias = np.frombuffer(file_data[stack_offset+4 : stack_offset+132], dtype=np.int32)
        # Load L1 weights as 32x512 int8 (16384 bytes)
        l1_weights = np.frombuffer(file_data[stack_offset+132 : stack_offset+16516], dtype=np.int8).reshape(32, 512)
        # Load L2 bias as 32 int32_t (128 bytes)
        l2_bias = np.frombuffer(file_data[stack_offset+16516 : stack_offset+16644], dtype=np.int32)
        # Load L2 weights as 32x32 int8 (1024 bytes)
        l2_weights = np.frombuffer(file_data[stack_offset+16644 : stack_offset+17668], dtype=np.int8).reshape(32, 32)
        # Load L3 bias as 1 int32_t (4 bytes)
        l3_bias = struct.unpack('<i', file_data[stack_offset+17668 : stack_offset+17672])[0]
        # Load L3 weights as 32 int8_t (32 bytes)
        l3_weights = np.frombuffer(file_data[stack_offset+17672 : stack_offset+17704], dtype=np.int8)
        
        print(f"  L1 bias: min={l1_bias.min()}, max={l1_bias.max()}, mean={l1_bias.mean():.2f}")
        print(f"  L1 bias values: {list(l1_bias)}")
        print(f"  L2 bias: min={l2_bias.min()}, max={l2_bias.max()}, mean={l2_bias.mean():.2f}")
        print(f"  L2 bias values: {list(l2_bias[:8])}")
        print(f"  L3 bias: {l3_bias}")
        print(f"  L3 weights: {list(l3_weights[:8])}...")

if __name__ == '__main__':
    check()
