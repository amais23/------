import json
import os

def main():
    path = '/Users/Shared/西洋棋代理人/rl_starter_12/scratch/complete_levels.json'
    if not os.path.exists(path):
        print(f"Error: {path} not found.")
        return

    with open(path, 'r') as f:
        data = json.load(f)

    levels = sorted(data.keys())
    print(f"Loaded levels: {levels}")
    for lvl in levels:
        print(f"  {lvl}: {len(data[lvl])} nodes")

    print("\n--- Pairwise Jaccard Similarity (node coordinate overlap) ---")
    
    # Extract coordinate sets
    coord_sets = {}
    for lvl in levels:
        coord_sets[lvl] = set(data[lvl].keys())

    # Print a matrix / table of overlaps
    # Similarity = |A intersect B| / min(|A|, |B|) or Jaccard: |A intersect B| / |A union B|
    # Let's show both absolute overlap count and Jaccard percentage.
    for i in range(len(levels)):
        for j in range(i + 1, len(levels)):
            l1, l2 = levels[i], levels[j]
            set1, set2 = coord_sets[l1], coord_sets[l2]
            intersection = set1.intersection(set2)
            union = set1.union(set2)
            
            jaccard = len(intersection) / len(union) if len(union) > 0 else 0
            overlap_pct_1 = len(intersection) / len(set1) if len(set1) > 0 else 0
            overlap_pct_2 = len(intersection) / len(set2) if len(set2) > 0 else 0
            
            print(f"{l1} vs {l2}:")
            print(f"  Overlap count: {len(intersection)}")
            print(f"  Jaccard Sim  : {jaccard:.2%}")
            print(f"  % of {l1} in {l2}: {overlap_pct_1:.2%}")
            print(f"  % of {l2} in {l1}: {overlap_pct_2:.2%}")
            print("-" * 30)

if __name__ == '__main__':
    main()
