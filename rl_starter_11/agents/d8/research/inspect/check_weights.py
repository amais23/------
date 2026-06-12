import struct
import sys

def check_nnue(path):
    try:
        with open(path, 'rb') as f:
            file_data = f.read()
            print(f"File size: {len(file_data)} bytes")
            
            # Read version/hash
            version = struct.unpack('<I', file_data[0:4])[0]
            network_hash = struct.unpack('<I', file_data[4:8])[0]
            desc_len = struct.unpack('<I', file_data[8:12])[0]
            desc = file_data[12:12+desc_len].decode('utf-8', errors='ignore')
            
            print(f"Version: 0x{version:08x}")
            print(f"Hash: 0x{network_hash:08x}")
            print(f"Description length: {desc_len}")
            print(f"Description: {desc}")
            
            offset = 12 + desc_len
            print(f"Header offset: {offset}")
            
            # Feature Transformer
            # Biases: 256 * int16 (512 bytes)
            # Weights: 49216 * 256 * int16 (25,200,128 bytes)
            # Let's see how much data is remaining
            remaining = len(file_data) - offset
            print(f"Remaining bytes: {remaining}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_nnue('nn.nnue')
