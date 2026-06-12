def find_hash(path):
    with open(path, 'rb') as f:
        f.seek(47645885)
        data = f.read()
        
    print(f"Data size: {len(data)}")
    
    # Target hashes to search for
    targets = [
        0x633376ca,
        0x63337155,
        0xb6c094f9,
        0x36c094cc,
        0xb6c094ff,
        0xb6c09500,
        0x36c09502,
        0x3817c116,
        0xb6c09505
    ]
    
    import struct
    # Let's search for any uint32 that matches
    for offset in range(0, len(data) - 4, 1):
        val = struct.unpack('<I', data[offset:offset+4])[0]
        if val in targets:
            print(f"Found target hash 0x{val:08x} at relative offset {offset} (absolute {47645885 + offset})")
        # Also print if it looks like a similar hash (e.g. starting with 0x6333 or 0xb6c0)
        elif (val & 0xffff0000) == 0x63330000 or (val & 0xffff0000) == 0xb6c00000 or (val & 0xfff00000) == 0x36c00000:
            print(f"Found similar hash 0x{val:08x} at relative offset {offset} (absolute {47645885 + offset})")

if __name__ == '__main__':
    find_hash('nn.nnue')
