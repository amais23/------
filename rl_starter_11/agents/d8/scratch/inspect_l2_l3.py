import numpy as np
import struct

def inspect_l2_l3(path='weights/nn.nnue'):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    fc_start = 47645889
    # Start position bucket uses stack 3
    start_stack = fc_start + 4768 + 3 * 17704
    
    print("start_stack:", start_stack)
    
    # 1. Inspect L2 biases at start_stack + 16452
    l2_bias_bytes = file_data[start_stack + 16452 : start_stack + 16452 + 128]
    print("\n--- L2 biases at start_stack + 16452 (first 128 bytes) ---")
    print("As Int32 (32 elements):")
    print(np.frombuffer(l2_bias_bytes, dtype=np.int32)[:32])
    print("As Int16 (64 elements):")
    print(np.frombuffer(l2_bias_bytes, dtype=np.int16)[:64])
    
    # 2. Inspect L2 weights.
    # If L2 biases are 32 int16_t (64 bytes), then L2 weights start at +16516.
    # If L2 biases are 32 int32_t (128 bytes), then L2 weights start at +16580.
    # Let's inspect L2 weights at both offsets.
    print("\n--- L2 weights at +16516 (first 32 bytes) ---")
    print(np.frombuffer(file_data[start_stack + 16516 : start_stack + 16516 + 32], dtype=np.int8))
    
    print("\n--- L2 weights at +16580 (first 32 bytes) ---")
    print(np.frombuffer(file_data[start_stack + 16580 : start_stack + 16580 + 32], dtype=np.int8))

    # Let's also print the remaining bytes of the stack (from +17540 to +17704)
    remaining_bytes = file_data[start_stack + 17540 : start_stack + 17704]
    print(f"\n--- Remaining bytes ({len(remaining_bytes)} bytes from +17540 to +17704) ---")
    # Let's print non-zero bytes or decode them
    for offset in range(0, len(remaining_bytes), 16):
        chunk = remaining_bytes[offset : offset + 16]
        print(f"Offset +{17540 + offset}: {chunk.hex()}")
        # Let's print as int16
        print(f"  Int16s: {np.frombuffer(chunk, dtype=np.int16)}")
        # Let's print as int32
        print(f"  Int32s: {np.frombuffer(chunk[:16 - (len(chunk)%4)], dtype=np.int32)}")
        # Let's print as int8
        print(f"  Int8s:  {np.frombuffer(chunk, dtype=np.int8)}")

if __name__ == '__main__':
    inspect_l2_l3()
