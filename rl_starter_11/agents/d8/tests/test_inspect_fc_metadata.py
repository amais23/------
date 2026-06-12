import struct

with open('weights/nn.nnue', 'rb') as f:
    data = f.read()

# FC metadata is from 47645889 (fc_start) to 47646161
fc_start = 47645889
metadata = data[fc_start : fc_start + 300]

print("FC Section Hash (Hex):", metadata[:4].hex())
print("Metadata string/bytes:")
try:
    print(metadata[4:268].decode('utf-8'))
except Exception as e:
    print(metadata[4:268])

# Let's print some integers from the metadata
ints = struct.unpack('<' + 'I'*(len(metadata)//4), metadata[:len(metadata)-(len(metadata)%4)])
print("\nIntegers in metadata:")
print(ints[:50])
