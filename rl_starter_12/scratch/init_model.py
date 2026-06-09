import gymnasium as gym
from train import PacmanStrategicWrapper
from sb3_contrib import MaskablePPO
import shutil
import os

print("Backing up old model.zip...")
if os.path.exists("model.zip"):
    shutil.copy("model.zip", "model_old.zip")
    print("Backup completed: model_old.zip")

print("Initializing new dummy MaskablePPO model with 36 dims & 6 actions...")
raw_env = gym.make("ALE/MsPacman-v5", obs_type="ram")
env = PacmanStrategicWrapper(raw_env)
model = MaskablePPO("MlpPolicy", env, verbose=1)
model.save("model.zip")
env.close()
print("New model.zip saved successfully!")
