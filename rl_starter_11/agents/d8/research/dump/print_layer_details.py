import struct

def dump_details(path):
    with open(path, 'rb') as f:
        f.seek(25199293)
        # Read next 256 bytes as 16-bit integers
        data = f.read(512)
        ints = struct.unpack(f'<{len(data)//2}h', data)
        print("First 20 int16s:", ints[:20])
        print("Min/Max/Mean of these int16s:", min(ints), max(ints), sum(ints)/len(ints))
        
        # Read next 1024 bytes and search for any patterns
        # Let's see how many total bytes are left
        f.seek(0, 2)
        total_size = f.tell()
        print(f"Total size: {total_size}")
        remaining = total_size - 25199293
        print(f"Remaining bytes: {remaining}")
        
        # Is the remaining size close to 49216 * 256 * 2? No, that is 25198592.
        # Wait, is 22522180 bytes close to 43840 * 256 * 2?
        # Let's calculate: 43840 * 256 * 2 = 22,446,080 bytes.
        # Yes! 43840 * 256 * 2 = 22,446,080 bytes!
        # And 22,522,180 - 22,446,080 = 76,100 bytes!
        # Wait, what is 43840?
        # 43840 / 64 = 685!
        # Wait, what is 685?
        # Let's calculate: 43840 features is for another FeatureTransformer!
        # Wait, why 43840?
        # In Stockfish, HalfKA(Friend) features are:
        # Friend: 10 piece types? Or 11 piece types?
        # Let's check!

if __name__ == '__main__':
    dump_details('nn.nnue')
