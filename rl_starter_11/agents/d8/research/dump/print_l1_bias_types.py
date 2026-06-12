import struct
import numpy as np

def verify(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    # Main Stack 3 starts at 47703833
    start = 47703833
    bias_data = file_data[start+4 : start+68]
    
    print("Bias data length:", len(bias_data))
    print("As hex:", bias_data.hex())
    
    # Try as 16 int32s
    ints32 = struct.unpack('<16i', bias_data)
    print("\nAs 16 int32:")
    print(ints32)
    
    # Try as 32 int16s
    ints16 = struct.unpack('<32h', bias_data)
    print("\nAs 32 int16:")
    print(ints16)
    
    # Try as 64 int8s
    ints8 = struct.unpack('<64b', bias_data)
    print("\nAs 64 int8:")
    print(ints8[:16], "...")

if __name__ == '__main__':
    verify('nn.nnue')
