import struct
import numpy as np

def verify(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    total_size = len(file_data)
    
    # Let's print the 32 values of L1 bias starting at total_size - 17700
    offset_fc = total_size - 17700
    l1_bias_fc = np.frombuffer(file_data[offset_fc : offset_fc + 128], dtype=np.int32)
    print("=== L1 bias from verify_fc.py (offset -17700) ===")
    print("Shape:", l1_bias_fc.shape)
    print("Values:", list(l1_bias_fc))
    print("Min/Max/Mean:", l1_bias_fc.min(), l1_bias_fc.max(), l1_bias_fc.mean())
    
    # Let's print the 16 values of L1 bias starting at 47703833 + 4 = 47703837
    offset_precise = 47703837
    l1_bias_precise = np.frombuffer(file_data[offset_precise : offset_precise + 64], dtype=np.int32)
    print("\n=== L1 bias from verify_precise_split.py (offset 47703837) ===")
    print("Shape:", l1_bias_precise.shape)
    print("Values:", list(l1_bias_precise))
    print("Min/Max/Mean:", l1_bias_precise.min(), l1_bias_precise.max(), l1_bias_precise.mean())

if __name__ == '__main__':
    verify('nn.nnue')
