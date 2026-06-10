#!/usr/bin/env python3
"""
🕹️  MsPacman Human Play — Per-Level Node Recorder
----------------------------------------------------
Stores nodes separately for EACH LEVEL so you can later
compare which levels share the same maze layout.

Data is saved to: complete_levels.json
  keys: level_0, level_1, level_2, level_3, ...

Controls:
  ↑ ↓ ← →   Move Pac-Man
  Space       NOOP
  R           Reset current episode (reload state if available)
  5/6/7/8     Jump to Level 0/2/4/6  (loads .pkl state if saved)
  Q / Esc     Quit and save
"""

import os, sys, json, pickle, time
from collections import defaultdict

import ale_py
import gymnasium as gym
import numpy as np
import pygame

# Import from model.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model import (
    extract_strategic_features, init_pellets_and_energizers,
    get_maze_id, align_coordinates_to_graph
)

gym.register_envs(ale_py)

SCRATCH    = os.path.dirname(os.path.abspath(__file__))
JSON_PATH  = os.path.join(SCRATCH, "data", "complete_levels.json")

# ── Display ────────────────────────────────────────────────────────────────
GAME_W, GAME_H = 160, 210
SCALE          = 4
HUD_W          = 300
FEAT_W         = 300
WIN_W          = GAME_W * SCALE + HUD_W + FEAT_W
WIN_H          = GAME_H * SCALE
FPS            = 30

# ── Colors ─────────────────────────────────────────────────────────────────
BG        = (15,  15,  25)
HUD_BG    = (20,  20,  35)
BORDER    = (60,  60, 100)
WHITE     = (240, 240, 250)
YELLOW    = (255, 220,  50)
CYAN      = ( 80, 220, 220)
GREEN     = ( 60, 220, 100)
RED       = (220,  70,  70)
ORANGE    = (255, 160,  40)
GRAY      = (120, 120, 140)
DARK_GRAY = ( 40,  40,  55)
PURPLE    = (160,  80, 220)
PINK      = (255, 120, 180)
TEAL      = ( 50, 180, 160)

KEY_ACTION = {
    pygame.K_UP:    1, pygame.K_RIGHT: 2,
    pygame.K_LEFT:  3, pygame.K_DOWN:  4,
    pygame.K_w:     1, pygame.K_d:     2,
    pygame.K_a:     3, pygame.K_s:     4,
    pygame.K_SPACE: 0,
}

KEY_LEVEL_SELECT = {
    pygame.K_5: 0,
    pygame.K_6: 2,
    pygame.K_7: 4,
    pygame.K_8: 6,
}

# ── Level → color palette ─────────────────────────────────────────────────
LEVEL_COLORS = [CYAN, PINK, ORANGE, PURPLE, GREEN, TEAL, YELLOW, WHITE]

def level_color(lv):
    return LEVEL_COLORS[lv % len(LEVEL_COLORS)]

# ── JSON I/O ───────────────────────────────────────────────────────────────
def load_graphs():
    """Load all level graphs from JSON. Keys: level_0, level_1, ..."""
    graphs = defaultdict(lambda: defaultdict(set))
    if os.path.exists(JSON_PATH):
        try:
            raw = json.load(open(JSON_PATH))
            for key, adj in raw.items():
                lv = int(key.split("_")[1])
                for k_str, neighbors in adj.items():
                    kx, ky = map(int, k_str.split(","))
                    for nx, ny in neighbors:
                        graphs[lv][(kx, ky)].add((nx, ny))
            totals = {k: len(v) for k, v in graphs.items()}
            print(f"[Load] {totals}")
        except Exception as e:
            print(f"[Load] Error: {e}")
    return graphs

def save_graphs(graphs):
    out = {}
    for lv, adj in graphs.items():
        out[f"level_{lv}"] = {
            f"{k[0]},{k[1]}": [list(v) for v in vs]
            for k, vs in adj.items()
        }
    json.dump(out, open(JSON_PATH, "w"), indent=2)
    totals = {k: len(v) for k, v in graphs.items()}
    print(f"[Save] {totals}")

