import struct
import numpy as np

def find_zeros(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    # Enemy FT weights start at 25199809
    start = 25199809
    num_features = 43840
    weights = np.frombuffer(file_data[start : start + num_features * 256 * 2], dtype=np.int16).reshape(num_features, 256)
    
    print("Enemy weights shape:", weights.shape)
    
    # Find rows that are all zero
    row_norms = np.abs(weights).sum(axis=1)
    zero_rows = np.where(row_norms == 0)[0]
    print(f"Number of all-zero rows: {len(zero_rows)}")
    
    if len(zero_rows) > 0:
        print("First 20 zero rows:", list(zero_rows[:20]))
        # Let's see if they are grouped by 64 (meaning whole planes are zero)
        planes_zero = []
        for p in range(685):
            plane_rows = np.arange(p*64, (p+1)*64)
            is_zero = all(r in zero_rows for r in plane_rows)
            if is_zero:
                planes_zero.append(p)
        print(f"Number of all-zero planes: {len(planes_zero)}")
        print("All-zero planes:", planes_zero)
        
        # Let's also check if there are individual zero rows within planes
        non_zero_planes_with_zeros = []
        for p in range(685):
            plane_rows = np.arange(p*64, (p+1)*64)
            zeros_in_plane = [r for r in plane_rows if r in zero_rows]
            if 0 < len(zeros_in_plane) < 64:
                non_zero_planes_with_zeros.append((p, zeros_in_plane))
        print(f"Number of planes with partial zeros: {len(non_zero_planes_with_zeros)}")
        if len(non_zero_planes_with_zeros) > 0:
            print("First few partial zero planes:")
            for p, zs in non_zero_planes_with_zeros[:5]:
                print(f"  Plane {p}: {len(zs)} zeros (e.g. {[z % 64 for z in zs[:10]]})")

if __name__ == '__main__':
    find_zeros('nn.nnue')
