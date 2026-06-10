import chess_engine_d7_han
import numpy as np

def make_starting_obs():
    obs = np.zeros((8, 8, 111), dtype=np.int8)
    obs[6, :, 7] = 1
    obs[7, 1, 8] = 1; obs[7, 6, 8] = 1
    obs[7, 2, 9] = 1; obs[7, 5, 9] = 1
    obs[7, 0, 10] = 1; obs[7, 7, 10] = 1
    obs[7, 3, 11] = 1
    obs[7, 4, 12] = 1
    obs[1, :, 13] = 1
    obs[0, 1, 14] = 1; obs[0, 6, 14] = 1
    obs[0, 2, 15] = 1; obs[0, 5, 15] = 1
    obs[0, 0, 16] = 1; obs[0, 7, 16] = 1
    obs[0, 3, 17] = 1
    obs[0, 4, 18] = 1
    obs[0, 0, 0] = 1  # K
    obs[0, 0, 1] = 1  # Q
    obs[0, 0, 2] = 1  # k
    obs[0, 0, 3] = 1  # q
    return obs

def make_complex_middlegame_obs():
    obs = np.zeros((8, 8, 111), dtype=np.int8)
    obs[7, 4, 12] = 1  # 白王 e1
    obs[7, 3, 11] = 1  # 白后 d1
    obs[7, 0, 10] = 1  # 白車 a1
    obs[7, 7, 10] = 1  # 白車 h1
    obs[7, 2, 9] = 1   # 白象 c1
    obs[3, 2, 9] = 1   # 白象 c4
    obs[5, 5, 8] = 1   # 白馬 f3
    obs[6, 0, 7] = 1; obs[6, 1, 7] = 1  # 白兵 a2, b2
    obs[4, 3, 7] = 1   # 白兵 d4
    obs[3, 4, 7] = 1   # 白兵 e5
    obs[6, 5, 7] = 1; obs[6, 6, 7] = 1; obs[6, 7, 7] = 1  # 白兵 f2, g2, h2
    
    obs[0, 4, 18] = 1  # 黑王 e8
    obs[0, 3, 17] = 1  # 黑后 d8
    obs[0, 0, 16] = 1  # 黑車 a8
    obs[0, 5, 16] = 1  # 黑車 f8
    obs[0, 2, 15] = 1  # 黑象 c8
    obs[4, 1, 15] = 1  # 黑象 b4
    obs[2, 2, 14] = 1  # 黑馬 c6
    obs[1, 0, 13] = 1; obs[1, 1, 13] = 1; obs[1, 2, 13] = 1  # 黑兵 a7,b7,c7
    obs[3, 3, 13] = 1  # 黑兵 d5
    obs[1, 5, 13] = 1; obs[1, 6, 13] = 1; obs[1, 7, 13] = 1  # 黑兵 f7,g7,h7
    
    obs[0, 0, 0] = 1  # K
    obs[0, 0, 1] = 1  # Q
    obs[0, 0, 2] = 1  # k
    return obs

def make_endgame_obs():
    obs = np.zeros((8, 8, 111), dtype=np.int8)
    obs[7, 6, 12] = 1  # 白王 g1
    obs[7, 3, 10] = 1  # 白車 d1
    obs[6, 0, 7] = 1   # 白兵 a2
    obs[6, 5, 7] = 1   # 白兵 f2
    obs[6, 6, 7] = 1   # 白兵 g2
    
    obs[0, 6, 18] = 1  # 黑王 g8
    obs[0, 2, 16] = 1  # 黑車 c8
    obs[1, 0, 13] = 1  # 黑兵 a7
    obs[1, 5, 13] = 1  # 黑兵 f7
    obs[1, 6, 13] = 1  # 黑兵 g7
    return obs

def py_rebuild_fen(obs):
    board_chars = [[' ' for _ in range(8)] for _ in range(8)]
    white_pieces = ['P', 'N', 'B', 'R', 'Q', 'K']
    black_pieces = ['p', 'n', 'b', 'r', 'q', 'k']
    
    for i in range(6):
        ch = 7 + i
        p = white_pieces[i]
        for r in range(8):
            for c in range(8):
                if obs[r, c, ch]:
                    if p == 'P' and r == 7:
                        continue
                    board_chars[r][c] = p
                    
    for i in range(6):
        ch = 13 + i
        p = black_pieces[i]
        for r in range(8):
            for c in range(8):
                if obs[r, c, ch]:
                    if p == 'p' and r == 0:
                        continue
                    board_chars[r][c] = p
                    
    ep_str = "-"
    for col in range(8):
        if obs[7, col, 7]:
            board_chars[4][col] = 'P'
            ep_str = chr(ord('a') + col) + "3"
    for col in range(8):
        if obs[0, col, 13]:
            board_chars[3][col] = 'p'
            ep_str = chr(ord('a') + col) + "6"
            
    placement = ""
    for r in range(8):
        empty_count = 0
        for c in range(8):
            pc = board_chars[r][c]
            if pc == ' ':
                empty_count += 1
            else:
                if empty_count > 0:
                    placement += str(empty_count)
                    empty_count = 0
                placement += pc
        if empty_count > 0:
            placement += str(empty_count)
        if r < 7:
            placement += "/"
            
    castling_str = ""
    if obs[0, 0, 0]: castling_str += "K"
    if obs[0, 0, 1]: castling_str += "Q"
    if obs[0, 0, 2]: castling_str += "k"
    if obs[0, 0, 3]: castling_str += "q"
    if not castling_str: castling_str = "-"
    
    return placement + " w " + castling_str + " " + ep_str + " 0 1"

print("Starting:")
print(py_rebuild_fen(make_starting_obs()))
print("Complex:")
print(py_rebuild_fen(make_complex_middlegame_obs()))
print("Endgame:")
print(py_rebuild_fen(make_endgame_obs()))
