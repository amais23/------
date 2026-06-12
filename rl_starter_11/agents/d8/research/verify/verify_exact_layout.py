import struct
import numpy as np

def verify(path):
    with open(path, 'rb') as f:
        f.seek(47645885)
        data = f.read()
        
    print(f"Total remaining data size: {len(data)}")
    
    # 4 buckets of FC layers
    # Each stack is exactly 17640 bytes.
    # Stack k starts at 5028 + k * 17640.
    for k in range(4):
        start = 5028 + k * 17640
        print(f"\n================ BUCKET {k} (start: {start}) ================")
        
        # Read fc_hash (4 bytes)
        fc_hash = struct.unpack('<I', data[start:start+4])[0]
        print(f"fc_hash: 0x{fc_hash:08x}")
        
        # L1 bias: 32 int32s (128 bytes)
        l1_bias = np.frombuffer(data[start+4 : start+4+128], dtype=np.int32)
        print(f"L1 bias: min={l1_bias.min()}, max={l1_bias.max()}, mean={l1_bias.mean():.2f}")
        print(f"  values: {l1_bias[:8]}")
        
        # L1 weights: 32 * 510 int8s (16320 bytes)
        l1_weights = np.frombuffer(data[start+132 : start+132+16320], dtype=np.int8).reshape(32, 510)
        print(f"L1 weights: min={l1_weights.min()}, max={l1_weights.max()}, mean={l1_weights.mean():.4f}, std={l1_weights.std():.4f}")
        print(f"  first few weights of row 0: {l1_weights[0, :8]}")
        
        # L2 bias: 32 int32s (128 bytes)
        l2_bias = np.frombuffer(data[start+16452 : start+16452+128], dtype=np.int32)
        print(f"L2 bias: min={l2_bias.min()}, max={l2_bias.max()}, mean={l2_bias.mean():.2f}")
        print(f"  values: {l2_bias[:8]}")
        
        # L2 weights: 32 * 32 int8s (1024 bytes)
        l2_weights = np.frombuffer(data[start+16580 : start+16580+1024], dtype=np.int8).reshape(32, 32)
        print(f"L2 weights: min={l2_weights.min()}, max={l2_weights.max()}, mean={l2_weights.mean():.4f}, std={l2_weights.std():.4f}")
        print(f"  first few weights of row 0: {l2_weights[0, :8]}")
        
        # L3 bias: 1 int32 (4 bytes)
        l3_bias = struct.unpack('<i', data[start+17604 : start+17608])[0]
        print(f"L3 bias: {l3_bias}")
        
        # L3 weights: 32 int8s (32 bytes)
        l3_weights = np.frombuffer(data[start+17608 : start+17640], dtype=np.int8)
        print(f"L3 weights: min={l3_weights.min()}, max={l3_weights.max()}, mean={l3_weights.mean():.4f}")
        print(f"  values: {l3_weights[:16]}")

if __name__ == '__main__':
    verify('nn.nnue')
