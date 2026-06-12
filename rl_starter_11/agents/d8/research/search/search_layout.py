import struct
import numpy as np

def search(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    # Let's parse header
    version = struct.unpack('<I', file_data[0:4])[0]
    network_hash = struct.unpack('<I', file_data[4:8])[0]
    desc_len = struct.unpack('<I', file_data[8:12])[0]
    desc = file_data[12:12+desc_len].decode('utf-8', errors='ignore')
    
    header_offset = 12 + desc_len
    
    # FT 1 (Friend):
    # Bias: 256 * int16 = 512 bytes
    # Weights: 49216 * 256 * int16 = 25,198,592 bytes
    ft1_size = 512 + 25198592
    
    # Offset after FT 1
    ft2_offset = header_offset + ft1_size
    print(f"FT2 starts at offset: {ft2_offset}")
    
    # We want to find the number of features E for FT 2 (Enemy)
    # FT 2 has:
    # Bias: 256 * int16 = 512 bytes
    # Weights: E * 256 * int16 = E * 512 bytes
    # So total FT 2 size = 512 + E * 512
    # After FT 2, we have the fully connected layers:
    # L1: bias (32 * int32 = 128 bytes) + weights (32 * 512 * int8 = 16384 bytes)
    # L2: bias (32 * int32 = 128 bytes) + weights (32 * 32 * int8 = 1024 bytes)
    # L3: bias (1 * int32 = 4 bytes) + weights (1 * 32 * int8 = 32 bytes)
    # Total FC size = 128 + 16384 + 128 + 1024 + 4 + 32 = 17700 bytes.
    # Wait, does each layer have a header?
    # Let's search over E and possible header sizes!
    # Let's assume there are layer headers. How many bytes do headers take?
    # Let's search E from 0 to 49216
    # Let's search the remaining bytes.
    remaining_bytes = len(file_data) - ft2_offset
    
    # Let's search for E such that the last 36 bytes (L3 bias + weights) are reasonable.
    # L3 bias: 1 int32, L3 weights: 32 int8.
    # Let's check for E:
    # We can try all E from 0 to 49216.
    # If there are no headers, then the offset of L1 is ft2_offset + 512 + E * 512.
    # Let's print out if any E gives a very reasonable L1/L2/L3 bias.
    # Specifically, L3 bias should be between -100000 and 100000, and L3 weights should be between -128 and 127 (they are int8, so they are always in that range, but their std/mean should be reasonable, e.g. std > 0.1).
    
    for E in range(40000, 49216):
        # Let's try different header offsets. Let's assume total header overhead of H bytes.
        # Since we saw remaining bytes is 75588 after E=43840 (which had remaining: 75588, and 17700 of FC weights. The difference was 57888 bytes).
        # Wait, if H = 57888? Why would H be 57888?
        # What if E is actually larger, so H is smaller?
        # Let's calculate: if H is small (e.g. 0 to 1000 bytes).
        # Then E must be around:
        # E * 512 + 512 + 17700 + H = remaining_bytes
        # E * 512 + H = remaining_bytes - 18212
        # E * 512 + H = 22522180 - 18212 = 22503968
        # Let's divide: 22503968 / 512 = 43953.06
        # So E must be around 43953!
        # If E = 43953, then H = 22503968 - 43953 * 512 = 32 bytes!
        # Wait!
        # `43953 * 512 = 22,503,936`!
        # `22,503,968 - 22,503,936 = 32` bytes!
        # Oh!!! 32 bytes of header overhead!
        # Let's check: 32 bytes is exactly 4 headers of 8 bytes each!
        # Or 8 headers of 4 bytes each!
        # That is incredibly clean!
        # Let's check if E = 43953 is the number of features!
        # Wait, is E = 43953?
        # Let's calculate: 43953 / 64 = 686.7... not an integer!
        # Wait, what if E = 43904?
        # `43904 / 64 = 686`!
        # Let's check: if E = 43904, then:
        # `43904 * 512 = 22,478,848` bytes.
        # `H = 22,503,968 - 22,478,848 = 25,120` bytes? That is large.
        # What if E = 43904 and there are other layers?
        # Let's search for E around 43900 to 44000 and H from 0 to 26000!
        pass

    # Let's write a loop that checks if the L3 bias (the last 36 bytes of the file, minus 32 bytes of weights = the 4 bytes before that) is reasonable!
    # L3 bias is at offset total_size - 36.
    # L3 weights is at offset total_size - 32.
    # Let's check:
    l3_bias_val = struct.unpack('<i', file_data[-36:-32])[0]
    l3_weights_val = np.frombuffer(file_data[-32:], dtype=np.int8)
    print(f"L3 bias at end of file: {l3_bias_val}")
    print(f"L3 weights at end of file: {l3_weights_val}")
    
    # Wow! L3 bias is -17104379? Or is it different?
    # In verify_loading.py, we read from the end and got:
    # L3 bias: -17104379
    # L3 weights: [-20, max=10, mean=-1.125]
    # Wait, these values are extremely reasonable!
    # This means the end of the file is indeed L3!
    # So the layers are aligned from the end!
    # Let's work backwards from the end of the file!
    # If we work backwards:
    # L3 weights: last 32 bytes (file_data[-32:])
    # L3 bias: 4 bytes before L3 weights (file_data[-36:-32])
    # L2 weights: 1024 bytes before L3 bias (file_data[-1060:-36])
    # L2 bias: 128 bytes before L2 weights (file_data[-1188:-1060])
    # L1 weights: 16384 bytes before L2 bias (file_data[-17572:-1188])
    # L1 bias: 128 bytes before L1 weights (file_data[-17700:-17572])
    # Let's print the values of L1, L2, L3 biases when we read backwards!

if __name__ == '__main__':
    search('nn.nnue')
