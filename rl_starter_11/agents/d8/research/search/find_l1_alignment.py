import struct
import numpy as np

def find_l1(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    total_size = len(file_data)
    
    # Let's search for the L1 bias start offset.
    # L1 bias should be 32 int32s (128 bytes).
    # Let's search in the range of offsets from -20000 to -17000.
    # We want to print if any offset has all 32 values as small integers.
    for offset in range(-20000, -17000, 4):
        bias = np.frombuffer(file_data[total_size + offset : total_size + offset + 128], dtype=np.int32)
        # Check if the bias values are reasonable (e.g. all between -20000 and 20000)
        if np.all(np.abs(bias) < 50000):
            print(f"Reasonable L1 bias found at offset {offset}:")
            print(bias)
            # Let's also print the first 20 weights after this bias
            weights_offset = offset + 128
            weights = np.frombuffer(file_data[total_size + weights_offset : total_size + weights_offset + 32], dtype=np.int8)
            print("Weights after bias:", weights)

if __name__ == '__main__':
    find_l1('nn.nnue')
