import struct

def dump(path):
    with open(path, 'rb') as f:
        f.read(4) # version
        f.read(4) # hash
        desc_len = struct.unpack('<I', f.read(4))[0]
        f.read(desc_len)
        
        # FT 1: bias (512 bytes) + weights (25,198,592 bytes)
        f.read(512 + 25198592)
        print("After FT 1 offset:", f.tell())
        
        # FT 2: bias (512 bytes) + weights (22,446,080 bytes)
        f.read(512 + 22446080)
        print("After FT 2 offset:", f.tell())
        
        # Now we are at the beginning of the fully connected layers (or their headers).
        # Let's print out the next 1000 uint32 values to find where the layers are.
        pos = f.tell()
        f.seek(0, 2)
        total_size = f.tell()
        f.seek(pos)
        
        print(f"Total size: {total_size}, remaining: {total_size - pos} bytes")
        
        # Read the remaining bytes as uint32
        data = f.read(total_size - pos)
        uints = struct.unpack(f'<{len(data)//4}I', data[:(len(data)//4)*4])
        for i, val in enumerate(uints[:100]):
            print(f"Index {i} (offset {pos + i*4}): 0x{val:08x} ({val})")

if __name__ == '__main__':
    dump('nn.nnue')
