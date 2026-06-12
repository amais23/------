import struct
import numpy as np

def verify_fc(path):
    with open(path, 'rb') as f:
        file_data = f.read()
    
    total_size = len(file_data)
    
    # Read backwards
    # L3
    l3_weights = np.frombuffer(file_data[-32:], dtype=np.int8)
    l3_bias = struct.unpack('<i', file_data[-36:-32])[0]
    
    # L2
    l2_weights = np.frombuffer(file_data[-1060:-36], dtype=np.int8).reshape(32, 32)
    l2_bias = np.frombuffer(file_data[-1188:-1060], dtype=np.int32)
    
    # L1
    l1_weights = np.frombuffer(file_data[-17572:-1188], dtype=np.int8).reshape(32, 512)
    l1_bias = np.frombuffer(file_data[-17700:-17572], dtype=np.int32)
    
    print("L3 bias:", l3_bias)
    print("L3 weights:", l3_weights)
    
    print("L2 bias min/max/mean:", l2_bias.min(), l2_bias.max(), l2_bias.mean())
    print("L2 weights min/max/mean:", l2_weights.min(), l2_weights.max(), l2_weights.mean())
    
    print("L1 bias min/max/mean:", l1_bias.min(), l1_bias.max(), l1_bias.mean())
    print("L1 weights min/max/mean:", l1_weights.min(), l1_weights.max(), l1_weights.mean())

if __name__ == '__main__':
    verify_fc('nn.nnue')
