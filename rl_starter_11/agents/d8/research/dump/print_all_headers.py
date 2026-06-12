import struct

def search_headers(path):
    with open(path, 'rb') as f:
        data = f.read()
    
    # Let's search for 0x5f2348b8 and 0x3e1d07ec (or any other known layer hashes)
    # in the file.
    # We want to print the offsets where they occur.
    target_hashes = [0x5f2348b8, 0x3e1d07ec]
    for h in target_hashes:
        offset = 0
        while True:
            offset = data.find(struct.pack('<I', h), offset)
            if offset == -1:
                break
            print(f"Hash 0x{h:08x} found at offset {offset} (from end {offset - len(data)})")
            offset += 4

if __name__ == '__main__':
    search_headers('nn.nnue')