# ── Graph update ───────────────────────────────────────────────────────────
def update_graph(graphs, px, py, prev_p, level):
    if prev_p is None:
        return
    ppx, ppy = prev_p
    if (ppx, ppy) == (px, py):
        return
    dist    = abs(px - ppx) + abs(py - ppy)
    is_warp = (ppy == py) and ((ppx < 25 and px > 140) or (ppx > 140 and px < 25))
    if dist <= 15 or is_warp:
        g = graphs[level]
        g[(ppx, ppy)].add((px, py))
        g[(px, py)].add((ppx, ppy))

# ── State persistence ──────────────────────────────────────────────────────
def state_path(level):
    return os.path.join(SCRATCH, "data", f"level_{level}_state.pkl")

def save_state(env, level):
    try:
        s = env.unwrapped.clone_state()
        pickle.dump(s, open(state_path(level), "wb"))
        print(f"[State] Saved level {level} → level_{level}_state.pkl")
    except Exception as e:
        print(f"[State] Save error: {e}")

def load_state(env, level):
    p = state_path(level)
    if not os.path.exists(p):
        return False
    try:
        s = pickle.load(open(p, "rb"))
        env.unwrapped.restore_state(s)
        print(f"[State] Loaded level {level} from {p}")
        return True
    except Exception as e:
        print(f"[State] Load error: {e}")
        return False

# ── HUD ────────────────────────────────────────────────────────────────────
def draw_hud(surface, font_lg, font_md, font_sm, state, graphs):
    hud_x = GAME_W * SCALE
    pygame.draw.rect(surface, HUD_BG, (hud_x, 0, HUD_W, WIN_H))
    pygame.draw.line(surface, BORDER, (hud_x, 0), (hud_x, WIN_H), 2)

    y = 12
    def row(label, value, color=WHITE, lc=GRAY):
        nonlocal y
        surface.blit(font_sm.render(label, True, lc),    (hud_x + 12, y))
        surface.blit(font_md.render(str(value), True, color), (hud_x + 12, y + 15))
        y += 40

    def section(title, color=CYAN):
        nonlocal y
        pygame.draw.rect(surface, DARK_GRAY, (hud_x + 6, y, HUD_W - 12, 24), border_radius=4)
        surface.blit(font_md.render(title, True, color), (hud_x + 12, y + 3))
        y += 30

    def sep():
        nonlocal y
        pygame.draw.line(surface, BORDER, (hud_x + 6, y), (hud_x + HUD_W - 12, y))
        y += 8

    # Title
    surface.blit(font_lg.render("📊 LEVEL RECORDER", True, YELLOW), (hud_x + 8, y))
    y += 34; sep()

    section("GAME STATUS", CYAN)
    row("LEVEL",  f"{state['level']}  (RAM={state['raw_level']})", PURPLE)
    row("LIVES",  "♥ " * state['lives'], GREEN if state['lives'] >= 3 else RED)
    row("SCORE",  f"{state['score']:,.0f}", YELLOW)
    row("POS",    f"({state['px']}, {state['py']})", WHITE)
    if "pellets" in state:
        row("PELLETS", f"{state['pellets']}", ORANGE)
    if "energizers" in state:
        row("ENERGIZERS", f"{state['energizers']}", GREEN)
    sep()

    section("PER-LEVEL NODES", GREEN)
    # Show last 8 levels with node counts
    all_levels = sorted(graphs.keys())
    shown = all_levels[-8:] if len(all_levels) > 8 else all_levels
    cur_lv = state['raw_level']
    for lv in shown:
        n   = len(graphs[lv])
        col = level_color(lv)
        bar_ratio = min(n / 1800, 1.0)
        lbl = font_sm.render(f"Lv{lv}", True, YELLOW if lv == cur_lv else GRAY)
        cnt = font_sm.render(f"{n}", True, col)
        surface.blit(lbl, (hud_x + 12, y))
        surface.blit(cnt, (hud_x + 60, y))
        bar_bg = pygame.Rect(hud_x + 100, y + 2, HUD_W - 116, 8)
        pygame.draw.rect(surface, DARK_GRAY, bar_bg, border_radius=3)
        if n > 0:
            bar_fill = pygame.Rect(hud_x + 100, y + 2, int((HUD_W - 116) * bar_ratio), 8)
            pygame.draw.rect(surface, col, bar_fill, border_radius=3)
        y += 18
    if not shown:
        surface.blit(font_sm.render("(no data yet)", True, GRAY), (hud_x + 12, y))
        y += 18
    sep()

    section("CONTROLS", TEAL)
    for k, a in [("↑↓←→", "Move"), ("Space", "NOOP"),
                 ("P", "Pause / Resume"),
                 ("5/6/7/8", "Load Level 0,2,4,6"), ("R", "Reset/Reload"),
                 ("Q/Esc", "Quit & Save")]:
        surface.blit(font_sm.render(k, True, YELLOW), (hud_x + 12, y))
        surface.blit(font_sm.render(f"→ {a}", True, GRAY), (hud_x + 80, y))
        y += 18
    y += 4

    save_txt = font_sm.render(state.get("last_save", ""), True, GREEN)
    surface.blit(save_txt, (hud_x + 12, y))

