# 實施計畫：RL 自動化進化管線

## 核心架構設計

為了避免 Python 動態載入（importlib.reload）C++ .so 檔案時常發生的記憶體區段錯誤（Segmentation Fault），我們採取「進程隔離」策略：

每次 Self-Play 都是透過 multiprocessing 產生全新的子進程（Sub-process），這些子進程會獨立載入當下最新編譯好的 chess_engine_d7_han。當部署階段重新編譯 .so 檔後，下一代的子進程自然就會載入全新的權重，完全無痛熱更新。

## 三大階段實作細節

### Self-Play 階段 (Data Generation)

使用 multiprocessing.Pool(10) 開啟 10 個核心。

為了避免陷入死局，設定最大步數限制（例如 200 步），超過視為和局。

收集對弈過程中的每一張靜態盤面 FEN 與最終結果（1, 0.5, 0），存入體驗回放池（Replay Buffer）。

### Train 階段 (Fine-Tuning)

從 Replay Buffer 取出資料（建議混合一點上一代的舊資料，避免「災難性遺忘 Catastrophic Forgetting」）。

進行 PyTorch 訓練，目標是最小化預測勝率與實際勝率的 MSE。

Deploy 階段 (Auto-Compilation)

透過 Python 的 re (正則表達式) 模組，直接開啟 deps/chess.hpp 或 engine.cpp，精準替換 PIECE_VAL 與 PST_* 陣列的字串。

使用 subprocess 呼叫 setup.py build_ext --inplace 重新編譯。

rl_pipeline.py 完整實作程式碼
請將以下程式碼儲存為 rl_pipeline.py，放在與 setup.py 同層級的目錄中。

