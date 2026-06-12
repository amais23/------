def compute_hash(L1, L2, L3, num_ls_buckets):
    # InputSlice hash
    prev_hash = 0xEC42E90D
    prev_hash ^= (L1 * 2)

    # Fully connected layers
    # l1: out_features = L2, in_features = 2*L1
    # l2: out_features = L3, in_features = L2
    # output: out_features = 1, in_features = L3
    
    # Layer 1
    layer_hash = 0xCC03DAE4
    layer_hash += L2 // num_ls_buckets
    layer_hash ^= prev_hash >> 1
    layer_hash ^= (prev_hash << 31) & 0xFFFFFFFF
    if L2 // num_ls_buckets != 1:
        layer_hash = (layer_hash + 0x538D24C7) & 0xFFFFFFFF
    prev_hash = layer_hash
    
    # Layer 2
    layer_hash = 0xCC03DAE4
    layer_hash += L3 // num_ls_buckets
    layer_hash ^= prev_hash >> 1
    layer_hash ^= (prev_hash << 31) & 0xFFFFFFFF
    if L3 // num_ls_buckets != 1:
        layer_hash = (layer_hash + 0x538D24C7) & 0xFFFFFFFF
    prev_hash = layer_hash
    
    # Output Layer
    layer_hash = 0xCC03DAE4
    layer_hash += 1 // 1 # wait, output.out_features is always 1, and output is not bucketed?
    # In serialize_ref.py: layer.out_features // model.num_ls_buckets
    # Wait, for output layer, is out_features 1?
    # Yes, output = nn.Linear(M.L3, 1), so out_features is 1.
    # So 1 // num_ls_buckets?
    # Let's check serialize_ref.py:
    # layer_hash += layer.out_features // model.num_ls_buckets
    # So for output layer, it adds 1 // num_ls_buckets (which is 0 if num_ls_buckets > 1!)
    layer_hash += 1 // num_ls_buckets
    layer_hash ^= prev_hash >> 1
    layer_hash ^= (prev_hash << 31) & 0xFFFFFFFF
    if 1 // num_ls_buckets != 1:
        layer_hash = (layer_hash + 0x538D24C7) & 0xFFFFFFFF
    
    return layer_hash

for b in [1, 2, 3, 4, 8, 16, 32, 64]:
    print(f"Buckets {b}: hash = 0x{compute_hash(256, 32, 32, b):08x}")
