import gymnasium as gym
from train import PacmanStrategicWrapper
import numpy as np
import ale_py

gym.register_envs(ale_py)

raw_env = gym.make("ALE/MsPacman-v5", obs_type="ram")
env = PacmanStrategicWrapper(raw_env)

obs, info = env.reset()
print(f"Initial remaining pellets: {len(env.remaining_pellets)}, energizers: {len(env.remaining_energizers)}")

# Let's run for 100 steps
for i in range(1, 101):
    masks = env.action_masks()
    valid_actions = [a for a, m in enumerate(masks) if m]
    action = 0 if (0 in valid_actions) else (valid_actions[0] if valid_actions else 2)
    obs, reward, term, trunc, info = env.step(action)
    px, py = int(env.last_raw_obs[10]), int(env.last_raw_obs[16])
    print(f"Step {i:3d} | Pacman: ({px:3d}, {py:3d}) | Reward: {reward:.4f} | Pellets remaining: {len(env.remaining_pellets):3d} | Energizers: {len(env.remaining_energizers)}")
    if term or trunc:
        print("Done!")
        break

env.close()
