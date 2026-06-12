import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import chess
import numpy as np
from tqdm import tqdm

processed_dir = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/research/data/processed"
input_file = os.path.join(processed_dir, "dataset.txt")
preprocessed_file = os.path.join(processed_dir, "preprocessed_dataset.pt")
model_save_path = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/weights/trained_model.pt"
nnue_save_path = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/weights/nn.nnue"
orig_nnue_path = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/weights/nn.nnue.orig"

# Back up the original nn.nnue if not already done
if os.path.exists(nnue_save_path) and not os.path.exists(orig_nnue_path):
    import shutil
    shutil.copy(nnue_save_path, orig_nnue_path)
    print(f"Backed up original weights to {orig_nnue_path}")

# ═══════════════════════════════════════════
# Feature Mapping (Must Match C++ exactly)
# ═══════════════════════════════════════════
def orient(is_white_pov: bool, sq: int):
    return sq ^ 56 if not is_white_pov else sq

def get_piece_features(board: chess.Board, is_white_pov: bool):
    king_sq = orient(is_white_pov, board.king(is_white_pov))
    us_indices = []
    for sq, p in board.piece_map().items():
        p_idx = (p.piece_type - 1) * 2 + (p.color != is_white_pov)
        oriented_sq = orient(is_white_pov, sq)
        idx = 1 + oriented_sq + p_idx * 64 + king_sq * 769
        us_indices.append(idx)
    return us_indices

def get_enemy_features(board: chess.Board, is_white_pov: bool):
    them_pov = not is_white_pov
    king_sq = orient(them_pov, board.king(them_pov))
    enemy_indices = []
    for sq, p in board.piece_map().items():
        if p.piece_type == chess.KING and p.color == is_white_pov:
            continue
        p_idx = (p.piece_type - 1) * 2 + (p.color != them_pov)
        oriented_sq = orient(them_pov, sq)
        if p.piece_type == chess.PAWN:
            pawn_plane = 0 if p.color == them_pov else 1
            plane_offset = 1 + pawn_plane * 48 + (oriented_sq - 8)
        else:
            pt_idx = (p.piece_type - 2) * 2 + (p.color != them_pov)
            plane_offset = 1 + 96 + pt_idx * 64 + oriented_sq
        idx = plane_offset + king_sq * 685
        enemy_indices.append(idx)
    return enemy_indices

# ═══════════════════════════════════════════
# PyTorch Dataset
# ═══════════════════════════════════════════
class ChessDataset(Dataset):
    def __init__(self, data_list):
        self.data = data_list
        
    def __len__(self):
        return len(self.data)
        
    def __getitem__(self, idx):
        us, them, score = self.data[idx]
        return torch.tensor(us, dtype=torch.long), torch.tensor(them, dtype=torch.long), torch.tensor(score, dtype=torch.float)

def collate_fn(batch):
    us_list, them_list, score_list = zip(*batch)
    
    us_flat = torch.cat(us_list)
    them_flat = torch.cat(them_list)
    
    us_offsets = torch.tensor([0] + [len(x) for x in us_list[:-1]], dtype=torch.long).cumsum(0)
    them_offsets = torch.tensor([0] + [len(x) for x in them_list[:-1]], dtype=torch.long).cumsum(0)
    
    scores = torch.stack(score_list)
    
    return us_flat, us_offsets, them_flat, them_offsets, scores

