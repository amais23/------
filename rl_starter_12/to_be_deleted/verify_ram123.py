import ale_py
import gymnasium as gym

gym.register_envs(ale_py)

def test_lives_level():
    env = gym.make("ALE/MsPacman-v5", obs_type="ram")
    obs, info = env.reset()
    
    print(f"Initial obs[123]: {obs[123]} (binary: {bin(obs[123])})")
    print(f"  Lower nybble (lives?): {obs[123] & 0x0F}")
    print(f"  Upper nybble (level?): {obs[123] >> 4}")
    
    for step in range(500):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            break
            
    print(f"End obs[123]: {obs[123]} (binary: {bin(obs[123])})")
    print(f"  Lower nybble (lives?): {obs[123] & 0x0F}")
    print(f"  Upper nybble (level?): {obs[123] >> 4}")
    
    env.close()

if __name__ == "__main__":
    test_lives_level()
