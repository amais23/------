import struct
import numpy as np

def verify_all(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    total_size = len(file_data)
    print(f"Total file size: {total_size} bytes")
    
    # 1. Header
    version = struct.unpack('<I', file_data[0:4])[0]
    network_hash = struct.unpack('<I', file_data[4:8])[0]
    desc_len = struct.unpack('<I', file_data[8:12])[0]
    desc = file_data[12:12+desc_len].decode('utf-8', errors='ignore')
    print(f"Header: version=0x{version:08x}, hash=0x{network_hash:08x}, desc={desc}")
    
    offset = 12 + desc_len
    
    # 2. Friend FT (Us)
    print(f"\n--- Friend FT (Us) starting at offset {offset} ---")
    friend_bias = np.frombuffer(file_data[offset : offset + 256 * 2], dtype=np.int16)
    print(f"Friend Bias: min={friend_bias.min()}, max={friend_bias.max()}, mean={friend_bias.mean():.4f}")
    offset += 256 * 2
    
    friend_weights = np.frombuffer(file_data[offset : offset + 49216 * 256 * 2], dtype=np.int16)
    print(f"Friend Weights: min={friend_weights.min()}, max={friend_weights.max()}, mean={friend_weights.mean():.4f}")
    offset += 49216 * 256 * 2
    print(f"Friend FT ends at offset {offset}")
    
    # 3. Enemy FT (Them)
    print(f"\n--- Enemy FT (Them) starting at offset {offset} ---")
    enemy_bias = np.frombuffer(file_data[offset : offset + 256 * 2], dtype=np.int16)
    print(f"Enemy Bias: min={enemy_bias.min()}, max={enemy_bias.max()}, mean={enemy_bias.mean():.4f}")
    offset += 256 * 2
    
    enemy_weights = np.frombuffer(file_data[offset : offset + 43840 * 256 * 2], dtype=np.int16)
    print(f"Enemy Weights: min={enemy_weights.min()}, max={enemy_weights.max()}, mean={enemy_weights.mean():.4f}")
    offset += 43840 * 256 * 2
    print(f"Enemy FT ends at offset {offset}")
    
    # Remaining bytes
    remaining = total_size - offset
    print(f"\nRemaining bytes for FC layers: {remaining}")
    
    # Let's inspect the layout of the FC layers.
    # The remaining data size is 75,584 bytes.
    # Let's print the first 32 bytes as hex and as uint32s.
    print("FC Section start hex:")
    print(file_data[offset : offset + 64].hex())
    
    print("\nFC Section start as uint32:")
    for i in range(16):
        val = struct.unpack('<I', file_data[offset + i*4 : offset + i*4 + 4])[0]
        print(f"Offset {offset + i*4}: hex=0x{val:08x}, int32={struct.unpack('<i', file_data[offset + i*4 : offset + i*4 + 4])[0]}")

    # Let's look at the very end of the file (last 17,700 bytes)
    print("\n--- Last 17,700 bytes (Bucket 3 / Stack 3) ---")
    l3_weights = np.frombuffer(file_data[-32:], dtype=np.int8)
    l3_bias = struct.unpack('<i', file_data[-36:-32])[0]
    l2_weights = np.frombuffer(file_data[-1060:-36], dtype=np.int8).reshape(32, 32)
    l2_bias = np.frombuffer(file_data[-1188:-1060], dtype=np.int32)
    l1_weights = np.frombuffer(file_data[-17572:-1188], dtype=np.int8).reshape(32, 512)
    l1_bias = np.frombuffer(file_data[-17700:-17572], dtype=np.int32)
    
    print(f"L3 bias: {l3_bias}")
    print(f"L3 weights: {l3_weights}")
    print(f"L2 bias: min={l2_bias.min()}, max={l2_bias.max()}, mean={l2_bias.mean():.4f}")
    print(f"L2 weights: min={l2_weights.min()}, max={l2_weights.max()}, mean={l2_weights.mean():.4f}")
    print(f"L1 bias: min={l1_bias.min()}, max={l1_bias.max()}, mean={l1_bias.mean():.4f}")
    print(f"L1 weights: min={l1_weights.min()}, max={l1_weights.max()}, mean={l1_weights.mean():.4f}")

if __name__ == '__main__':
    verify_all('nn.nnue')
