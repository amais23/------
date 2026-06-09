import ale_py
import gymnasium as gym
import numpy as np

gym.register_envs(ale_py)

def run_inspect():
    env = gym.make("ALE/MsPacman-v5", obs_type="ram")
    obs, info = env.reset()
    
    prev_ram = obs.copy()
    step = 0
    
    # We will run for 10,000 steps to see if any level transitions occur
    # or if we can find RAM locations that change when dots_eaten (RAM[119]) resets.
    for step in range(10000):
        action = env.action_space.sample()
        next_obs, reward, terminated, truncated, info = env.step(action)
        
        # Check if RAM[119] (dots eaten) has decreased (which means reset / new level or new game)
        # RAM[119] is dots eaten.
        if next_obs[119] < prev_ram[119] and prev_ram[119] > 10:
            print(f"Step {step}: dots eaten reset from {prev_ram[119]} to {next_obs[119]}!")
            # Print which RAM bytes changed significantly
            changed_bytes = []
            for idx in range(128):
                if next_obs[idx] != prev_ram[idx]:
                    changed_bytes.append(f"RAM[{idx}]: {prev_ram[idx]} -> {next_obs[idx]}")
            print("  Changed RAM bytes:")
            print("    " + ", ".join(changed_bytes[:15]))
            
        prev_ram = next_obs.copy()
        if terminated or truncated:
            obs, info = env.reset()
            prev_ram = obs.copy()
            
    env.close()

if __name__ == "__main__":
    run_inspect()
