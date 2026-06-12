def print_hex(path):
    with open(path, 'rb') as f:
        f.seek(-1200, 2)
        data = f.read(40)
        print("Bytes [-1200:-1160] hex:")
        print(data.hex())

if __name__ == '__main__':
    print_hex('nn.nnue')
