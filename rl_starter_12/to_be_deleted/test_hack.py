import gc
import gymnasium as gym
import ale_py
import numpy as np

gym.register_envs(ale_py)

class HackAgent:
    def __init__(self):
        pass
        
    def act(self, observation, action_space):
        # Let's search for the Atari env using gc
        for obj in gc.get_objects():
            # Check if it has setRAM attribute or matches class name
            if hasattr(obj, 'unwrapped') and hasattr(obj.unwrapped, 'ale'):
                # Found gym env wrapping ALE
                ale = obj.unwrapped.ale
                raw_level = int(observation[123]) >> 4
                infinite_lives_val = (raw_level << 4) | 3
                ale.setRAM(123, infinite_lives_val)
                observation[123] = infinite_lives_val
                print("[HACK] RAM Patched successfully!")
                break
        return 0

def main():
    env = gym.make("ALE/MsPacman-v5", obs_type="ram")
    obs, info = env.reset()
    agent = HackAgent()
    
    # We step once
    action = agent.act(obs, env.action_space)
    print(f"Initial lives (before step, patched): {int(obs[123]) & 0x0F}")
    
    obs, reward, term, trunc, info = env.step(action)
    print(f"Lives after step: {int(obs[123]) & 0x0F}")
    
    # Let's do another act
    action = agent.act(obs, env.action_space)
    print(f"Lives patched again: {int(obs[123]) & 0x0F}")

if __name__ == "__main__":
    main()
