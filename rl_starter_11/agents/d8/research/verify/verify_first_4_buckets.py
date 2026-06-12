import struct
import numpy as np

def verify(path):
    with open(path, 'rb') as f:
        f.seek(47645889)
        data = f.read(5024)
        
    print(f"Data size: {len(data)}")
    
    # Let's try 4 buckets of size 1256.
    # Where does the L2 bias start in each bucket?
    # If the layout of each bucket is:
    # - fc_hash (4 bytes)
    # - L1 bias (64 bytes)
    # - L2 bias (128 bytes)
    # - L2 weights (1024 bytes)
    # - L3 bias (4 bytes)
    # - L3 weights (32 bytes)
    # Total = 4 + 64 + 128 + 1024 + 4 + 32 = 1256 bytes!
    # Let's check if this is the case!
    for i in range(4):
        start = i * 1256
        print(f"\n--- Bucket {i} (start: {start}) ---")
        fc_hash = struct.unpack('<I', data[start:start+4])[0]
        l1_bias = np.frombuffer(data[start+4 : start+68], dtype=np.int32)
        l2_bias = np.frombuffer(data[start+68 : start+196], dtype=np.int32)
        l3_bias = struct.unpack('<i', data[start+1220 : start+1224])[0]
        l3_weights = np.frombuffer(data[start+1224 : start+1256], dtype=np.int8)
        
        print(f"fc_hash: 0x{fc_hash:08x}")
        print(f"L1 bias: min={l1_bias.min()}, max={l1_bias.max()}, mean={l1_bias.mean():.2f}")
        print(f"  values: {l1_bias}")
        print(f"L2 bias: min={l2_bias.min()}, max={l2_bias.max()}, mean={l2_bias.mean():.2f}")
        print(f"  values: {l2_bias[:8]}")
        print(f"L3 bias: {l3_bias}")
        print(f"L3 weights: {l3_weights[:8]}...")

if __name__ == '__main__':
    verify('nn.nnue')
