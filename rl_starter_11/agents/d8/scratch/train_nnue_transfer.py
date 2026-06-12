import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import chess
import numpy as np
from tqdm import tqdm
import sys

sys.path.insert(0, "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8")
from scratch.train_nnue import ChessDataset, collate_fn, NNUE, preprocess_data

processed_dir = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/research/data/processed"
preprocessed_file = os.path.join(processed_dir, "preprocessed_dataset.pt")
model_save_path = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/weights/trained_model.pt"
orig_nnue_path = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/weights/nn.nnue.orig"

def load_from_binary(model, binary_path):
    with open(binary_path, "rb") as f:
        data = f.read()
    
    def load_tensor(offset, shape, scale, dtype):
        num_elements = int(np.prod(shape))
        bytes_to_read = num_elements * np.dtype(dtype).itemsize
        buf = data[offset : offset + bytes_to_read]
        arr = np.frombuffer(buf, dtype=dtype).reshape(shape).astype(np.float32)
        return torch.from_numpy(arr / scale)
        
    model.friend_bias.data.copy_(load_tensor(193, [256], 127.0, np.int16))
    model.friend_emb.weight.data.copy_(load_tensor(705, [49216, 256], 127.0, np.int16))
    
    model.enemy_bias.data.copy_(load_tensor(25199297, [256], 127.0, np.int16))
    model.enemy_emb.weight.data.copy_(load_tensor(25199809, [43840, 256], 127.0, np.int16))
    
    main_start = 47650913
    model.l1.bias.data.copy_(load_tensor(main_start + 4, [16], 8128.0, np.int32))
    model.l1.weight.data.copy_(load_tensor(main_start + 68, [16, 1024], 64.0, np.int8))
    
    model.l2.bias.data.copy_(load_tensor(main_start + 16452, [32], 8128.0, np.int32))
    model.l2.weight.data.copy_(load_tensor(main_start + 16580, [32, 32], 64.0, np.int8))
    
    model.output.bias.data.copy_(load_tensor(main_start + 17604, [1], 9600.0, np.int32))
    model.output.weight.data.copy_(load_tensor(main_start + 17608, [1, 32], 9600.0 / 127.0, np.int8))
    
    print("Successfully loaded model weights from original binary!")

def train():
    print(f"Loading preprocessed dataset...")
    data_list = preprocess_data()  # Will re-generate if file doesn't exist
    dataset = ChessDataset(data_list)
    
    train_size = int(0.9 * len(dataset))
    val_size = len(dataset) - train_size
    train_set, val_set = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_set, batch_size=4096, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_set, batch_size=4096, shuffle=False, collate_fn=collate_fn)
    
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using training device: {device}")
    
    model = NNUE()
    load_from_binary(model, orig_nnue_path)
    model = model.to(device)
    
    # Freeze the embeddings
    model.friend_emb.weight.requires_grad = False
    model.friend_bias.requires_grad = False
    model.enemy_emb.weight.requires_grad = False
    model.enemy_bias.requires_grad = False
    
    # Only optimize L1, L2, L3 weights and biases
    trainable_params = [
        model.l1.weight, model.l1.bias,
        model.l2.weight, model.l2.bias,
        model.output.weight, model.output.bias
    ]
    
    optimizer = torch.optim.Adam(trainable_params, lr=0.001)
    criterion = nn.HuberLoss(delta=1.0)
    
    epochs = 15
    best_val_loss = float("inf")
    
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for us_flat, us_offsets, them_flat, them_offsets, scores in train_loader:
            us_flat = us_flat.to(device)
            us_offsets = us_offsets.to(device)
            them_flat = them_flat.to(device)
            them_offsets = them_offsets.to(device)
            scores = scores.to(device)
            
            optimizer.zero_grad()
            pred = model(us_flat, us_offsets, them_flat, them_offsets)
            loss = criterion(pred, scores)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * scores.size(0)
            
        train_loss /= len(train_set)
        
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for us_flat, us_offsets, them_flat, them_offsets, scores in val_loader:
                us_flat = us_flat.to(device)
                us_offsets = us_offsets.to(device)
                them_flat = them_flat.to(device)
                them_offsets = them_offsets.to(device)
                scores = scores.to(device)
                
                pred = model(us_flat, us_offsets, them_flat, them_offsets)
                loss = criterion(pred, scores)
                val_loss += loss.item() * scores.size(0)
                
        val_loss /= len(val_set)
        print(f"Epoch {epoch:02d}/{epochs:02d} | Train MSE: {train_loss:.5f} | Val MSE: {val_loss:.5f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
            torch.save(model.state_dict(), model_save_path)
            
    print(f"Training completed. Best Val MSE: {best_val_loss:.5f}")

if __name__ == '__main__':
    train()
