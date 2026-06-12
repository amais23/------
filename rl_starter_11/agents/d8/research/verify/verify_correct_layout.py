import struct
import numpy as np

def verify(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    fc_start = 47645889
    
    # 1. 4 small stacks (Buckets 0-3 L2/L3)
    print("=== SMALL STACKS (BUCKETS 0-3 L2/L3) ===")
    for i in range(4):
        start = fc_start + i * 1192
        print(f"\nSmall Stack {i} (offset {start}):")
        fc_hash = struct.unpack('<I', file_data[start : start+4])[0]
        l2_bias = np.frombuffer(file_data[start+4 : start+132], dtype=np.int32)
        l2_weights = np.frombuffer(file_data[start+132 : start+1156], dtype=np.int8).reshape(32, 32)
        l3_bias = struct.unpack('<i', file_data[start+1156 : start+1160])[0]
        l3_weights = np.frombuffer(file_data[start+1160 : start+1192], dtype=np.int8)
        
        print(f"  fc_hash: 0x{fc_hash:08x}")
        print(f"  L2 bias: min={l2_bias.min()}, max={l2_bias.max()}, mean={l2_bias.mean():.2f}")
        print(f"  L2 bias values: {l2_bias[:8]}")
        print(f"  L3 bias: {l3_bias}")
        print(f"  L3 weights: {l3_weights[:8]}...")

    # 2. 4 large stacks (Buckets 4-7 L1/L2/L3)
    print("\n=== LARGE STACKS (BUCKETS 4-7 L1/L2/L3) ===")
    large_start = fc_start + 4768
    for i in range(4):
        start = large_start + i * 17704
        print(f"\nLarge Stack {i} (offset {start}):")
        fc_hash = struct.unpack('<I', file_data[start : start+4])[0]
        l1_bias = np.frombuffer(file_data[start+4 : start+132], dtype=np.int32)
        l1_weights = np.frombuffer(file_data[start+132 : start+16516], dtype=np.int8).reshape(32, 512)
        l2_bias = np.frombuffer(file_data[start+16516 : start+16644], dtype=np.int32)
        l2_weights = np.frombuffer(file_data[start+16644 : start+17668], dtype=np.int8).reshape(32, 32)
        l3_bias = struct.unpack('<i', file_data[start+17668 : start+17672])[0]
        l3_weights = np.frombuffer(file_data[start+17672 : start+17704], dtype=np.int8)
        
        print(f"  fc_hash: 0x{fc_hash:08x}")
        print(f"  L1 bias: min={l1_bias.min()}, max={l1_bias.max()}, mean={l1_bias.mean():.2f}")
        print(f"  L1 bias values: {l1_bias[:8]}")
        print(f"  L1 weights: min={l1_weights.min()}, max={l1_weights.max()}, mean={l1_weights.mean():.4f}")
        print(f"  L2 bias: min={l2_bias.min()}, max={l2_bias.max()}, mean={l2_bias.mean():.2f}")
        print(f"  L2 bias values: {l2_bias[:8]}")
        print(f"  L3 bias: {l3_bias}")
        print(f"  L3 weights: {l3_weights[:8]}...")

if __name__ == '__main__':
    verify('nn.nnue')
