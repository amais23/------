import ale_py
import gymnasium as gym

gym.register_envs(ale_py)

def test_sl():
    env = gym.make("ALE/MsPacman-v5", obs_type="ram")
    obs, info = env.reset()
    
    # Clone state
    print("Cloning state...")
    saved_state = env.unwrapped.clone_state()
    
    # Take 50 random steps
    print("Taking 50 steps...")
    for _ in range(50):
        obs, reward, term, trunc, info = env.step(env.action_space.sample())
        if term or trunc:
            break
            
    px, py = int(obs[10]), int(obs[16])
    print(f"Position after 50 steps: ({px}, {py})")
    
    # Restore state
    print("Restoring state...")
    env.unwrapped.restore_state(saved_state)
    
    # Take 1 step and check position
    obs, reward, term, trunc, info = env.step(0)
    px_restored, py_restored = int(obs[10]), int(obs[16])
    print(f"Position after restore and 1 step: ({px_restored}, {py_restored})")
    
    env.close()

if __name__ == "__main__":
    test_sl()
