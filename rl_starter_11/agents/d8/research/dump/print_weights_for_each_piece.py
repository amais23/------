import struct
import numpy as np

def analyze(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    # Enemy FT weights start at 25199809
    start = 25199809
    num_planes = 685
    weights = np.frombuffer(file_data[start : start + num_planes * 64 * 256 * 2], dtype=np.int16)
    weights = weights.reshape(num_planes, 64, 256)
    
    # Calculate the mean absolute weight for each plane
    plane_stats = np.abs(weights).mean(axis=(1, 2))
    
    print("Plane Statistics (First 20 planes):")
    for p in range(20):
        print(f"  Plane {p}: mean_abs_weight={plane_stats[p]:.4f}")
        
    print("\nPlane Statistics (Last 20 planes):")
    for p in range(num_planes - 20, num_planes):
        print(f"  Plane {p}: mean_abs_weight={plane_stats[p]:.4f}")
        
    # Let's count how many planes have high/low/zero weights, or if we can see groups of 64
    # Let's check the distribution of plane_stats
    print("\nSorted unique plane stats (first 10):", sorted(plane_stats)[:10])
    
    # Let's print which planes have very low/zero weights
    very_low = np.where(plane_stats < 0.05)[0]
    print(f"\nNumber of planes with mean_abs_weight < 0.05: {len(very_low)}")
    if len(very_low) > 0:
        print("Planes with very low weights:", list(very_low))

if __name__ == '__main__':
    analyze('nn.nnue')
