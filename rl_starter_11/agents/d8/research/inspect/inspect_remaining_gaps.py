import struct
import numpy as np

def inspect(path):
    with open(path, 'rb') as f:
        f.seek(47645885)
        data = f.read(3840)
        
    print(f"Data length: {len(data)}")
    
    # 1. Check if it's float32
    floats = np.frombuffer(data[:128], dtype=np.float32)
    print("Interpret first 128 bytes as float32:")
    print(floats[:8])
    
    # 2. Interpret as int32
    int32s = np.frombuffer(data[:128], dtype=np.int32)
    print("Interpret first 128 bytes as int32:")
    print(int32s[:8])
    
    # 3. Interpret as int16
    int16s = np.frombuffer(data[:128], dtype=np.int16)
    print("Interpret first 128 bytes as int16:")
    print(int16s[:16])
    
    # 4. Interpret as int8
    int8s = np.frombuffer(data[:128], dtype=np.int8)
    print("Interpret first 128 bytes as int8:")
    print(int8s[:32])
    
    # Let's count how many non-zero bytes are there in the 3840 bytes
    nz = np.count_nonzero(int8s)
    print(f"Non-zero elements in first 128 bytes (int8): {nz} / 128")
    
    # Let's check if there are repeating patterns of 1024 or other sizes
    print("\n--- Statistics of blocks of size 1024 (as int8) ---")
    for i in range(3):
        block = np.frombuffer(data[i*1024 : (i+1)*1024], dtype=np.int8)
        print(f"Block {i}: min={block.min()}, max={block.max()}, mean={block.mean():.4f}, std={block.std():.4f}")

if __name__ == '__main__':
    inspect('nn.nnue')
