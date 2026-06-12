def get_stack_size(in_features, out_features_l1, out_features_l2, is_output_bucketed, num_ls_buckets):
    # Padding in_features to 32
    padded_in = ((in_features + 31) // 32) * 32
    # L1
    l1_bias = out_features_l1 * 4
    l1_weights = out_features_l1 * padded_in
    
    # L2
    padded_l2_in = ((out_features_l1 + 31) // 32) * 32
    l2_bias = out_features_l2 * 4
    l2_weights = out_features_l2 * padded_l2_in
    
    # L3 (output)
    padded_l3_in = ((out_features_l2 + 31) // 32) * 32
    l3_bias = 4
    l3_weights = 1 * padded_l3_in
    
    # Size of one stack
    stack_size = 4 + l1_bias + l1_weights + l2_bias + l2_weights + l3_bias + l3_weights
    
    # Total size for all buckets
    total_size = stack_size * num_ls_buckets
    
    return stack_size, total_size

# Brute force
print("Searching for matches...")
for L2 in [8, 16, 32, 64]:
    for L3 in [8, 16, 32, 64]:
        for buckets in range(1, 17):
            for in_f in [510, 512]:
                stack_size, total_size = get_stack_size(in_f, L2, L3, True, buckets)
                if total_size == 75588 or stack_size == 17640:
                    print(f"L2={L2}, L3={L3}, buckets={buckets}, in_f={in_f} => stack={stack_size}, total={total_size}")
