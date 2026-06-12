def dump_offset(path):
    with open(path, 'rb') as f:
        f.seek(47633274 - 50)
        data = f.read(200)
        print("Data around 47633274:")
        print(data.hex())
        # Let's decode as ascii
        print("Decoded as ASCII (replacing non-ascii):")
        print(data.decode('ascii', errors='replace'))

if __name__ == '__main__':
    dump_offset('nn.nnue')