# ═══════════════════════════════════════════
# NNUE Architecture A Model
# ═══════════════════════════════════════════
class NNUE(nn.Module):
    def __init__(self):
        super().__init__()
        # Feature Transformer (FT) Embeddings & Biases
        self.friend_emb = nn.EmbeddingBag(49216, 256, mode="sum")
        self.friend_bias = nn.Parameter(torch.zeros(256))
        
        self.enemy_emb = nn.EmbeddingBag(43840, 256, mode="sum")
        self.enemy_bias = nn.Parameter(torch.zeros(256))
        
        # Fully Connected Layers (Architecture A)
        self.l1 = nn.Linear(1024, 16)
        self.l2 = nn.Linear(32, 32)
        self.output = nn.Linear(32, 1)
        
        # Initialize weights
        nn.init.kaiming_uniform_(self.friend_emb.weight, a=0.2)
        nn.init.constant_(self.friend_bias, 0.0)
        nn.init.kaiming_uniform_(self.enemy_emb.weight, a=0.2)
        nn.init.constant_(self.enemy_bias, 0.0)
        nn.init.kaiming_uniform_(self.l1.weight, a=0.2)
        nn.init.kaiming_uniform_(self.l2.weight, a=0.2)
        nn.init.kaiming_uniform_(self.output.weight, a=0.2)
        
    def forward(self, us_indices, us_offsets, them_indices, them_offsets):
        # Feature Transformer evaluation
        acc_us = self.friend_emb(us_indices, us_offsets) + self.friend_bias
        acc_them = self.enemy_emb(them_indices, them_offsets) + self.enemy_bias
        
        # Dual Clipped ReLU (Activation scale 1.0 in float model)
        in_l1 = torch.cat([
            torch.clamp(acc_us, 0.0, 1.0),
            torch.clamp(-acc_us, 0.0, 1.0),
            torch.clamp(acc_them, 0.0, 1.0),
            torch.clamp(-acc_them, 0.0, 1.0)
        ], dim=1)
        
        # L1 layer propagation
        out_l1 = self.l1(in_l1)
        
        # Dual Clipped ReLU on L1 output
        in_l2 = torch.cat([
            torch.clamp(out_l1, 0.0, 1.0),
            torch.clamp(-out_l1, 0.0, 1.0)
        ], dim=1)
        
        # L2 layer propagation
        out_l2 = self.l2(in_l2)
        
        # Standard Clipped ReLU on L2 output
        in_l3 = torch.clamp(out_l2, 0.0, 1.0)
        
        # L3 output
        score = self.output(in_l3)
        return score

# ═══════════════════════════════════════════
# Preprocessing & Training
# ═══════════════════════════════════════════
def preprocess_data():
    if os.path.exists(preprocessed_file):
        print(f"Loading preprocessed dataset from {preprocessed_file}...")
        return torch.load(preprocessed_file)
        
    print(f"Reading dataset from {input_file}...")
    preprocessed_data = []
    
    with open(input_file, "r") as f:
        lines = f.readlines()
        
    print("Converting FENs into active feature indices...")
    for line in tqdm(lines):
        line = line.strip()
        if not line:
            continue
        fen, score_str = line.split(",")
        score = float(score_str)
        
        board = chess.Board(fen)
        is_white_pov = (board.turn == chess.WHITE)
        
        # Normalize score: convert centipawns to STM (side-to-move) perspective.
        # Stockfish scores are always white-relative (+ means white winning).
        # NNUE uses STM convention: + means the current player is winning.
        # So when it's black's turn, we NEGATE the score.
        score_val = score / 100.0
        if not is_white_pov:
            score_val = -score_val
        
        us = get_piece_features(board, is_white_pov)
        them = get_enemy_features(board, is_white_pov)
        
        preprocessed_data.append((us, them, [score_val]))
        
    print(f"Saving preprocessed dataset to {preprocessed_file}...")
    torch.save(preprocessed_data, preprocessed_file)
    return preprocessed_data

def train():
    data_list = preprocess_data()
    dataset = ChessDataset(data_list)
    
    train_size = int(0.9 * len(dataset))
    val_size = len(dataset) - train_size
    train_set, val_set = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_set, batch_size=4096, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_set, batch_size=4096, shuffle=False, collate_fn=collate_fn)
    
    # Use MPS (Metal GPU) on M4 Macbook, fallback to CPU
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using training device: {device}")
    
    model = NNUE().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-3)
    criterion = nn.HuberLoss(delta=1.0)
    
    epochs = 20
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
