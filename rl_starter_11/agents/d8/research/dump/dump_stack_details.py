import struct
import numpy as np

def dump(path):
    with open(path, 'rb') as f:
        f.seek(47645885)
        data = f.read()
        
    print(f"Total remaining data size: {len(data)}")
    
    # Let's inspect Stack 0 starting around 5028
    # We found fc_hash at 5028.
    fc_hash_offset = 5028
    fc_hash = struct.unpack('<I', data[fc_hash_offset:fc_hash_offset+4])[0]
    print(f"\n--- Stack 0 at offset {fc_hash_offset} ---")
    print(f"fc_hash: 0x{fc_hash:08x}")
    
    # 1. Let's look at the 128 bytes before fc_hash (offsets 4900 to 5028)
    # Could this be L1 bias of Stack 0?
    before_bias = np.frombuffer(data[fc_hash_offset-128:fc_hash_offset], dtype=np.int32)
    print("128 bytes before fc_hash (as int32):")
    print(before_bias)
    
    # 2. Let's look at the 128 bytes after fc_hash (offsets 5032 to 5160)
    # Could this be L1 bias of Stack 0?
    after_bias = np.frombuffer(data[fc_hash_offset+4:fc_hash_offset+4+128], dtype=np.int32)
    print("128 bytes after fc_hash (as int32):")
    print(after_bias)
    
    # 3. Let's look at the next 128 bytes (offsets 5160 to 5288)
    after_bias_2 = np.frombuffer(data[fc_hash_offset+4+128:fc_hash_offset+4+256], dtype=np.int32)
    print("Next 128 bytes (as int32):")
    print(after_bias_2)
    
    # 4. Let's look at the first 32 bytes of weights after fc_hash + 4
    # If the bias is at fc_hash_offset - 128, then weights start at fc_hash_offset + 4!
    # Let's print that:
    weights_after_hash = np.frombuffer(data[fc_hash_offset+4:fc_hash_offset+4+32], dtype=np.int8)
    print("First 32 bytes after fc_hash as int8:")
    print(weights_after_hash)

if __name__ == '__main__':
    dump('nn.nnue')
