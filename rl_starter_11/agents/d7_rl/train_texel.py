import os
import sqlite3
import zipfile
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from tqdm import tqdm
import chess_engine_d7_han

# ═══════════════════════════════════════════
# 1. Device Configuration
# ═══════════════════════════════════════════
device = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# ═══════════════════════════════════════════
# 2. Data Loading & Feature Extraction
# ═══════════════════════════════════════════
def parse_eval(val):
    val_str = str(val).strip()
    if val_str.startswith('#'):
        try:
            mate_str = val_str[1:]
            if mate_str.startswith('+'):
                mate_val = int(mate_str[1:])
            elif mate_str.startswith('-'):
                # Handle cases like #-3
                mate_val = int(mate_str)
            else:
                mate_val = int(mate_str)
            
            # Map mate to high centipawn values (e.g. 15000)
            if mate_val > 0:
                return 15000.0 - mate_val
            else:
                return -15000.0 - mate_val
        except ValueError:
            return 10000.0 if '+' in val_str else -10000.0
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def load_positions_from_db(db_path):
    print(f"Loading FENs from SQLite database: {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT fen, evaluation FROM positions")
    rows = cursor.fetchall()
    conn.close()
    return [(fen, parse_eval(evaluation)) for fen, evaluation in rows]

def load_positions_from_csv(zip_path):
    print(f"Loading FENs from CSV zip: {zip_path}...")
    fens_evals = []
    with zipfile.ZipFile(zip_path) as z:
        csv_filename = [name for name in z.namelist() if name.endswith('.csv')][0]
        with z.open(csv_filename) as f:
            # Read in chunks to show progress
            chunksize = 100000
            for chunk in pd.read_csv(f, chunksize=chunksize):
                for _, row in chunk.iterrows():
                    fens_evals.append((row['FEN'], parse_eval(row['Analysis'])))
    return fens_evals

# Load all available datasets
X_np = None
Y_np = None
features_cache_path = "FEN_data/extracted_features.npz"

if os.path.exists(features_cache_path):
    print(f"Found cached features at {features_cache_path}. Loading cached data...")
    cache = np.load(features_cache_path)
    X_np = cache['X']
    Y_np = cache['Y']
    num_samples = len(Y_np)
    print(f"Loaded {num_samples} samples from cache.")
else:
    data = []
    db_path = "FEN_data/chess_analysis.db"
    csv_zip_path = "FEN_data/fen_analysis.csv.zip"

    if os.path.exists(db_path):
        data.extend(load_positions_from_db(db_path))
    if os.path.exists(csv_zip_path):
        data.extend(load_positions_from_csv(csv_zip_path))

    # Remove duplicate FENs
    unique_data = {}
    for fen, eval_val in data:
        unique_data[fen] = eval_val

    fens = list(unique_data.keys())
    evals = list(unique_data.values())
    num_samples = len(fens)
    print(f"Total unique positions loaded: {num_samples}")

    # Pre-extract features using C++ engine
    print("Extracting features using C++ engine...")
    X_np = np.zeros((num_samples, 459), dtype=np.float32)
    for i, fen in enumerate(tqdm(fens)):
        X_np[i] = chess_engine_d7_han.extract_features(fen)

    Y_np = np.array(evals, dtype=np.float32)

    # Save pre-extracted features to disk for faster restarts
    np.savez_compressed(features_cache_path, X=X_np, Y=Y_np)
    print(f"Features successfully extracted and saved to {features_cache_path}")

# ═══════════════════════════════════════════
# 3. Model Definition
# ═══════════════════════════════════════════
class TexelTuningModel(nn.Module):
    def __init__(self):
        super().__init__()
        # 459 parameters to optimize
        self.weights = nn.Parameter(torch.zeros(459, dtype=torch.float32))
        
        # Initialize with standard heuristic values to speed up convergence
        with torch.no_grad():
            self.weights[0] = 100.0  # Pawn Value
            self.weights[1] = 320.0  # Knight Value
            self.weights[2] = 330.0  # Bishop Value
            self.weights[3] = 500.0  # Rook Value
            self.weights[4] = 900.0  # Queen Value
            # Other weights (PSTs and special evaluation items) remain initialized to 0

    def forward(self, x):
        # Linear dot product: Score = X * W
        return torch.matmul(x, self.weights)

# ═══════════════════════════════════════════
# 4. Training Loop
# ═══════════════════════════════════════════
X_tensor = torch.tensor(X_np, dtype=torch.float32)
Y_tensor = torch.tensor(Y_np, dtype=torch.float32)

dataset = TensorDataset(X_tensor, Y_tensor)
# 80/20 Train/Val Split
train_size = int(0.8 * num_samples)
val_size = num_samples - train_size
train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])

train_loader = DataLoader(train_dataset, batch_size=4096, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=4096, shuffle=False)

model = TexelTuningModel().to(device)
optimizer = optim.Adam(model.parameters(), lr=0.1)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=3, factor=0.5)

# Sigmoid scaling factor for Texel's Tuning
# Standard Stockfish sigmoid maps centipawn to [0, 1] range: prob = 1 / (1 + 10^(-eval / 400))
def eval_to_prob(eval_val):
    return torch.sigmoid(eval_val / 400.0)

print("\nStarting PyTorch Texel's Tuning...")
num_epochs = 30
best_val_loss = float('inf')

for epoch in range(num_epochs):
    model.train()
    train_loss = 0.0
    for batch_x, batch_y in train_loader:
        batch_x, batch_y = batch_x.to(device), batch_y.to(device)
        
        optimizer.zero_grad()
        
        # Predict scores
        pred_scores = model(batch_x)
        
        # Apply Sigmoid mapping
        pred_prob = eval_to_prob(pred_scores)
        target_prob = eval_to_prob(batch_y)
        
        # Texel's Tuning Loss (MSE of Win Probabilities)
        loss = nn.MSELoss()(pred_prob, target_prob)
        loss.backward()
        optimizer.step()
        
        train_loss += loss.item() * batch_x.size(0)
    
    train_loss /= len(train_dataset)
    
    # Validation
    model.eval()
    val_loss = 0.0
    with torch.no_grad():
        for batch_x, batch_y in val_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            pred_scores = model(batch_x)
            pred_prob = eval_to_prob(pred_scores)
            target_prob = eval_to_prob(batch_y)
            loss = nn.MSELoss()(pred_prob, target_prob)
            val_loss += loss.item() * batch_x.size(0)
            
    val_loss /= len(val_dataset)
    scheduler.step(val_loss)
    
    print(f"Epoch {epoch+1:02d}/{num_epochs:02d} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}")
    
    # Save best parameters
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), "FEN_data/best_texel_model.pth")
        
        # Export weights to C++ array format
        weights_np = model.weights.detach().cpu().numpy()
        np.save("FEN_data/optimized_weights.npy", weights_np)

print("\nTraining completed! Best Validation Loss:", best_val_loss)

# Print some of the tuned piece values
tuned_weights = np.load("FEN_data/optimized_weights.npy")
print("\n--- Optimized Piece Values ---")
print(f"Pawn:   {tuned_weights[0]:.2f} (Orig: 100)")
print(f"Knight: {tuned_weights[1]:.2f} (Orig: 320)")
print(f"Bishop: {tuned_weights[2]:.2f} (Orig: 330)")
print(f"Rook:   {tuned_weights[3]:.2f} (Orig: 500)")
print(f"Queen:  {tuned_weights[4]:.2f} (Orig: 900)")
