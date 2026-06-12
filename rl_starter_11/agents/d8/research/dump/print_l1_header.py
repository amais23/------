import struct

def print_l1_header(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    total_size = len(file_data)
    # L1 bias starts at -18828.
    # Let's print the 20 uint32s before that.
    print("uint32s before -18828:")
    for offset in range(-18900, -18824, 4):
        val = struct.unpack('<I', file_data[total_size + offset : total_size + offset + 4])[0]
        print(f"Offset {offset}: hex=0x{val:08x} ({val})")

if __name__ == '__main__':
    print_l1_header('nn.nnue')
