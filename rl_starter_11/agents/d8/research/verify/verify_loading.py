import struct
import numpy as np

def verify(path):
    with open(path, 'rb') as f:
        # Header
        version = struct.unpack('<I', f.read(4))[0]
        network_hash = struct.unpack('<I', f.read(4))[0]
        desc_len = struct.unpack('<I', f.read(4))[0]
        desc = f.read(desc_len).decode('utf-8', errors='ignore')
        print(f"Header: version=0x{version:08x}, hash=0x{network_hash:08x}, desc={desc}")
        
        # In Stockfish/nnue-pytorch, the FeatureTransformer has:
        # bias: [256] int16
        # weights: [49216 * 256] int16
        # Let's read these!
        ft_bias = np.frombuffer(f.read(256 * 2), dtype=np.int16)
        ft_weights = np.frombuffer(f.read(49216 * 256 * 2), dtype=np.int16)
        
        print(f"FeatureTransformer Us (Friend):")
        print(f"  bias: shape={ft_bias.shape}, min={ft_bias.min()}, max={ft_bias.max()}, mean={ft_bias.mean():.4f}")
        print(f"  weights: shape={ft_weights.shape}, min={ft_weights.min()}, max={ft_weights.max()}, mean={ft_weights.mean():.4f}")
        
        # Now let's see what is next.
        # Wait, the remaining bytes is 22,522,180 bytes.
        # Let's see: could the next layer be the FeatureTransformer for Them (Enemy)?
        # If so, it might have:
        # bias: [256] int16
        # weights: [43840 * 256] int16
        # Let's check!
        ft_enemy_bias = np.frombuffer(f.read(256 * 2), dtype=np.int16)
        ft_enemy_weights = np.frombuffer(f.read(43840 * 256 * 2), dtype=np.int16)
        
        print(f"FeatureTransformer Them (Enemy):")
        print(f"  bias: shape={ft_enemy_bias.shape}, min={ft_enemy_bias.min()}, max={ft_enemy_bias.max()}, mean={ft_enemy_bias.mean():.4f}")
        print(f"  weights: shape={ft_enemy_weights.shape}, min={ft_enemy_weights.min()}, max={ft_enemy_weights.max()}, mean={ft_enemy_weights.mean():.4f}")
        
        # Now let's read the FC layers.
        # In Stockfish:
        # L1 (AffineTransform[32<-512]):
        #   bias: [32] int32
        #   weights: [32 * 512] int8
        l1_bias = np.frombuffer(f.read(32 * 4), dtype=np.int32)
        l1_weights = np.frombuffer(f.read(32 * 512), dtype=np.int8)
        
        print(f"L1 (AffineTransform[32<-512]):")
        print(f"  bias: shape={l1_bias.shape}, min={l1_bias.min()}, max={l1_bias.max()}, mean={l1_bias.mean():.4f}")
        print(f"  weights: shape={l1_weights.shape}, min={l1_weights.min()}, max={l1_weights.max()}, mean={l1_weights.mean():.4f}")
        
        # L2 (AffineTransform[32<-32]):
        #   bias: [32] int32
        #   weights: [32 * 32] int8
        l2_bias = np.frombuffer(f.read(32 * 4), dtype=np.int32)
        l2_weights = np.frombuffer(f.read(32 * 32), dtype=np.int8)
        
        print(f"L2 (AffineTransform[32<-32]):")
        print(f"  bias: shape={l2_bias.shape}, min={l2_bias.min()}, max={l2_bias.max()}, mean={l2_bias.mean():.4f}")
        print(f"  weights: shape={l2_weights.shape}, min={l2_weights.min()}, max={l2_weights.max()}, mean={l2_weights.mean():.4f}")
        
        # L3 (AffineTransform[1<-32]):
        #   bias: [1] int32
        #   weights: [1 * 32] int8
        l3_bias = np.frombuffer(f.read(1 * 4), dtype=np.int32)
        l3_weights = np.frombuffer(f.read(1 * 32), dtype=np.int8)
        
        print(f"L3 (AffineTransform[1<-32]):")
        print(f"  bias: shape={l3_bias.shape}, min={l3_bias.min()}, max={l3_bias.max()}, mean={l3_bias.mean():.4f}")
        print(f"  weights: shape={l3_weights.shape}, min={l3_weights.min()}, max={l3_weights.max()}, mean={l3_weights.mean():.4f}")
        
        # Let's check if there are any remaining bytes.
        pos = f.tell()
        f.seek(0, 2)
        total_size = f.tell()
        print(f"Total size: {total_size}, read up to: {pos}, remaining: {total_size - pos} bytes")

if __name__ == '__main__':
    verify('nn.nnue')
