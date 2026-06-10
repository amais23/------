"""
BUG-5 驗證測試：超時導致 Board 腐敗 → SEGFAULT
使用正確的 observation 格式來測試搜尋引擎的超時安全性
"""
import sys, os, threading, time, traceback
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess_engine_d7_han

def make_starting_obs():
    """建立標準初始局面的 observation (8,8,111)"""
    obs = np.zeros((8, 8, 111), dtype=np.int8)
    
    # 白方棋子 (channels 7-12): PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING
    # 棋盤 row 0 = rank 8 (top), row 7 = rank 1 (bottom)
    
    # 白兵 (channel 7) - row 6 (rank 2)
    obs[6, :, 7] = 1
    
    # 白馬 (channel 8) - b1, g1
    obs[7, 1, 8] = 1; obs[7, 6, 8] = 1
    
    # 白象 (channel 9) - c1, f1
    obs[7, 2, 9] = 1; obs[7, 5, 9] = 1
    
    # 白車 (channel 10) - a1, h1
    obs[7, 0, 10] = 1; obs[7, 7, 10] = 1
    
    # 白后 (channel 11) - d1
    obs[7, 3, 11] = 1
    
    # 白王 (channel 12) - e1
    obs[7, 4, 12] = 1
    
    # 黑兵 (channel 13) - row 1 (rank 7)
    obs[1, :, 13] = 1
    
    # 黑馬 (channel 14) - b8, g8
    obs[0, 1, 14] = 1; obs[0, 6, 14] = 1
    
    # 黑象 (channel 15) - c8, f8
    obs[0, 2, 15] = 1; obs[0, 5, 15] = 1
    
    # 黑車 (channel 16) - a8, h8
    obs[0, 0, 16] = 1; obs[0, 7, 16] = 1
    
    # 黑后 (channel 17) - d8
    obs[0, 3, 17] = 1
    
    # 黑王 (channel 18) - e8
    obs[0, 4, 18] = 1
    
    # 易位權 (channels 0-3)
    obs[0, 0, 0] = 1  # K
    obs[0, 0, 1] = 1  # Q
    obs[0, 0, 2] = 1  # k
    obs[0, 0, 3] = 1  # q
    
    return obs

def make_complex_middlegame_obs():
    """建立複雜中局局面 (更容易觸發深層搜尋超時)"""
    obs = np.zeros((8, 8, 111), dtype=np.int8)
    
    # 白方: 王e1, 后d1, 車a1/h1, 象c1/c4, 馬f3, 兵 a2,b2,d4,e5,f2,g2,h2
    obs[7, 4, 12] = 1  # 白王 e1
    obs[7, 3, 11] = 1  # 白后 d1
    obs[7, 0, 10] = 1  # 白車 a1
    obs[7, 7, 10] = 1  # 白車 h1
    obs[7, 2, 9] = 1   # 白象 c1
    obs[3, 2, 9] = 1   # 白象 c4 (row=7-4+0=3 for rank 5... actually row = 8-rank, so rank 5 = row 3)
    obs[5, 5, 8] = 1   # 白馬 f3 (rank 3 = row 5)
    obs[6, 0, 7] = 1; obs[6, 1, 7] = 1  # 白兵 a2, b2
    obs[4, 3, 7] = 1   # 白兵 d4 (rank 4 = row 4)
    obs[3, 4, 7] = 1   # 白兵 e5 (rank 5 = row 3)
    obs[6, 5, 7] = 1; obs[6, 6, 7] = 1; obs[6, 7, 7] = 1  # 白兵 f2, g2, h2
    
    # 黑方: 王e8, 后d8, 車a8/f8, 象c8/b4, 馬c6, 兵 a7,b7,c7,d5,f7,g7,h7
    obs[0, 4, 18] = 1  # 黑王 e8
    obs[0, 3, 17] = 1  # 黑后 d8
    obs[0, 0, 16] = 1  # 黑車 a8
    obs[0, 5, 16] = 1  # 黑車 f8
    obs[0, 2, 15] = 1  # 黑象 c8
    obs[4, 1, 15] = 1  # 黑象 b4 (rank 4 = row 4)
    obs[2, 2, 14] = 1  # 黑馬 c6 (rank 6 = row 2)
    obs[1, 0, 13] = 1; obs[1, 1, 13] = 1; obs[1, 2, 13] = 1  # 黑兵 a7,b7,c7
    obs[3, 3, 13] = 1  # 黑兵 d5 (rank 5 = row 3)
    obs[1, 5, 13] = 1; obs[1, 6, 13] = 1; obs[1, 7, 13] = 1  # 黑兵 f7,g7,h7
    
    # 部分易位權
    obs[0, 0, 0] = 1  # K
    obs[0, 0, 1] = 1  # Q
    obs[0, 0, 2] = 1  # k
    
    return obs

