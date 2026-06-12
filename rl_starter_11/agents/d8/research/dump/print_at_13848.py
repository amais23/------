import struct

def print_val(path):
    with open(path, 'rb') as f:
        f.seek(47645885 + 13848)
        val = struct.unpack('<I', f.read(4))[0]
        print(f"Uint32 at relative offset 13848: 0x{val:08x} ({val})")

if __name__ == '__main__':
    print_val('nn.nnue')
