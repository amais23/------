import json
import os

results_file = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/tournament_results_d8.json"
with open(results_file, "r") as f:
    results = json.load(f)

print(f"Total games analyzed: {len(results)}")
for game in results[:3]:
    print(f"\n=== Game {game['game_idx']+1} ===")
    print(f"White: {game['white_name']} vs Black: {game['black_name']}")
    print(f"Result: {game['result']}")
    history = game['history']
    print("First 10 moves and scores:")
    for h in history[:10]:
        print(f"  Ply {h['ply']}: {h['player']} ({h['agent']}) played {h['move_uci']} (score={h['score']}, time={h['time_elapsed']:.4f}s, nps={h['nps']})")
    print("Last 5 moves and scores:")
    for h in history[-5:]:
        print(f"  Ply {h['ply']}: {h['player']} ({h['agent']}) played {h['move_uci']} (score={h['score']}, time={h['time_elapsed']:.4f}s, nps={h['nps']})")
