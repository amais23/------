import os
import sys
import gymnasium as gym
import numpy as np
import ale_py

gym.register_envs(ale_py)

# Add parent directory to sys.path so we can import agent and model
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agent import Agent

def evaluate_agent(episodes=5):
    env = gym.make("ALE/MsPacman-v5", obs_type="ram")
    agent = Agent()
    scores = []
    
    print(f"Evaluating Hybrid PPO Agent over {episodes} episodes...")
    for ep in range(episodes):
        obs, info = env.reset()
        agent.reset(obs)
        done = False
        total_reward = 0
        steps = 0
        
        while not done:
            action = agent.act(obs, env.action_space)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            steps += 1
            done = terminated or truncated
            
        scores.append(total_reward)
        print(f"Episode {ep + 1}: Score = {total_reward}, Steps = {steps}")
        
    env.close()
    mean_score = np.mean(scores)
    std_score = np.std(scores)
    print(f"\nAverage Score: {mean_score:.2f} ± {std_score:.2f}")

if __name__ == "__main__":
    evaluate_agent()
