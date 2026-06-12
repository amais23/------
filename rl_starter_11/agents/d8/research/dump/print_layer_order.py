import struct
import numpy as np

def check_all_layers(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    total_size = len(file_data)
    
    # Let's print the L1, L2, L3 biases for all 4 subnetworks
    # We found:
    # L1 bias 3: -18828
    # L2 bias 3: -1188
    # L1 bias 2: -36468
    # L2 bias 2: -18828 - 17640 + 1128? No:
    # Let's check the offsets of L1 and L2 biases we found in find_all_l2_biases:
    # Offset 47685005 (from end -36468) -> L2 bias 2? Or L1 bias 2?
    # Offset 47702645 (from end -18828) -> L1 bias 3?
    # Offset 47720285 (from end -1188) -> L2 bias 3?
    # Let's print out the 32 values at each of these offsets:
    offsets = [
        total_size - 18828 - 17640*2, # L1 bias 1?
        total_size - 1188 - 17640*2,  # L2 bias 1?
        total_size - 36468,            # L1 bias 2?
        total_size - 18828,            # L1 bias 3?
        total_size - 1188              # L2 bias 3?
    ]
    
    for i, offset in enumerate(offsets):
        bias = np.frombuffer(file_data[offset:offset+128], dtype=np.int32)
        print(f"Offset {offset} (from end {offset - total_size}):")
        print(bias[:10])

if __name__ == '__main__':
    check_all_layers('nn.nnue')
