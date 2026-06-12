import struct

def parse_nnue(path):
    with open(path, 'rb') as f:
        # 1. Header
        version = struct.unpack('<I', f.read(4))[0]
        network_hash = struct.unpack('<I', f.read(4))[0]
        desc_len = struct.unpack('<I', f.read(4))[0]
        desc = f.read(desc_len).decode('utf-8', errors='ignore')
        print(f"Version: 0x{version:08x}")
        print(f"Hash: 0x{network_hash:08x}")
        print(f"Description: {desc}")
        
        # In Stockfish, the layers are stored in the order they are defined.
        # Let's print out the size of the rest of the file.
        pos = f.tell()
        f.seek(0, 2)
        end = f.tell()
        print(f"Remaining bytes from {pos}: {end - pos}")
        
        f.seek(pos)
        # Let's read some parts and see if we can identify sizes.
        # In Stockfish NNUE, the FeatureTransformer has:
        # Bias: 256 * int16 = 512 bytes
        # Weights: 49216 * 256 * int16 = 25,200,128 bytes
        # Let's check if the remaining bytes is larger.
        # Wait, Stockfish 12/13 NNUE has FeatureTransformer with:
        # Bias: 512 * int16 = 1024 bytes? No, the description says 256x2.
        # Wait, is the weight matrix larger?
        # Let's look at the Stockfish 12 format.
        # In SF12:
        # Features = HalfKA(Friend)
        # Weight size is 40960 * 256 * 2? Or 49216 * 256 * 2?
        # Wait! Let's check what is after the description.
        # Stockfish NNUE files have a header for each layer!
        # Let's read the next 4 bytes.
        layer_header = struct.unpack('<I', f.read(4))[0]
        print(f"Layer header 1: 0x{layer_header:08x}")
        # Let's see if there's a size or type.

if __name__ == '__main__':
    parse_nnue('nn.nnue')
