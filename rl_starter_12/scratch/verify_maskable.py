import gymnasium as gym
from train import PacmanStrategicWrapper
from sb3_contrib import MaskablePPO
import numpy as np

print("Testing PacmanStrategicWrapper with MaskablePPO...")
raw_env = gym.make("ALE/MsPacman-v5", obs_type="ram")
env = PacmanStrategicWrapper(raw_env)

obs, info = env.reset()
print("Reset successful!")
print("Obs shape:", obs.shape)

masks = env.action_masks()
print("Action masks:", masks)
assert len(masks) == 6, "Masks length must be 6"
assert isinstance(masks, np.ndarray), "Masks must be a numpy array"
assert masks.dtype == bool, "Masks dtype must be bool"

print("Taking a step...")
valid_actions = [i for i, m in enumerate(masks) if m]
action = valid_actions[0] if valid_actions else 2
next_obs, reward, term, trunc, info = env.step(action)
print("Step successful!")
print("Next obs shape:", next_obs.shape)
print("Reward:", reward)

model = MaskablePPO(
    "MlpPolicy",
    env,
    verbose=1
)
print("MaskablePPO initialized successfully!")
env.close()
print("All check-ups passed!")
