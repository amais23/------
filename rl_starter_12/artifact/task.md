# MsPacman Option D Optimization Checklist

- `[x]` 實作十一大系統優化代碼
  - `[x]` 修改 [model.py](file:///Users/Shared/西洋棋代理人/rl_starter_12/model.py)：新增鬼魂動量過濾、曼哈頓估算安全退路、前進動量分數、傳送門自動連通等 (透過修改 [generate_model.py](file:///Users/Shared/西洋棋代理人/rl_starter_12/scratch/generate_model.py) 實現)
  - `[x]` 修改 [train.py](file:///Users/Shared/西洋棋代理人/rl_starter_12/train.py)：新增動作覆蓋重罰 (-20)、分立地圖組管理、鬼魂前幀追蹤、生命減少清空 `prev_p`
  - `[x]` 修改 [agent.py](file:///Users/Shared/西洋棋代理人/rl_starter_12/agent.py)：分立地圖管理、追蹤 `last_action` 與 `prev_ghosts_pos`，死亡生命重置
- `[ ]` Maze 2+ 地圖完全收集與硬編碼
  - `[ ]` 撰寫並執行 [collect_all_mazes.py](file:///Users/Shared/西洋棋代理人/rl_starter_12/scratch/collect_all_mazes.py) 自動採集四張地圖鄰接表
  - `[ ]` 將四張地圖以 zlib + base64 硬編碼寫死在 [model.py](file:///Users/Shared/西洋棋代理人/rl_starter_12/model.py) 中，徹底消滅開局陣痛期
- `[ ]` 本地訓練與驗證
  - `[ ]` 重新啟動 `train.py` 進行 2M 步分層 PPO 訓練
  - `[ ]` 評估分層 PPO 代理人的平均得分與關卡突破率
- `[ ]` 上傳與測試
  - `[ ]` 執行 `run.py` 上傳至 MLArena 平台