```python
import os
import re
import time
import subprocess
import multiprocessing
import chess
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# ═══════════════════════════════════════════
# 系統與訓練超參數配置
# ═══════════════════════════════════════════
NUM_CORES = 10
GAMES_PER_CORE = 15        # 每代約產生 150 盤對局
GENERATIONS = 4            # 總共進化 4 代 (總耗時約 2 小時)
MAX_MOVES_PER_GAME = 100   # 避免無限期對局
SCALE_FACTOR = 4.028981    # 你的權重放大基準

# ═══════════════════════════════════════════
# 階段 1: Self-Play 工作函數 (在獨立進程中執行)
# ═══════════════════════════════════════════
def worker_self_play(worker_id):
    # 在子進程中才 import，確保每次都載入硬碟上最新編譯的 .so 檔
    import chess_engine_d7_han as ce
    
    board = chess.Board()
    engine_w = ce.SearchEngine()
    engine_b = ce.SearchEngine()
    engine_w.init("")
    engine_b.init("")
    engine_w.new_game()
    engine_b.new_game()
    
    game_history = []
    
    while not board.is_game_over() and board.fullmove_number < MAX_MOVES_PER_GAME:
        fen = board.fen()
        # 排除包含吃子或將軍的動態盤面 (Quiet positions only)
        is_quiet = not board.is_check() and not board.is_capture(board.peek()) if len(board.move_stack) > 0 else True
        if is_quiet:
            game_history.append(fen)
            
        # 將 FEN 轉為 Observation 或直接交給引擎 (根據你實際的 Python 接口)
        # 這裡以假設你的引擎有一個 get_best_move 接口為例
        try:
            if board.turn == chess.WHITE:
                # 請根據你的 API 替換成實際取 action 的方法
                action = engine_w.solve(fen_to_obs(fen), get_mask(board)) 
            else:
                action = engine_b.solve(fen_to_obs(fen), get_mask(board))
                
            move = action_to_move(action) # 假設你有這個轉換函數
            board.push(move)
        except Exception as e:
            # 捕捉超時或其他例外，提早結束這盤
            break

    # 判定勝負
    res = board.result()
    if res == "1-0": reward = 1.0
    elif res == "0-1": reward = 0.0
    else: reward = 0.5 # 和局或到達步數上限
    
    return [(f, reward) for f in game_history]

# 輔助 Dummy 函數 (請替換為你實際的 PettingZoo 轉換邏輯)
def fen_to_obs(fen): return np.zeros((8,8,111), dtype=np.int8)
def get_mask(board): return np.ones(4672, dtype=np.int8)
def action_to_move(action): return chess.Move.from_uci("e2e4") # 替換為實際邏輯

# ═══════════════════════════════════════════
# 階段 2: PyTorch 訓練與特徵提取
# ═══════════════════════════════════════════
class RLDataset(Dataset):
    def __init__(self, data):
        import chess_engine_d7_han as ce
        self.features = []
        self.targets = []
        for fen, target in data:
            feat = ce.extract_features(fen)
            self.features.append(feat)
            self.targets.append(target)
            
    def __len__(self): return len(self.targets)
    def __getitem__(self, idx):
        return torch.tensor(self.features[idx], dtype=torch.float32), torch.tensor([self.targets[idx]], dtype=torch.float32)

class LinearEvalModel(nn.Module):
    def __init__(self, initial_weights_path=None):
        super().__init__()
        self.fc = nn.Linear(459, 1, bias=False)
        # 如果有之前的權重，載入作為基礎
        if initial_weights_path and os.path.exists(initial_weights_path):
            weights = np.load(initial_weights_path)
            self.fc.weight.data = torch.tensor(weights, dtype=torch.float32).unsqueeze(0)

    def forward(self, x):
        return torch.sigmoid((self.fc(x) / 400.0) * 2.302585)

def train_network(dataset_tuples, generation):
    print(f"啟動 PyTorch 訓練，資料量: {len(dataset_tuples)} FENs...")
    dataset = RLDataset(dataset_tuples)
    dataloader = DataLoader(dataset, batch_size=2048, shuffle=True)
    
    # 載入上一代的權重作為起點 (如果存在)
    model = LinearEvalModel(initial_weights_path="latest_weights.npy")
    optimizer = optim.Adam(model.parameters(), lr=0.5) # 微調 LR 較小
    criterion = nn.MSELoss()
    
    model.train()
    for epoch in range(3): # 快速微調 3 個 Epoch
        total_loss = 0
        for x, y in dataloader:
            optimizer.zero_grad()
            pred = model(x)
            loss = criterion(pred, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"  Epoch {epoch+1} Loss: {total_loss/len(dataloader):.4f}")
        
    new_weights = model.fc.weight.data.numpy()[0]
    np.save("latest_weights.npy", new_weights) # 儲存供下一代使用
    return new_weights

# ═══════════════════════════════════════════
# 階段 3: 自動回填 C++ 原始碼與重新編譯
# ═══════════════════════════════════════════
def update_cpp_and_recompile(raw_weights):
    print("正在將新權重寫回 C++ 並重新編譯...")
    target_file = "deps/chess.hpp" # 請確認你的常數是寫在哪個檔案
    
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 等比例放大權重並四捨五入
    scaled = np.round(raw_weights * SCALE_FACTOR).astype(int)
    
    # 1. 替換 PIECE_VAL (前 5 個特徵)
    piece_val_str = f"static constexpr int PIECE_VAL[7] = {{{scaled[0]}, {scaled[1]}, {scaled[2]}, {scaled[3]}, {scaled[4]}, 20000, 0}};"
    content = re.sub(r"static constexpr int PIECE_VAL\[7\]\s*=\s*\{.*?\};", piece_val_str, content)
    
    # 2. 替換 PST 陣列 (這裡以 PST_PAWN 為例，索引 5~68)
    pst_pawn_vals = ", ".join(map(str, scaled[5:69]))
    pst_pawn_str = f"static constexpr int16_t PST_PAWN[64] = {{{pst_pawn_vals}}};"
    content = re.sub(r"static constexpr int16_t PST_PAWN\[64\]\s*=\s*\{.*?\};", pst_pawn_str, content, flags=re.DOTALL)
    
    # TODO: 依樣畫葫蘆，寫入 PST_KNIGHT, BISHOP, ROOK, QUEEN 等...

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    # 呼叫系統指令重新編譯
    # 使用 inplace 覆蓋現有 .so 檔
    result = subprocess.run(["python", "setup.py", "build_ext", "--inplace"], capture_output=True, text=True)
    if result.returncode != 0:
        print("編譯失敗！錯誤訊息：\n", result.stderr)
        exit(1)
    print("編譯成功，新一代引擎部署完畢！")

# ═══════════════════════════════════════════
# 主管線 Orchestrator
# ═══════════════════════════════════════════
if __name__ == "__main__":
    replay_buffer = [] # 跨代資料保留，避免遺忘
    
    for gen in range(1, GENERATIONS + 1):
        print(f"\n{'='*50}\n🚀 啟動進化世代 Generation {gen}/{GENERATIONS}\n{'='*50}")
        
        # Phase 1: Self-Play
        start_time = time.time()
        with multiprocessing.Pool(NUM_CORES) as pool:
            results = pool.map(worker_self_play, range(NUM_CORES * GAMES_PER_CORE))
            
        gen_data = [item for sublist in results for item in sublist]
        replay_buffer.extend(gen_data)
        
        # 限制 Replay Buffer 大小，保留最新的 10 萬筆
        if len(replay_buffer) > 100000:
            replay_buffer = replay_buffer[-100000:]
            
        print(f"Self-Play 結束，本代產生 {len(gen_data)} FENs，耗時 {time.time() - start_time:.1f} 秒")
        
        # Phase 2: Train
        new_weights = train_network(replay_buffer, gen)
        
        # Phase 3: Deploy
        update_cpp_and_recompile(new_weights)
```

### 上線前的最後準備

在正式讓這個腳本跑 2 小時之前，程式碼中有標註 TODO 以及需要替換成你實際介面的地方（例如 fen_to_obs 和你的 C++ 實際寫入檔案的路徑）。
