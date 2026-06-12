import torch
import chess
import sys

sys.path.insert(0, "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8")

preprocessed_file = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/research/data/processed/preprocessed_dataset.pt"

def test():
    data = torch.load(preprocessed_file)
    print(f"Total samples: {len(data)}")
    
    # Print first 10 samples
    for i in range(10):
        us, them, score = data[i]
        print(f"Sample {i}: score = {score}")

if __name__ == '__main__':
    test()
