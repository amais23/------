def dump_end(path):
    with open(path, 'rb') as f:
        f.seek(0, 2)
        total_size = f.tell()
        f.seek(total_size - 1024)
        data = f.read(1024)
        print("Last 1024 bytes hex:")
        print(data[-256:].hex())
        # Let's see if there are any readable strings
        import re
        matches = re.finditer(b'[a-zA-Z0-9_\\(\\)\\[\\]\\->\\:\\,]{4,}', data)
        for m in matches:
            print(f"String found near end (offset {total_size - 1024 + m.start()}): {data[m.start():m.end()].decode('ascii', errors='ignore')}")

if __name__ == '__main__':
    dump_end('nn.nnue')
