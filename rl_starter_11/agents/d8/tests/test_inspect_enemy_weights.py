import numpy as np

def inspect(path):
    with open(path, 'rb') as f:
        file_data = f.read()
        
    start = 25199809
    num_features = 43840
    weights = np.frombuffer(file_data[start : start + num_features * 256 * 2], dtype=np.int16)
    
    print(f"Enemy weights total elements: {len(weights)}")
    print(f"Min: {weights.min()}, Max: {weights.max()}, Mean: {weights.mean():.4f}, Std: {weights.std():.4f}")
    
    # Count occurrences of extreme values
    extreme_neg = np.sum(weights == -32768)
    extreme_pos = np.sum(weights == 32767)
    extreme_pos_32766 = np.sum(weights == 32766)
    print(f"Occurrences of -32768: {extreme_neg}")
    print(f"Occurrences of 32767:  {extreme_pos}")
    print(f"Occurrences of 32766:  {extreme_pos_32766}")
    
    # Let's see the first 100 weights
    print("\nFirst 20 weights:")
    print(list(weights[:20]))

if __name__ == '__main__':
    inspect('weights/nn.nnue')
