import sys
import os
import numpy as np

# 新增當前目錄至 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from d4_pro.agent import Agent as D4Agent
from d6_cpp.agent import Agent as D6Agent
from d7_rl.agent import Agent as D7Agent

print("Importing agents successful!")

obs = np.zeros((8, 8, 111), dtype=np.int8)
# 第 12 和 18 頻道代表國王位置，如果沒有國王，重建會出錯，所以我們在 obs 中放入兩個國王
# 白國王在 (7,4,12)，黑國王在 (0,4,18)
obs[7, 4, 12] = 1
obs[0, 4, 18] = 1

mask = np.ones(4672, dtype=np.int8)

print("Testing d4_pro...")
a4 = D4Agent()
act4 = a4.act(obs, mask)
print(f"d4_pro action: {act4}, nps: {a4.last_nps}, score: {a4.last_score}")

print("Testing d6_cpp...")
a6 = D6Agent()
act6 = a6.act(obs, mask)
print(f"d6_cpp action: {act6}, nps: {a6.last_nps}, score: {a6.last_score}")

print("Testing d7_rl...")
a7 = D7Agent()
act7 = a7.act(obs, mask)
print(f"d7_rl action: {act7}, nps: {a7.last_nps}, score: {a7.last_score}")
