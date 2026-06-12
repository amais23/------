import struct
import numpy as np

def find_boundaries(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    total_size = len(file_data)
    
    # Let's inspect the data from the end backwards.
    # L3 weights: last 32 bytes (file_data[-32:])
    # L3 bias: 4 bytes (file_data[-36:-32])
    # L2 weights: 1024 bytes (file_data[-1060:-36])
    # L2 bias: 128 bytes (file_data[-1188:-1060])
    # Let's verify if the L2 bias actually starts at -1188.
    # Let's print the L2 biases:
    l2_bias = np.frombuffer(file_data[-1188:-1060], dtype=np.int32)
    print("L2 biases:", l2_bias)
    
    # Now, what is before L2 bias?
    # According to our calculation, L1 weights is 16384 bytes, which would be from -17572 to -1188.
    # But wait, does L2 have a header?
    # Let's look at the uint32s from -1250 to -1180 to see if there's any header!
    print("uint32s around -1200:")
    for offset in range(-1250, -1150, 4):
        val = struct.unpack('<I', file_data[total_size + offset : total_size + offset + 4])[0]
        val_s = struct.unpack('<i', file_data[total_size + offset : total_size + offset + 4])[0]
        print(f"Offset {offset}: hex=0x{val:08x}, int32={val_s}")

if __name__ == '__main__':
    find_boundaries('nn.nnue')
