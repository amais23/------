import os
import torch
import numpy as np

model_save_path = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/weights/trained_model.pt"
orig_nnue_path = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/weights/nn.nnue.orig"
dest_nnue_path = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/weights/nn.nnue"

# Load model definition to avoid import issues
import sys
sys.path.insert(0, "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8")
from scratch.train_nnue import NNUE

def export():
    print("Loading PyTorch model state...")
    model = NNUE()
    model.load_state_dict(torch.load(model_save_path, map_location="cpu"))
    model.eval()
    
    print(f"Reading original weights file from {orig_nnue_path}...")
    with open(orig_nnue_path, "rb") as f:
        data = bytearray(f.read())
        
    def write_tensor(offset, tensor, scale, dtype, clamp_val=None):
        scaled = tensor.detach().cpu().numpy() * scale
        if clamp_val is not None:
            scaled = np.clip(scaled, -clamp_val, clamp_val)
        rounded = np.round(scaled).astype(dtype)
        bytes_to_write = rounded.tobytes()
        data[offset : offset + len(bytes_to_write)] = bytes_to_write
        print(f"Wrote to offset {offset}: shape {tensor.shape}, scale {scale}, written {len(bytes_to_write)} bytes")

    # 1. FT Friend Us weights & biases
    # Offset 193: friend_bias (256 int16)
    write_tensor(193, model.friend_bias, 127.0, np.int16)
    # Offset 705: friend_weights (49216x256 int16)
    # The EmbeddingBag weights are shaped (49216, 256), flat tobytes is shape (49216, 256)
    write_tensor(705, model.friend_emb.weight, 127.0, np.int16)
    
    # 2. FT Enemy Them weights & biases
    # Offset 25199297: enemy_bias (256 int16)
    write_tensor(25199297, model.enemy_bias, 127.0, np.int16)
    # Offset 25199809: enemy_weights (43840x256 int16)
    write_tensor(25199809, model.enemy_emb.weight, 127.0, np.int16)
    
    # 3. Write FC layers (L1, L2, L3) to all 4 Stacks and 4 Buckets
    fc_start = 47645889
    
    # Isolated Buckets 0-3 (L2 + L3, stride 1188 bytes)
    for i in range(4):
        bucket_offset = fc_start + 272 + i * 1188
        
        # L2 biases: 32 int32 (128 bytes)
        write_tensor(bucket_offset, model.l2.bias, 8128.0, np.int32)
        # L2 weights: 32x32 int8 (1024 bytes)
        # Note: Linear weights in PyTorch are shaped (out_features, in_features) -> (32, 32)
        write_tensor(bucket_offset + 128, model.l2.weight, 64.0, np.int8, clamp_val=127)
        # L3 bias: 1 int32 (4 bytes)
        write_tensor(bucket_offset + 1152, model.output.bias, 9600.0, np.int32)
        # L3 weights: 32 int8 (32 bytes)
        # PyTorch output shape is (1, 32)
        write_tensor(bucket_offset + 1156, model.output.weight, 9600.0 / 127.0, np.int8, clamp_val=127)
        
    # Main Stacks 0-3 (L1 + L2 + L3, stride 17640 bytes)
    main_start = fc_start + 272 + 4 * 1188 # 47650913
    for i in range(4):
        stack_offset = main_start + i * 17640
        
        # L1 biases: 16 int32 (64 bytes) starting at stack_offset + 4
        write_tensor(stack_offset + 4, model.l1.bias, 8128.0, np.int32)
        # L1 weights: 16x1024 int8 (16384 bytes) starting at stack_offset + 68
        write_tensor(stack_offset + 68, model.l1.weight, 64.0, np.int8, clamp_val=127)
        
        # L2 biases: 32 int32 (128 bytes) starting at stack_offset + 16452
        write_tensor(stack_offset + 16452, model.l2.bias, 8128.0, np.int32)
        # L2 weights: 32x32 int8 (1024 bytes) starting at stack_offset + 16580
        write_tensor(stack_offset + 16580, model.l2.weight, 64.0, np.int8, clamp_val=127)
        
        # L3 bias: 1 int32 (4 bytes) starting at stack_offset + 17604
        write_tensor(stack_offset + 17604, model.output.bias, 9600.0, np.int32)
        # L3 weights: 32 int8 (32 bytes) starting at stack_offset + 17608
        write_tensor(stack_offset + 17608, model.output.weight, 9600.0 / 127.0, np.int8, clamp_val=127)
        
    print(f"Writing quantized NNUE to {dest_nnue_path}...")
    with open(dest_nnue_path, "wb") as f:
        f.write(data)
    print("Export completed successfully!")

if __name__ == '__main__':
    export()
