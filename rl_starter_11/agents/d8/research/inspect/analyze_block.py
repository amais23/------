import struct
import numpy as np

def analyze(path):
    with open(path, 'rb') as f:
        f.seek(47645885 + 3840)
        data = f.read(17640)
        
    print(f"Read block of size: {len(data)}")
    
    # Let's print out the first 256 bytes as int32
    print("\nFirst 128 bytes interpreted as int32:")
    int32s = np.frombuffer(data[:128], dtype=np.int32)
    print(int32s)
    
    # We know a bias was found at the beginning of this block (which is at 3840).
    # Since 3840 was found to be a reasonable bias, the first 128 bytes are indeed the bias.
    # What is after the bias? The weights should start at offset 128.
    # Let's check the size of the weights.
    # If the weights are L1 weights, they should have size 16384 (from offset 128 to 16512).
    # Let's analyze the next 16384 bytes as int8.
    weights = np.frombuffer(data[128:128+16384], dtype=np.int8)
    print("\nL1 weights candidate (size 16384):")
    print(f"  min={weights.min()}, max={weights.max()}, mean={weights.mean():.4f}, std={weights.std():.4f}")
    print(f"  first 32 values: {weights[:32]}")
    
    # What is after offset 16512?
    # The remaining size of the block is 17640 - 16512 = 1128 bytes.
    # Let's analyze the remaining 1128 bytes!
    tail = data[16512:]
    print(f"\nRemaining tail size: {len(tail)} bytes")
    
    # Let's check if there is an L2 bias (128 bytes) and L2 weights (1024 bytes) in the tail.
    # Let's look for biases in the tail.
    # L2 bias should be 32 int32s (128 bytes).
    # Let's check if the first 128 bytes of the tail are reasonable as int32.
    l2_bias = np.frombuffer(tail[:128], dtype=np.int32)
    print("\nTail first 128 bytes as int32 (L2 bias candidate?):")
    print(f"  min={l2_bias.min()}, max={l2_bias.max()}, mean={l2_bias.mean():.2f}, std={l2_bias.std():.2f}")
    print(f"  values: {l2_bias[:8]}")
    
    # Let's check if the next 1024 bytes are reasonable as int8 (L2 weights candidate?).
    l2_weights = np.frombuffer(tail[128:128+1024], dtype=np.int8)
    print("\nTail next 1024 bytes as int8 (L2 weights candidate?):")
    print(f"  min={l2_weights.min()}, max={l2_weights.max()}, mean={l2_weights.mean():.4f}, std={l2_weights.std():.4f}")
    print(f"  first 32 values: {l2_weights[:32]}")
    
    # Wait, 128 + 1024 = 1152 bytes. But tail has only 1128 bytes!
    # Let's see: how many bytes are actually left in the tail after 128?
    # 1128 - 128 = 1000 bytes!
    # Wait! 1000 bytes!
    # Let's print the size and check if we read them.
    print(f"Actual bytes available for L2 weights: {len(tail[128:])}")
    
if __name__ == '__main__':
    analyze('nn.nnue')
