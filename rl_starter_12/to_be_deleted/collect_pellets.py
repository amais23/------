import ale_py
import gymnasium as gym
import json
import os

gym.register_envs(ale_py)

def collect_pellets(episodes=150):
    env = gym.make("ALE/MsPacman-v5", obs_type="ram")
    
    dots = set()
    energizers = set()
    
    print(f"Collecting dot and energizer coordinates over {episodes} episodes...")
    for ep in range(episodes):
        obs, info = env.reset()
        done = False
        
        while not done:
            action = env.action_space.sample()
            next_obs, reward, terminated, truncated, info = env.step(action)
            
            px, py = int(next_obs[10]), int(next_obs[16])
            
            if reward == 10:
                dots.add((px, py))
            elif reward == 50:
                energizers.add((px, py))
                
            done = terminated or truncated
            
        if (ep + 1) % 30 == 0:
            print(f"Episode {ep+1}/{episodes}: Collected {len(dots)} dots, {len(energizers)} energizers")
            
    env.close()
    
    # Save to JSON
    output = {
        "dots": [list(p) for p in sorted(dots)],
        "energizers": [list(p) for p in sorted(energizers)]
    }
    
    out_path = os.path.join(os.path.dirname(__file__), "pellets_data.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
        
    print(f"Saved pellet coordinates to {out_path}")

if __name__ == "__main__":
    collect_pellets(150)
