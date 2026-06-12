import struct
import numpy as np

def verify(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    fc_start = 47645889
    
    # 1. Verify 4 isolated buckets (Buckets 0-3 L2/L3)
    print("=== ISOLATED BUCKETS 0-3 (L2/L3) ===")
    isolated_start = fc_start + 272  # 4 bytes hash + 268 bytes metadata
    for i in range(4):
        start = isolated_start + i * 1188
        print(f"\nIsolated Bucket {i} (offset {start}):")
        l2_bias = np.frombuffer(file_data[start : start+128], dtype=np.int32)
        l2_weights = np.frombuffer(file_data[start+128 : start+1152], dtype=np.int8).reshape(32, 32)
        l3_bias = struct.unpack('<i', file_data[start+1152 : start+1156])[0]
        l3_weights = np.frombuffer(file_data[start+1156 : start+1188], dtype=np.int8)
        
        print(f"  L2 bias: min={l2_bias.min()}, max={l2_bias.max()}, mean={l2_bias.mean():.2f}")
        print(f"  L2 bias values: {l2_bias[:8]}")
        print(f"  L3 bias: {l3_bias}")
        print(f"  L3 weights: {l3_weights[:8]}...")

    # 2. Verify 4 main stacks (Buckets 4-7 / Stack 0-3 of L1/L2/L3)
    print("\n=== MAIN STACKS 0-3 (BUCKETS 4-7 L1/L2/L3) ===")
    large_start = isolated_start + 4752
    for i in range(4):
        start = large_start + i * 17640
        print(f"\nMain Stack {i} (offset {start}):")
        fc_hash = struct.unpack('<I', file_data[start : start+4])[0]
        l1_bias = np.frombuffer(file_data[start+4 : start+68], dtype=np.int32)
        l1_weights = np.frombuffer(file_data[start+68 : start+16452], dtype=np.int8).reshape(16, 1024)
        l2_bias = np.frombuffer(file_data[start+16452 : start+16580], dtype=np.int32)
        l2_weights = np.frombuffer(file_data[start+16580 : start+17604], dtype=np.int8).reshape(32, 32)
        l3_bias = struct.unpack('<i', file_data[start+17604 : start+17608])[0]
        l3_weights = np.frombuffer(file_data[start+17608 : start+17640], dtype=np.int8)
        
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
