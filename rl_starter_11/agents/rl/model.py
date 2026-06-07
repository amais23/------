"""
Model configuration for Hybrid RL Agent
"""
from sb3_contrib import MaskablePPO

ALGORITHM     = MaskablePPO
POLICY        = "MlpPolicy"
POLICY_KWARGS = dict(
    net_arch=[512, 512],
)
SAVE_PATH     = "model"
