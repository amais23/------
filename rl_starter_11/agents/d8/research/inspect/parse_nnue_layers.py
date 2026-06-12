def find_strings(path):
    with open(path, 'rb') as f:
        data = f.read()
    
    # Search for ASCII strings of length >= 4
    import re
    # We want to search the entire file for ASCII strings
    matches = re.finditer(b'[a-zA-Z0-9_\\(\\)\\[\\]\\->\\:\\,]{4,}', data)
    for m in matches:
        start = m.start()
        end = m.end()
        print(f"String found at offset {start}: {data[start:end].decode('ascii', errors='ignore')}")

if __name__ == '__main__':
    find_strings('nn.nnue')
