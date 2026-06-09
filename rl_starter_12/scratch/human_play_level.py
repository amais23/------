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

gym.register_envs(ale_py)

SCRATCH    = os.path.dirname(os.path.abspath(__file__))
JSON_PATH  = os.path.join(SCRATCH, "data", "complete_levels.json")

# ── Display ────────────────────────────────────────────────────────────────
GAME_W, GAME_H = 160, 210
SCALE          = 4
HUD_W          = 300
WIN_W          = GAME_W * SCALE + HUD_W
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

# ── Helpers ────────────────────────────────────────────────────────────────
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

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    pygame.display.set_caption("🕹️  MsPacman — Level Recorder")
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    clock  = pygame.time.Clock()

    font_lg = pygame.font.SysFont("Arial", 26, bold=True)
    font_md = pygame.font.SysFont("Arial", 15, bold=True)
    font_sm = pygame.font.SysFont("Arial", 13)

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
    notif_text     = "Use ↑↓←→ to move  |  5/6/7/8 = load Level 0,2,4,6"
    notif_timer    = 200
    notif_color    = CYAN
    game_over_freeze = 0
    running        = True

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

                elif event.key in KEY_ACTION:
                    held_action = KEY_ACTION[event.key]

            elif event.type == pygame.KEYUP:
                if event.key in KEY_ACTION and KEY_ACTION[event.key] == held_action:
                    held_action = 0

        # ── Step ──────────────────────────────────────────────────────────
        if game_over_freeze > 0:
            game_over_freeze -= 1
        else:
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

            # Auto-save every 30 s
            if time.time() - last_save_time > 30:
                save_graphs(graphs)
                last_save_msg = "✔ Auto-saved"; last_save_time = time.time()

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

        # ── Render ────────────────────────────────────────────────────────
        screen.fill(BG)
        if frame is not None:
            surf = pygame.surfarray.make_surface(np.transpose(frame, (1, 0, 2)))
            screen.blit(pygame.transform.scale(surf, (GAME_W * SCALE, GAME_H * SCALE)), (0, 0))

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
            "episode":   episode, "steps": steps,
            "last_save": last_save_msg if (time.time() - last_save_time < 4) else "",
        }, graphs)

        pygame.display.flip()
        clock.tick(FPS)

    # ── Cleanup ───────────────────────────────────────────────────────────
    save_graphs(graphs)
    env.close(); pygame.quit()
    print("Saved and exited.")

if __name__ == "__main__":
    main()
