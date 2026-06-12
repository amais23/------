import struct

def parse(path):
    with open(path, 'rb') as f:
        # Header
        f.read(4) # version
        f.read(4) # hash
        desc_len = struct.unpack('<I', f.read(4))[0]
        f.read(desc_len)
        
        # FT bias
        f.read(256 * 2)
        # FT weights
        f.read(49216 * 256 * 2)
        
        # Now we are at offset 25199293.
        # Let's print out what we see at this position.
        # Stockfish NNUE format stores layers sequentially.
        # Let's see if there is another layer description or header.
        # Often layers have a header like:
        # [4 bytes] size/type
        # Let's read 10 values of uint32
        for i in range(10):
            val = struct.unpack('<I', f.read(4))[0]
            print(f"uint32 {i}: 0x{val:08x} ({val})")

if __name__ == '__main__':
    parse('nn.nnue')
