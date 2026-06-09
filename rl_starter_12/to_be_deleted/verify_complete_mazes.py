import json
import os

json_path = "/Users/Shared/西洋棋代理人/rl_starter_12/scratch/complete_mazes.json"
if os.path.exists(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
        for m_id in [1, 2, 3, 4]:
            key = f"maze_{m_id}"
            if key in data:
                print(f"{key} has {len(data[key])} nodes.")
            else:
                print(f"{key} is missing.")
else:
    print("complete_mazes.json does not exist!")