def draw_notification(surface, font_lg, text, color=YELLOW, alpha=255):
    surf = font_lg.render(text, True, color)
    surf.set_alpha(alpha)
    rect = surf.get_rect(center=(GAME_W * SCALE // 2, WIN_H // 2))
    shadow = font_lg.render(text, True, (0, 0, 0))
    shadow.set_alpha(alpha // 2)
    surface.blit(shadow, rect.move(2, 2))
    surface.blit(surf, rect)

# 36 feature labels (0-indexed, matching extract_strategic_features order)
FEAT_LABELS = [
    # 0-1: Pac-Man position
    "f00 PacX/160",
    "f01 PacY/160",
    # 2-5: Ghost distances exp(-0.05*d)
    "f02 G0 dist↑",
    "f03 G1 dist↑",
    "f04 G2 dist↑",
    "f05 G3 dist↑",
    # 6-13: Ghost relative directions (dx/L1, dy/L1)
    "f06 G0 dx/L1",
    "f07 G0 dy/L1",
    "f08 G1 dx/L1",
    "f09 G1 dy/L1",
    "f10 G2 dx/L1",
    "f11 G2 dy/L1",
    "f12 G3 dx/L1",
    "f13 G3 dy/L1",
    # 14: Closest non-blue ghost distance
    "f14 MinDanger↑",
    # 15: Blue timer
    "f15 BlueTimer",
    # 16: Closest pellet distance
    "f16 PelletDist↑",
    # 17: Closest energizer distance
    "f17 EnergyDist↑",
    # 18: Energizers remaining ratio
    "f18 Energz Ratio",
    # 19: RAM pellet count tanh
    "f19 RAM Pellets",
    # 20: Lives
    "f20 Lives/5",
    # 21: Level
    "f21 Level/10",
    # 22-25: Direction safety UP/RIGHT/LEFT/DOWN
    "f22 Safe UP↑",
    "f23 Safe RIGHT↑",
    "f24 Safe LEFT↑",
    "f25 Safe DOWN↑",
    # 26: Dead-end flag
    "f26 DeadEnd",
    # 27-30: Ghosts in house flags
    "f27 G0 InHouse",
    "f28 G1 InHouse",
    "f29 G2 InHouse",
    "f30 G3 InHouse",
    # 31: Pacman in house
    "f31 Pac InHouse",
    # 32: Closest blue ghost distance
    "f32 BlueGst↑",
    # 33: Blue ghost count ratio
    "f33 BlueGst Ratio",
    # 34: Fruit distance exp(-0.05*d)
    "f34 FruitDist↑",
    # 35: Fruit exists flag
    "f35 FruitExists",
    # 36-37: Fruit position normalized (obs[11]/160, obs[17]/160); 0 if no fruit
    "f36 FruitX/160",
    "f37 FruitY/160",
    # 38: Pellet ratio (eaten / max)
    "f38 Pellet Ratio",
    # 39: Ghost Chase/Scatter Timer
    "f39 ChaseTimer",
    # 40-43: Player direction one-hot
    "f40 Player Dir UP",
    "f41 Player Dir RT",
    "f42 Player Dir DN",
    "f43 Player Dir LT",
]

def draw_feat_hud(surface, font_md, font_sm, feat_vec, obs):
    feat_x = GAME_W * SCALE + HUD_W
    pygame.draw.rect(surface, HUD_BG, (feat_x, 0, FEAT_W, WIN_H))
    pygame.draw.line(surface, BORDER, (feat_x, 0), (feat_x, WIN_H), 2)

    y = 12
    # Title
    pygame.draw.rect(surface, DARK_GRAY, (feat_x + 6, y, FEAT_W - 12, 24), border_radius=4)
    surface.blit(font_md.render("📊 44-DIM INPUT FEATURES", True, PURPLE), (feat_x + 12, y + 3))
    y += 36

    # Column layout: 2 columns of 22
    ROWS_PER_COL = 22
    COL_W = (FEAT_W - 16) // 2
    ROW_H = 20

    for i in range(44):
        col_idx = i // ROWS_PER_COL
        row_idx = i % ROWS_PER_COL
        rx = feat_x + 8 + col_idx * COL_W
        ry = y + row_idx * ROW_H

        val = feat_vec[i]
        label = FEAT_LABELS[i] if i < len(FEAT_LABELS) else f"f{i:02d}"

        # Colour based on magnitude
        if val > 0.7:
            vc = GREEN
        elif val > 0.3:
            vc = YELLOW
        elif val < -0.3:
            vc = RED
        else:
            vc = GRAY

        surface.blit(font_sm.render(label, True, GRAY), (rx, ry))
        surface.blit(font_sm.render(f"{val:+.3f}", True, vc), (rx + COL_W - 55, ry))

    # ── Decode & Verify Section ──────────────────────────────────────────
    y = 12 + 36 + 22 * 20 + 10

    # Section Title
    pygame.draw.rect(surface, DARK_GRAY, (feat_x + 6, y, FEAT_W - 12, 24), border_radius=4)
    surface.blit(font_md.render("🔍 DECODED (0-1 VALUE VERIFY)", True, CYAN), (feat_x + 12, y + 3))
    y += 32

    # Decode Pac-Man position
    pac_x = feat_vec[0] * 160.0
    pac_y = feat_vec[1] * 160.0

    surface.blit(font_sm.render("Pacman Pos (f00,f01):", True, GRAY), (feat_x + 12, y))
    surface.blit(font_sm.render(f"({pac_x:.1f}, {pac_y:.1f})", True, YELLOW), (feat_x + 160, y))
    y += 24

    # Decode Ghost positions & distances
    ghost_colors = [YELLOW, CYAN, PINK, RED]
    ghost_names = ["G0 (Yellow)", "G1 (Cyan)", "G2 (Pink)", "G3 (Red)"]

    for i in range(4):
        f_dist = feat_vec[2 + i]
        # Calculate Dijkstra distance in pixel grid count (d = -20 * ln(feat))
        dist_px = -20.0 * np.log(f_dist) if f_dist > 1e-6 else float('inf')

        # Calculate relative dx, dy from relative directions
        dx_dir = feat_vec[6 + 2 * i]
        dy_dir = feat_vec[7 + 2 * i]

        dx = dx_dir * dist_px if dist_px != float('inf') else 0.0
        dy = dy_dir * dist_px if dist_px != float('inf') else 0.0

        gx = pac_x + dx
        gy = pac_y + dy

        lbl_col = ghost_colors[i]
        dist_str = f"{dist_px:.1f} px" if dist_px != float('inf') else "inf"
        pos_str = f"({gx:.1f}, {gy:.1f})" if dist_px != float('inf') else "N/A"

        surface.blit(font_sm.render(f"{ghost_names[i]} Pos:", True, GRAY), (feat_x + 12, y))
        surface.blit(font_sm.render(pos_str, True, lbl_col), (feat_x + 100, y))
        surface.blit(font_sm.render(f"Dist: {dist_str}", True, lbl_col), (feat_x + 200, y))
        y += 20

    # Fruit: read directly from RAM (obs[11]=fruit_x, obs[17]=fruit_y per AtariARI)
    fruit_exists = feat_vec[35] > 0.5
    f_fruit_dist = feat_vec[34]
    fruit_dist_px = -20.0 * np.log(f_fruit_dist) if (fruit_exists and f_fruit_dist > 1e-6) else float('inf')

    # Fruit position from features f36, f37 (added to vector) OR raw RAM
    raw_fx = int(obs[11])   # AtariARI: fruit_x = RAM[11]
    raw_fy = int(obs[17])   # AtariARI: fruit_y = RAM[17]
    feat_fx = feat_vec[36] * 160.0  # from f36
    feat_fy = feat_vec[37] * 160.0  # from f37

    fruit_pos_raw = f"RAM({raw_fx}, {raw_fy})" if fruit_exists else "N/A"
    fruit_pos_feat = f"f36/37({feat_fx:.1f}, {feat_fy:.1f})" if fruit_exists else "N/A"
    fruit_dist_str = f"{fruit_dist_px:.1f} px" if fruit_exists and fruit_dist_px != float('inf') else "N/A"

    surface.blit(font_sm.render("Fruit (RAM):", True, GRAY), (feat_x + 12, y))
    surface.blit(font_sm.render(fruit_pos_raw, True, ORANGE), (feat_x + 100, y))
    y += 18
    surface.blit(font_sm.render("Fruit (feat):", True, GRAY), (feat_x + 12, y))
    surface.blit(font_sm.render(fruit_pos_feat, True, ORANGE), (feat_x + 100, y))
    y += 18
    surface.blit(font_sm.render("Fruit Dist:", True, GRAY), (feat_x + 12, y))
    surface.blit(font_sm.render(fruit_dist_str, True, ORANGE), (feat_x + 100, y))

# ── Helpers ────────────────────────────────────────────────────────────────
def gp(gx, gy):
    return (int(gx * SCALE), int(gy * SCALE))

def draw_text_with_shadow(surface, font, text, pos, color):
    shadow = font.render(text, True, (0, 0, 0))
    txt = font.render(text, True, color)
    surface.blit(shadow, (pos[0] + 1, pos[1] + 1))
    surface.blit(txt, pos)

def patch_infinite_lives(env, obs):
    """Lock lives at 3 in RAM."""
    raw_level = int(obs[123]) >> 4
    val = (raw_level << 4) | 3
    env.unwrapped.ale.setRAM(123, val)
    obs[123] = val

def do_reset(env, graphs, level_override=None):
    """Reset env, optionally restore saved state, lock lives. Returns obs."""
    obs, _ = env.reset()
    if level_override is not None and load_state(env, level_override):
        obs = np.array(env.unwrapped.ale.getRAM(), dtype=np.uint8)
    else:
        if level_override is not None:
            # RAM fallback: force level
            env.unwrapped.ale.setRAM(123, (level_override << 4) | 3)
            obs[123] = (level_override << 4) | 3
    patch_infinite_lives(env, obs)
    return obs

def init_features_state(obs, graphs):
    raw_level = int(obs[123]) >> 4
    maze_id = get_maze_id(raw_level)
    graph = graphs[raw_level]
    
    remaining_pellets = set()
    remaining_energizers = set()
    visited_nodes = set()
    
    p, e = init_pellets_and_energizers(graph, maze_id)
    remaining_pellets.update(p)
    remaining_energizers.update(e)
    
    prev_ghosts_pos = [(int(obs[6+i]), int(obs[12+i])) for i in range(4)]
    feat_prev_p = None
    
    feat_vec, feat_prev_p = extract_strategic_features(
        obs, graph, feat_prev_p, remaining_pellets, remaining_energizers, visited_nodes, prev_ghosts_pos
    )
    return remaining_pellets, remaining_energizers, visited_nodes, prev_ghosts_pos, feat_prev_p, feat_vec

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    pygame.display.set_caption("🕹️  MsPacman — Level Recorder")
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    clock  = pygame.time.Clock()

    font_lg = pygame.font.SysFont("Arial", 26, bold=True)
    font_md = pygame.font.SysFont("Arial", 15, bold=True)
    font_sm = pygame.font.SysFont("Arial", 13)
    font_tiny = pygame.font.SysFont("Arial", 10, bold=True)

    graphs = load_graphs()

    env = gym.make("ALE/MsPacman-v5", obs_type="ram", render_mode="rgb_array",
                   frameskip=1, repeat_action_probability=0.0)

    level_override = None
    obs            = do_reset(env, graphs)
    frame          = env.render()

    prev_p         = None
    prev_lives     = 3
    current_level  = int(obs[123]) >> 4
    current_score  = 0.0
    episode        = 1
    steps          = 0
    held_action    = 0
    last_save_time = 0
    last_save_msg  = ""
    notif_text     = "Use ↑↓←→ to move  |  5/6/7/8 = load Level 0,2,4,6 | P = Pause"
    notif_timer    = 200
    notif_color    = CYAN
    game_over_freeze = 0
    paused         = False
    running        = True

    # Initialize strategic feature states
    remaining_pellets, remaining_energizers, visited_nodes, prev_ghosts_pos, feat_prev_p, feat_vec = init_features_state(obs, graphs)

    while running:
        # ── Events ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

                elif event.key == pygame.K_r:
                    obs = do_reset(env, graphs, level_override)
                    frame = env.render()
                    prev_p = None; prev_lives = 3
                    current_level = int(obs[123]) >> 4
                    current_score = 0.0; steps = 0; episode += 1
                    held_action = 0
                    notif_text = f"Episode {episode} — Level {current_level}"
                    notif_timer = 60; notif_color = GREEN
                    save_graphs(graphs)
                    last_save_msg = "✔ Saved"; last_save_time = time.time()
                    remaining_pellets, remaining_energizers, visited_nodes, prev_ghosts_pos, feat_prev_p, feat_vec = init_features_state(obs, graphs)

                elif event.key == pygame.K_p:
                    paused = not paused
                    notif_text = "⏸ PAUSED" if paused else "▶ RESUMED"
                    notif_timer = 60
                    notif_color = YELLOW

                elif event.key in KEY_LEVEL_SELECT:
                    level_override = KEY_LEVEL_SELECT[event.key]
                    obs = do_reset(env, graphs, level_override)
                    frame = env.render()
                    prev_p = None; prev_lives = 3
                    current_level = int(obs[123]) >> 4
                    current_score = 0.0; steps = 0; episode += 1
                    held_action = 0
                    has_state = os.path.exists(state_path(level_override))
                    notif_text  = f"{'✨ Loaded' if has_state else '⚠️ RAM'} Level {level_override}"
                    notif_timer = 90; notif_color = GREEN if has_state else ORANGE
                    remaining_pellets, remaining_energizers, visited_nodes, prev_ghosts_pos, feat_prev_p, feat_vec = init_features_state(obs, graphs)

                elif event.key in KEY_ACTION:
                    held_action = KEY_ACTION[event.key]

            elif event.type == pygame.KEYUP:
                if event.key in KEY_ACTION and KEY_ACTION[event.key] == held_action:
                    held_action = 0

        # ── Step ──────────────────────────────────────────────────────────
        if game_over_freeze > 0:
            game_over_freeze -= 1
        elif not paused:
            obs, reward, terminated, truncated, _ = env.step(held_action)
            frame = env.render()
            current_score += reward
            steps += 1

            px, py    = int(obs[10]), int(obs[16])
            raw_level = int(obs[123]) >> 4
            lives     = int(obs[123]) & 0x0F

            # Record nodes for CURRENT LEVEL (not maze_id)
            if lives >= prev_lives:
                update_graph(graphs, px, py, prev_p, raw_level)
            else:
                prev_p = None
                notif_text = "💀 Died!"; notif_timer = 60; notif_color = RED

            # Infinite lives
            patch_infinite_lives(env, obs)
            prev_p     = (px, py)
            prev_lives = 3

            # Level transition
            if raw_level != current_level:
                print(f"[Transition] Level {current_level} → {raw_level}")
                save_state(env, raw_level)          # save new level's start state
                save_graphs(graphs)
                last_save_msg = f"✔ Level {raw_level} state saved"
                last_save_time = time.time()
                if level_override is not None:
                    level_override = raw_level       # track new level
                notif_text  = f"🎉 Now Level {raw_level}! State saved."
                notif_timer = 180; notif_color = YELLOW
                current_level = raw_level
                prev_p = None
                
                # Reset features state on level transition
                visited_nodes.clear()
                remaining_pellets.clear()
                remaining_energizers.clear()
                maze_id = get_maze_id(raw_level)
                p, e = init_pellets_and_energizers(graphs[raw_level], maze_id)
                remaining_pellets.update(p)
                remaining_energizers.update(e)
                prev_ghosts_pos = [(int(obs[6+i]), int(obs[12+i])) for i in range(4)]
                feat_prev_p = None

            # Auto-save every 30 s
            if time.time() - last_save_time > 30:
                save_graphs(graphs)
                last_save_msg = "✔ Auto-saved"; last_save_time = time.time()

            # Extract features
            ghosts_pos = [(int(obs[6+i]), int(obs[12+i])) for i in range(4)]
            feat_vec, feat_prev_p = extract_strategic_features(
                obs, graphs[raw_level], feat_prev_p, remaining_pellets, remaining_energizers, visited_nodes, prev_ghosts_pos
            )
            prev_ghosts_pos = ghosts_pos

            if terminated or truncated:
                notif_text = f"GAME OVER  Score: {current_score:.0f}"
                notif_timer = 120; notif_color = RED
                game_over_freeze = 60
                save_graphs(graphs)
                last_save_msg = "✔ Saved"; last_save_time = time.time()
                obs = do_reset(env, graphs, level_override)
                frame = env.render()
                prev_p = None; prev_lives = 3
                current_level = int(obs[123]) >> 4
                current_score = 0.0; steps = 0; episode += 1
                remaining_pellets, remaining_energizers, visited_nodes, prev_ghosts_pos, feat_prev_p, feat_vec = init_features_state(obs, graphs)

        # ── Render ────────────────────────────────────────────────────────
        screen.fill(BG)
        if frame is not None:
            surf = pygame.surfarray.make_surface(np.transpose(frame, (1, 0, 2)))
            screen.blit(pygame.transform.scale(surf, (GAME_W * SCALE, GAME_H * SCALE)), (0, 0))

        # ── Draw Overlay Coordinates directly on game screen ──────────────
        raw_level = int(obs[123]) >> 4
        px, py = int(obs[10]), int(obs[16])
        aligned_px, aligned_py = align_coordinates_to_graph(graphs[raw_level], px, py)
        
        # Draw Pac-Man raw (white) and aligned (cyan) dots
        pygame.draw.circle(screen, WHITE, gp(px, py), 3)
        pygame.draw.circle(screen, CYAN, gp(aligned_px, aligned_py), 4, 1)
        draw_text_with_shadow(screen, font_tiny, f"P:{px},{py}", (gp(px, py)[0] + 6, gp(px, py)[1] - 12), WHITE)
        draw_text_with_shadow(screen, font_tiny, f"A:{aligned_px},{aligned_py}", (gp(px, py)[0] + 6, gp(px, py)[1] + 2), CYAN)
        
        # Draw Ghosts
        ghost_colors = [YELLOW, CYAN, PINK, RED]
        for i in range(4):
            g_x, g_y = int(obs[6+i]), int(obs[12+i])
            if g_x > 0 or g_y > 0:
                pygame.draw.circle(screen, ghost_colors[i], gp(g_x, g_y), 3)
                draw_text_with_shadow(screen, font_tiny, f"G{i}:{g_x},{g_y}", (gp(g_x, g_y)[0] + 6, gp(g_x, g_y)[1] - 5), ghost_colors[i])
                
        # Draw Fruit
        fr_x, fr_y = int(obs[11]), int(obs[17])
        if fr_x > 0 and fr_y > 0:
            pygame.draw.circle(screen, ORANGE, gp(fr_x, fr_y), 3)
            draw_text_with_shadow(screen, font_tiny, f"FR:{fr_x},{fr_y}", (gp(fr_x, fr_y)[0] + 6, gp(fr_x, fr_y)[1] - 5), ORANGE)

        if notif_timer > 0:
            draw_notification(screen, font_lg, notif_text, notif_color, min(255, notif_timer * 3))
            notif_timer -= 1

        raw_level = int(obs[123]) >> 4
        draw_hud(screen, font_lg, font_md, font_sm, {
            "score":     current_score,
            "lives":     int(obs[123]) & 0x0F,
            "level":     raw_level + 1,
            "raw_level": raw_level,
            "px": int(obs[10]), "py": int(obs[16]),
            "pellets":    len(remaining_pellets),
            "energizers": len(remaining_energizers),
            "episode":   episode, "steps": steps,
            "last_save": last_save_msg if (time.time() - last_save_time < 4) else "",
        }, graphs)

        draw_feat_hud(screen, font_md, font_sm, feat_vec, obs)

        pygame.display.flip()
        clock.tick(FPS)

    # ── Cleanup ───────────────────────────────────────────────────────────
    save_graphs(graphs)
    env.close(); pygame.quit()
    print("Saved and exited.")

if __name__ == "__main__":
    main()
