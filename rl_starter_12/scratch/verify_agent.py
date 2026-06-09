import ale_py
import gymnasium as gym
gym.register_envs(ale_py)
from agent import Agent

print("Initializing Pacman Agent...")
try:
    agent = Agent()
    print("Agent initialized successfully!")
    
    raw_env = gym.make("ALE/MsPacman-v5", obs_type="ram")
    obs, info = raw_env.reset()
    
    print("Agent taking action...")
    action = agent.act(obs, raw_env.action_space)
    print(f"Action taken: {action}")
    
    raw_env.close()
    print("Agent verification completed successfully!")
except Exception as e:
    print(f"Verification failed: {e}")