def make_endgame_obs():
    """建立殘局局面 (少子，搜尋更深)"""
    obs = np.zeros((8, 8, 111), dtype=np.int8)
    
    # 白方: 王g1, 車d1, 兵 a2, f2, g2
    obs[7, 6, 12] = 1  # 白王 g1
    obs[7, 3, 10] = 1  # 白車 d1
    obs[6, 0, 7] = 1   # 白兵 a2
    obs[6, 5, 7] = 1   # 白兵 f2
    obs[6, 6, 7] = 1   # 白兵 g2
    
    # 黑方: 王g8, 車c8, 兵 a7, f7, g7
    obs[0, 6, 18] = 1  # 黑王 g8
    obs[0, 2, 16] = 1  # 黑車 c8
    obs[1, 0, 13] = 1  # 黑兵 a7
    obs[1, 5, 13] = 1  # 黑兵 f7
    obs[1, 6, 13] = 1  # 黑兵 g7
    
    return obs


print("=" * 60)
print("BUG-5 修復驗證測試：搜尋超時 Board 腐敗防護")
print("=" * 60)

OBSERVATIONS = [
    ("初始局面", make_starting_obs()),
    ("複雜中局", make_complex_middlegame_obs()),
    ("殘局", make_endgame_obs()),
]

mask = np.ones(4672, dtype=np.int8)

def run_stress(thread_id, num_calls=30):
    """壓力測試：重複呼叫 solve() 觸發超時"""
    engine = chess_engine_d7_han.SearchEngine()
    engine.init("")
    
    errors = []
    for i in range(num_calls):
        name, obs = OBSERVATIONS[i % len(OBSERVATIONS)]
        try:
            print(f"  T-{thread_id}: Calling [{i+1}/{num_calls}] {name}...", flush=True)
            result = engine.solve(obs, mask, -1)
            print(f"  T-{thread_id}: Completed [{i+1}/{num_calls}] {name} → action={result}", flush=True)
        except RuntimeError as e:
            print(f"  T-{thread_id}: RuntimeError [{i+1}/{num_calls}] {name} → {e}", flush=True)
        except Exception as e:
            print(f"  T-{thread_id}: Error [{i+1}/{num_calls}] {name} → {type(e).__name__}: {e}", flush=True)
            errors.append(f"[{i}] {name}: {type(e).__name__}: {e}")
    return errors

# ─── 測試 1: 單線程壓力 ───
print("\n📋 測試 1: 單線程壓力測試 (30 次呼叫)")
t0 = time.time()
errs = run_stress(0, 30)
dt = time.time() - t0
print(f"  完成！{dt:.1f}s, 錯誤: {len(errs)}")
if errs:
    for e in errs: print(f"    ⚠️ {e}")

# ─── 測試 2: 4 線程並行 ───
print("\n📋 測試 2: 4 線程並行壓力測試 (每線程 30 次)")
threads = []
results = [None] * 4

def worker(tid):
    try:
        results[tid] = run_stress(tid, 30)
    except Exception:
        results[tid] = [f"FATAL: {traceback.format_exc()}"]

t0 = time.time()
for i in range(4):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join(timeout=180)

dt = time.time() - t0
print(f"\n  總耗時 {dt:.1f}s")

all_ok = True
for i, r in enumerate(results):
    if r is None:
        print(f"  T-{i}: ❌ 超時或未完成")
        all_ok = False
    elif len(r) > 0:
        print(f"  T-{i}: ❌ {len(r)} 錯誤")
        for e in r: print(f"    {e}")
        all_ok = False
    else:
        print(f"  T-{i}: ✅ OK")

if all_ok:
    print("\n🎉 所有測試通過！BUG-5 修復有效，沒有 SEGFAULT！")
else:
    print("\n⚠️ 發現問題")

sys.exit(0 if all_ok else 1)
