def print_hex(path):
    with open(path, 'rb') as f:
        f.seek(-2350, 2)
        data = f.read(200)
        print("Bytes [-2350:-2150] hex:")
        print(data.hex())

if __name__ == '__main__':
    print_hex('nn.nnue')
