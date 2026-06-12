def print_hex(path):
    with open(path, 'rb') as f:
        f.seek(-17750, 2)
        data = f.read(100)
        print("Bytes [-17750:-17650] hex:")
        print(data.hex())

if __name__ == '__main__':
    print_hex('nn.nnue')
