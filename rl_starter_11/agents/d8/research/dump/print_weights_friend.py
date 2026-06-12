import struct
import numpy as np

def analyze(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    # Friend FT weights start at 705
    start = 705
    num_planes = 769
    weights = np.frombuffer(file_data[start : start + num_planes * 64 * 256 * 2], dtype=np.int16)
    weights = weights.reshape(num_planes, 64, 256)
    
    # Calculate the mean absolute weight for each plane
    plane_stats = np.abs(weights).mean(axis=(1, 2))
    
    print("Friend FT Plane Statistics (Last 20 planes):")
    for p in range(num_planes - 20, num_planes):
        print(f"  Plane {p}: mean_abs_weight={plane_stats[p]:.4f}")

if __name__ == '__main__':
    analyze('nn.nnue')
