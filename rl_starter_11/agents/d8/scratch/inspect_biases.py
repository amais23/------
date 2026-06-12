import numpy as np

def inspect(path='weights/nn.nnue'):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    fc_start = 47645889
    # Start position bucket uses stack 3
    start_stack = fc_start + 4768 + 3 * 17704
    
    print("--- Stack 3 header (first 16 bytes) ---")
    header = file_data[start_stack : start_stack + 16]
    print("Hex:", header.hex())
    print("Int32s:", np.frombuffer(header, dtype=np.int32))
    print("Int16s:", np.frombuffer(header, dtype=np.int16))
    
    # Let's inspect L1 biases at start_stack + 4
    # Let's read 128 bytes from start_stack + 4
    l1_bias_bytes = file_data[start_stack + 4 : start_stack + 132]
    print("\n--- L1 biases (first 128 bytes from start_stack + 4) ---")
    print("As Int32 (32 elements):")
    print(np.frombuffer(l1_bias_bytes, dtype=np.int32))
    print("As Int16 (64 elements):")
    print(np.frombuffer(l1_bias_bytes, dtype=np.int16))
    print("As Float32 (32 elements):")
    print(np.frombuffer(l1_bias_bytes, dtype=np.float32))

    # Let's search the file stack data for clean small biases.
    # Where does L1 weights start? If L1 bias is 32 int16_t (64 bytes), L1 weights starts at +68.
    # If L1 bias is 32 int32_t (128 bytes), L1 weights starts at +132.
    # Let's print the first 64 weights of L1 weights from +68 and +132.
    print("\n--- L1 weights at +68 (first 32 bytes) ---")
    print(np.frombuffer(file_data[start_stack + 68 : start_stack + 100], dtype=np.int8))
    print("\n--- L1 weights at +132 (first 32 bytes) ---")
    print(np.frombuffer(file_data[start_stack + 132 : start_stack + 164], dtype=np.int8))

if __name__ == '__main__':
    inspect()
