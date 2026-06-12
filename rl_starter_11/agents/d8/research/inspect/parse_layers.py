import struct

def parse_layers(path):
    with open(path, 'rb') as f:
        # 1. Header
        version = struct.unpack('<I', f.read(4))[0]
        network_hash = struct.unpack('<I', f.read(4))[0]
        desc_len = struct.unpack('<I', f.read(4))[0]
        desc = f.read(desc_len).decode('utf-8', errors='ignore')
        print(f"Version: 0x{version:08x}")
        print(f"Hash: 0x{network_hash:08x}")
        print(f"Description: {desc}")
        
        # In Stockfish/nnue-pytorch, the weights file has a header, then the FeatureTransformer weights.
        # Let's see what is stored in the next bytes.
        # FT bias
        ft_bias_data = f.read(256 * 2)
        print(f"FT bias read: {len(ft_bias_data)} bytes")
        
        # FT weights
        ft_weights_data = f.read(49216 * 256 * 2)
        print(f"FT weights read: {len(ft_weights_data)} bytes")
        
        # Let's see what is after the FeatureTransformer
        pos = f.tell()
        print(f"Offset after FT weights: {pos}")
        
        # Let's read the next 100 bytes and print as ints/chars/etc.
        next_data = f.read(100)
        print(f"Next 100 bytes (hex): {next_data.hex()[:50]}...")
        
        # Let's print total remaining size
        f.seek(0, 2)
        print(f"Total file size: {f.tell()} bytes")
        print(f"Remaining bytes after FT weights: {f.tell() - pos} bytes")

if __name__ == '__main__':
    parse_layers('nn.nnue')
