import struct
import numpy as np

def test_loader(path):
    with open(path, 'rb') as f:
        # 1. Read header
        version = struct.unpack('<I', f.read(4))[0]
        network_hash = struct.unpack('<I', f.read(4))[0]
        desc_len = struct.unpack('<I', f.read(4))[0]
        desc = f.read(desc_len).decode('utf-8', errors='ignore')
        
        print(f"Header: version=0x{version:08x}, hash=0x{network_hash:08x}, desc={desc}")
        print(f"Position after header: {f.tell()}")
        
        # 2. Read Feature Transformer Hash
        ft_hash = struct.unpack('<I', f.read(4))[0]
        print(f"FT hash: 0x{ft_hash:08x}, position: {f.tell()}")
        
        # 3. Read Feature Transformer (Friend)
        # bias: 256 int16 = 512 bytes
        # weights: 49216 * 256 int16 = 25198592 bytes
        # psqtweights: 49216 * 0 = 0 bytes
        ft1_bias = np.fromfile(f, dtype=np.int16, count=256)
        ft1_weights = np.fromfile(f, dtype=np.int16, count=49216 * 256)
        print(f"FT1 Friend read. Position: {f.tell()}")
        
        # Wait, does it write Feature Transformer (Enemy) next?
        # In serialize_ref.py:
        # "self.write_feature_transformer(model)" is called once.
        # But wait! The description says Features=HalfKA(Friend)[49216->256x2].
        # In variant-nnue-pytorch, a feature set with "x2" typically has two feature transformers: Us and Them!
        # Let's check: does it write both?
        # Let's check the size of the rest of the file if we assume it writes Them.
        # If it writes Them, its feature transformer has:
        # bias: 256 int16 = 512 bytes
        # weights: 43840 * 256 int16 = 22446080 bytes
        # Let's check if there is an Enemy feature transformer:
        pos_before_enemy = f.tell()
        # Let's read the Enemy feature transformer
        ft2_bias = np.fromfile(f, dtype=np.int16, count=256)
        ft2_weights = np.fromfile(f, dtype=np.int16, count=43840 * 256)
        print(f"FT2 Enemy read. Position: {f.tell()}")
        
        # Let's see the remaining bytes
        remaining_pos = f.tell()
        f.seek(0, 2)
        total_size = f.tell()
        f.seek(remaining_pos)
        print(f"Remaining bytes: {total_size - remaining_pos}")
        
        # Let's try reading the FC layer stacks!
        # In serialize_ref.py, each stack has:
        # - fc_hash (4 bytes int32)
        # - l1: bias (32 int32 = 128 bytes), weight (32 * 512 int8 = 16384 bytes)
        # - l2: bias (32 int32 = 128 bytes), weight (32 * 32 int8 = 1024 bytes)
        # - output: bias (1 int32 = 4 bytes), weight (1 * 32 int8 = 32 bytes)
        # Total per stack = 4 + 128 + 16384 + 128 + 1024 + 4 + 32 = 17704 bytes.
        # Let's try to read stacks one by one!
        stack_idx = 0
        while f.tell() < total_size:
            current_pos = f.tell()
            if total_size - current_pos < 17704:
                # Less than a full stack remains. Let's see what is left!
                print(f"Less than a full stack remains: {total_size - current_pos} bytes")
                # Let's print the next few bytes as int32
                left_data = f.read()
                print("Leftover bytes hex:", left_data.hex()[:100])
                break
                
            # Read stack
            stack_hash = struct.unpack('<I', f.read(4))[0]
            l1_bias = np.fromfile(f, dtype=np.int32, count=32)
            l1_weights = np.fromfile(f, dtype=np.int8, count=32 * 512)
            l2_bias = np.fromfile(f, dtype=np.int32, count=32)
            l2_weights = np.fromfile(f, dtype=np.int8, count=32 * 32)
            l3_bias = np.fromfile(f, dtype=np.int32, count=1)
            l3_weights = np.fromfile(f, dtype=np.int8, count=32)
            
            print(f"Stack {stack_idx}: hash=0x{stack_hash:08x}")
            print(f"  L1 bias: {l1_bias[:4]}...")
            print(f"  L2 bias: {l2_bias[:4]}...")
            print(f"  L3 bias: {l3_bias[0]}")
            print(f"  L3 weights: {l3_weights[:4]}...")
            print(f"  Position after Stack {stack_idx}: {f.tell()}")
            stack_idx += 1
            
        print(f"Final position: {f.tell()}, Total size: {total_size}")

if __name__ == '__main__':
    test_loader('nn.nnue')
