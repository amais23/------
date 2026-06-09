#!/usr/bin/env python3
"""
🕹️  MsPacman Human Play + Maze Recorder
----------------------------------------------
Play MsPacman yourself with keyboard controls.
All maze connectivity data is recorded automatically
and saved to complete_mazes.json.

Controls:
  ↑ ↓ ← →   Move Pac-Man
  Space       NOOP (pause action)
  R           Reset current episode
  Q / Esc     Quit and save

Press any arrow key to start!
"""

import os
import sys
import json
import pickle
import time
from collections import defaultdict

import ale_py
import gymnasium as gym
import numpy as np
import pygame

gym.register_envs(ale_py)

# ── Paths ──────────────────────────────────────────────────────────────────
JSON_PATH = os.path.join(os.path.dirname(__file__), "complete_mazes.json")

# ── Display ────────────────────────────────────────────────────────────────
GAME_W, GAME_H = 160, 210          # ALE native resolution
SCALE          = 4                  # pixel scale factor → 640×840
HUD_W          = 280               # right-side HUD width
WIN_W          = GAME_W * SCALE + HUD_W
WIN_H          = GAME_H * SCALE

FPS = 30                            # display refresh rate (game runs at ~60)

# ── Colors ─────────────────────────────────────────────────────────────────
BG          = (15,  15,  25)
HUD_BG      = (20,  20,  35)
BORDER      = (60,  60, 100)
WHITE       = (240, 240, 250)
YELLOW      = (255, 220,  50)
CYAN        = ( 80, 220, 220)
GREEN       = ( 60, 220, 100)
RED         = (220,  70,  70)
ORANGE      = (255, 160,  40)
GRAY        = (120, 120, 140)
DARK_GRAY   = ( 40,  40,  55)
PURPLE      = (160,  80, 220)
PINK        = (255, 120, 180)
TEAL        = ( 50, 180, 160)

# ── Key → Action mapping ───────────────────────────────────────────────────
KEY_ACTION = {
    pygame.K_UP:    1,   # UP
    pygame.K_RIGHT: 2,   # RIGHT
    pygame.K_LEFT:  3,   # LEFT
    pygame.K_DOWN:  4,   # DOWN
    pygame.K_w:     1,
    pygame.K_d:     2,
    pygame.K_a:     3,
    pygame.K_s:     4,
    pygame.K_SPACE: 0,   # NOOP
}

# ── Maze ID manual override keys ───────────────────────────────────────────
KEY_MAZE_OVERRIDE = {
    pygame.K_1: 1,
    pygame.K_2: 2,
    pygame.K_3: 3,
    pygame.K_4: 4,
}

# ── Level select keys ──────────────────────────────────────────────────────
KEY_LEVEL_SELECT = {
    pygame.K_5: 0,   # Level 0 (Maze 1)
    pygame.K_6: 2,   # Level 2 (Maze 2)
    pygame.K_7: 4,   # Level 4 (Maze 3)
    pygame.K_8: 6,   # Level 6 (Maze 4)
}

# ── Maze level mapping ─────────────────────────────────────────────────────
# NOTE: This mapping may need adjustment based on observed game behaviour.
# Override at runtime using keyboard 1/2/3/4 if auto-detection is wrong.
_MAZE_CYCLE_STEP = 2  # each maze spans 2 levels

def get_maze_id(level):
    """Map 0-indexed RAM level to maze ID 1-4 (2 levels per maze, cycles every 8)."""
    return (level // 2) % 4 + 1

def is_in_house(x, y):
    return (75 <= x <= 101) and (72 <= y <= 88)

# ── JSON I/O ───────────────────────────────────────────────────────────────
def load_graphs():
    maze_graphs = {i: defaultdict(set) for i in range(1, 5)}
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r") as f:
                data = json.load(f)
            for m_id in range(1, 5):
                key = f"maze_{m_id}"
                if key in data:
                    for k_str, neighbors in data[key].items():
                        kx, ky = map(int, k_str.split(","))
                        for nx, ny in neighbors:
                            maze_graphs[m_id][(kx, ky)].add((nx, ny))
            totals = {i: len(maze_graphs[i]) for i in range(1, 5)}
            print(f"[Load] Loaded: {totals}")
        except Exception as e:
            print(f"[Load] Error: {e}")
    return maze_graphs

def save_graphs(maze_graphs):
    output = {}
    for m_id, g in maze_graphs.items():
        output[f"maze_{m_id}"] = {
            f"{k[0]},{k[1]}": [list(v) for v in vs]
            for k, vs in g.items()
        }
    with open(JSON_PATH, "w") as f:
        json.dump(output, f, indent=2)
    totals = {i: len(maze_graphs[i]) for i in range(1, 5)}
    print(f"[Save] {totals}")

# ── Graph learning ─────────────────────────────────────────────────────────
def update_graph(maze_graphs, px, py, prev_p, current_maze_id):
    if prev_p is None:
        return
    ppx, ppy = prev_p
    if (ppx, ppy) == (px, py):
        return
    dist = abs(px - ppx) + abs(py - ppy)
    is_warp = (ppy == py) and ((ppx < 25 and px > 140) or (ppx > 140 and px < 25))
    if dist <= 15 or is_warp:
        graph = maze_graphs[current_maze_id]
        graph[(ppx, ppy)].add((px, py))
        graph[(px, py)].add((ppx, ppy))
        # Auto-connect warp tunnels
        for node in list(graph.keys()):
            if node[0] <= 20:
                for rx in [158, 157, 156]:
                    if (rx, node[1]) in graph:
                        graph[node].add((rx, node[1]))
                        graph[(rx, node[1])].add(node)

# ── HUD drawing ────────────────────────────────────────────────────────────
def draw_hud(surface, font_lg, font_md, font_sm, state):
    hud_x = GAME_W * SCALE
    # Background
    pygame.draw.rect(surface, HUD_BG, (hud_x, 0, HUD_W, WIN_H))
    pygame.draw.line(surface, BORDER, (hud_x, 0), (hud_x, WIN_H), 2)

    y = 16
    def row(label, value, color=WHITE, label_color=GRAY):
        nonlocal y
        lbl = font_sm.render(label, True, label_color)
        val = font_md.render(str(value), True, color)
        surface.blit(lbl, (hud_x + 14, y))
        surface.blit(val, (hud_x + 14, y + 16))
        y += 44

    def section(title, color=CYAN):
        nonlocal y
        pygame.draw.rect(surface, DARK_GRAY, (hud_x + 8, y, HUD_W - 16, 26), border_radius=4)
        t = font_md.render(title, True, color)
        surface.blit(t, (hud_x + 14, y + 4))
        y += 34

    def separator():
        nonlocal y
        pygame.draw.line(surface, BORDER, (hud_x + 8, y), (hud_x + HUD_W - 16, y))
        y += 10

    # Title
    title = font_lg.render("🗺  MAP RECORDER", True, YELLOW)
    surface.blit(title, (hud_x + 10, y))
    y += 36
    separator()

    # Game stats
    section("GAME STATUS", CYAN)
    lives_color = GREEN if state["lives"] >= 3 else (ORANGE if state["lives"] == 2 else RED)
    row("SCORE",  f"{state['score']:,}",  YELLOW)
    row("LIVES",  "♥ " * state["lives"],  lives_color)
    row("LEVEL",  f"{state['level']} (RAM={state['raw_level']})", PURPLE)
    # Maze ID: show override indicator
    maze_label = f"#{state['maze_id']}"
    maze_color = ORANGE if state['maze_overridden'] else PINK
    override_note = " [MANUAL]" if state['maze_overridden'] else " [AUTO]"
    row("MAZE",   maze_label + override_note, maze_color)
    separator()

    # Maze collection progress
    section("MAZE PROGRESS", GREEN)
    maze_colors = {1: CYAN, 2: PINK, 3: ORANGE, 4: PURPLE}
    for m_id in range(1, 5):
        n = state["maze_nodes"][m_id]
        bar_color = maze_colors[m_id]
        if n == 0:
            bar_color = DARK_GRAY
        max_nodes = 1800
        fill_ratio = min(n / max_nodes, 1.0)

        label = font_sm.render(f"Maze {m_id}", True, GRAY)
        count = font_sm.render(f"{n} nodes", True, bar_color)
        surface.blit(label, (hud_x + 14, y))
        surface.blit(count, (hud_x + 120, y))
        y += 18
        # Progress bar
        bar_bg   = pygame.Rect(hud_x + 14, y, HUD_W - 28, 10)
        bar_fill = pygame.Rect(hud_x + 14, y, int((HUD_W - 28) * fill_ratio), 10)
        pygame.draw.rect(surface, DARK_GRAY, bar_bg, border_radius=4)
        if n > 0:
            pygame.draw.rect(surface, bar_color, bar_fill, border_radius=4)
        y += 18
    separator()

    # Current position
    section("PACMAN INFO", ORANGE)
    row("POSITION", f"({state['px']}, {state['py']})", WHITE)
    row("EPISODE",  state["episode"], WHITE)
    row("STEPS",    state["steps"],   WHITE)
    separator()

    # Controls
    section("CONTROLS", TEAL)
    controls = [
        ("↑ ↓ ← →", "Move"),
        ("Space",    "NOOP"),
        ("1/2/3/4",  "Override Maze ID"),
        ("5/6/7/8",  "Select Level 0,2,4,6"),
        ("R",        "Reset episode"),
        ("Q / Esc",  "Quit & Save"),
    ]
    for key, action in controls:
        k = font_sm.render(key, True, YELLOW)
        a = font_sm.render(f"→ {action}", True, GRAY)
        surface.blit(k, (hud_x + 14, y))
        surface.blit(a, (hud_x + 90, y))
        y += 20
    y += 6

    # Save status
    save_txt = font_sm.render(state.get("last_save", ""), True, GREEN)
    surface.blit(save_txt, (hud_x + 14, y))

def draw_notification(surface, font_lg, text, color=YELLOW, alpha=255):
    """Centered overlay notification."""
    surf = font_lg.render(text, True, color)
    surf.set_alpha(alpha)
    rect = surf.get_rect(center=(GAME_W * SCALE // 2, WIN_H // 2))
    # Shadow
    shadow = font_lg.render(text, True, (0, 0, 0))
    shadow.set_alpha(alpha // 2)
    surface.blit(shadow, rect.move(2, 2))
    surface.blit(surf, rect)

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    pygame.display.set_caption("🕹️  MsPacman — Map Recorder")

    screen = pygame.display.set_mode((WIN_W, WIN_H))
    clock  = pygame.time.Clock()

    font_lg = pygame.font.SysFont("Arial", 28, bold=True)
    font_md = pygame.font.SysFont("Arial", 16, bold=True)
    font_sm = pygame.font.SysFont("Arial", 13)

    # Load maze data
    maze_graphs = load_graphs()

    # Create environment
    env = gym.make(
        "ALE/MsPacman-v5",
        obs_type="ram",
        render_mode="rgb_array",
        frameskip=1,          # no frame skip — human needs every frame
        repeat_action_probability=0.0,  # disable sticky actions for human play
    )

    obs, info = env.reset()
    # Patch RAM to lock lives at 3
    raw_level = int(obs[123]) >> 4
    env.unwrapped.ale.setRAM(123, (raw_level << 4) | 3)
    obs[123] = (raw_level << 4) | 3
    frame = env.render()

    prev_p          = None
    current_level   = raw_level
    prev_lives      = 3
    current_score   = 0
    episode         = 1
    steps           = 0
    held_action     = 0      # last key held
    last_save_time  = 0
    last_save_msg   = ""
    maze_override   = None   # None = auto, int 1-4 = manual
    level_override  = None   # None = auto, int 0-3 = manual level
    notif_text      = "Press any arrow key to start! | Keys 5-8 = load Level 0,2,4,6"
    notif_timer     = 180    # frames
    notif_color     = CYAN

    running          = True
    game_over_freeze = 0   # freeze frames on game over

    while running:
        # ── Event handling ────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_r:
                    # Reset episode
                    obs, info = env.reset()
                    
                    loaded_from_file = False
                    if level_override is not None:
                        maze_id = get_maze_id(level_override)
                        state_path = os.path.join(os.path.dirname(__file__), f"maze_{maze_id}_state.pkl")
                        if os.path.exists(state_path):
                            try:
                                with open(state_path, "rb") as sf:
                                    state_bytes = sf.read()
                                env.unwrapped.restore_state(state_bytes)
                                obs = np.array(env.unwrapped.ale.getRAM(), dtype=np.uint8)
                                loaded_from_file = True
                                print(f"[State Load] Reset using state file: {state_path}")
                            except Exception as le:
                                print(f"[State Load] Reset state restore failed: {le}")
                                
                    if not loaded_from_file:
                        # Patch RAM to lock lives at 3, using level_override if set
                        raw_level = level_override if level_override is not None else (int(obs[123]) >> 4)
                        env.unwrapped.ale.setRAM(123, (raw_level << 4) | 3)
                        obs[123] = (raw_level << 4) | 3
                        print(f"[Level Reset] Reset using RAM patch fallback")
                    
                    raw_level     = int(obs[123]) >> 4
                    frame         = env.render()
                    prev_p        = None
                    current_level = raw_level
                    prev_lives    = int(obs[123]) & 0x0F
                    current_score = 0
                    steps         = 0
                    episode      += 1
                    held_action   = 0
                    # Align maze override if level is overridden
                    if level_override is not None:
                        maze_override = get_maze_id(level_override)
                    else:
                        maze_override = None
                    notif_text    = f"Episode {episode} — Reset Level={raw_level+1}"
                    notif_timer   = 60
                    notif_color   = GREEN
                    save_graphs(maze_graphs)
                    last_save_msg  = "✔ Saved on reset"
                    last_save_time = time.time()

                elif event.key in KEY_LEVEL_SELECT:
                    level_override = KEY_LEVEL_SELECT[event.key]
                    maze_id = get_maze_id(level_override)
                    state_path = os.path.join(os.path.dirname(__file__), f"maze_{maze_id}_state.pkl")
                    
                    loaded_from_file = False
                    if os.path.exists(state_path):
                        try:
                            with open(state_path, "rb") as sf:
                                state_bytes = pickle.load(sf)
                            env.unwrapped.restore_state(state_bytes)
                            # Sync observation from restored RAM
                            obs = np.array(env.unwrapped.ale.getRAM(), dtype=np.uint8)
                            loaded_from_file = True
                            print(f"[State Load] Loaded level state from {state_path}")
                        except Exception as le:
                            print(f"[State Load] Failed to restore state: {le}")
                            
                    if not loaded_from_file:
                        obs, info = env.reset()
                        # Force the selected level and 3 lives
                        raw_level = level_override
                        env.unwrapped.ale.setRAM(123, (raw_level << 4) | 3)
                        obs[123] = (raw_level << 4) | 3
                        print(f"[Level Select] Fallback: Set level {level_override} in RAM")
                    
                    raw_level     = int(obs[123]) >> 4
                    frame         = env.render()
                    prev_p        = None
                    current_level = raw_level
                    prev_lives    = int(obs[123]) & 0x0F
                    current_score = 0
                    steps         = 0
                    episode      += 1
                    held_action   = 0
                    maze_override = get_maze_id(raw_level)
                    
                    notif_text  = f"✨ LOADED LEVEL {raw_level + 1} (Maze {maze_override})"
                    if not loaded_from_file:
                        notif_text = f"⚠️ FALLBACK LEVEL {raw_level + 1} (RAM Patch)"
                    notif_timer = 120
                    notif_color = GREEN if loaded_from_file else ORANGE
                    print(f"[Level Select] Active: level {raw_level} (maze {maze_override})")
                    save_graphs(maze_graphs)
                    last_save_msg  = f"✔ Saved on level jump"
                    last_save_time = time.time()

                elif event.key in KEY_MAZE_OVERRIDE:
                    maze_override = KEY_MAZE_OVERRIDE[event.key]
                    notif_text  = f"🗺  MAZE OVERRIDE → #{maze_override}"
                    notif_timer = 90
                    notif_color = ORANGE
                    print(f"[Override] Maze ID manually set to {maze_override} (raw level={current_level})")

                elif event.key in KEY_ACTION:
                    held_action = KEY_ACTION[event.key]

            elif event.type == pygame.KEYUP:
                if event.key in KEY_ACTION and KEY_ACTION[event.key] == held_action:
                    held_action = 0  # release: back to NOOP

        # ── Step ──────────────────────────────────────────────────────────
        if game_over_freeze > 0:
            game_over_freeze -= 1
        else:
            action = held_action  # 0 = NOOP if no key held

            obs, reward, terminated, truncated, info = env.step(action)
            frame = env.render()
            current_score += reward
            steps += 1

            px, py = int(obs[10]), int(obs[16])
            raw_level = int(obs[123]) >> 4
            level     = raw_level
            lives     = int(obs[123]) & 0x0F
            # Use manual override if set, otherwise auto-detect
            maze_id = maze_override if maze_override is not None else get_maze_id(level)

            # Graph update
            if lives >= prev_lives:  # only record if not dead
                update_graph(maze_graphs, px, py, prev_p, maze_id)
            else:
                prev_p = None  # death: reset position chain
                notif_text  = "💀 DIED! Keep going!"
                notif_timer = 90
                notif_color = RED

            # Patch RAM to prevent life loss (keep lives at 3)
            infinite_lives_val = (raw_level << 4) | 3
            env.unwrapped.ale.setRAM(123, infinite_lives_val)
            obs[123] = infinite_lives_val

            prev_p     = (px, py)
            prev_lives = 3

            # Level transition
            if level != current_level:
                # Save new level start state
                try:
                    state_bytes = env.unwrapped.clone_state()
                    maze_id = get_maze_id(level)
                    state_path = os.path.join(os.path.dirname(__file__), f"maze_{maze_id}_state.pkl")
                    with open(state_path, "wb") as sf:
                        pickle.dump(state_bytes, sf)
                    print(f"[State Save] Automatically saved state for Level {level+1} to {state_path}")
                except Exception as se:
                    print(f"[State Save] Error cloning state: {se}")

                auto_maze = get_maze_id(level)
                notif_text  = f"🎉 LEVEL UP! Level={level+1} → Auto-Maze={auto_maze} | Saved state!"
                notif_timer = 180
                notif_color = YELLOW
                current_level = level
                maze_override = None  # reset override on level change so user can re-specify
                print(f"[Level] Transition → level={level} (raw RAM={raw_level}) auto_maze={auto_maze}")
                save_graphs(maze_graphs)
                last_save_msg  = f"✔ Saved on level-up"
                last_save_time = time.time()

            # Auto-save every 30 seconds
            if time.time() - last_save_time > 30:
                save_graphs(maze_graphs)
                last_save_msg  = f"✔ Auto-saved"
                last_save_time = time.time()

            # Game over
            if terminated or truncated:
                notif_text  = f"GAME OVER  Score: {current_score:.0f}"
                notif_timer = 150
                notif_color = RED
                game_over_freeze = 90
                save_graphs(maze_graphs)
                last_save_msg  = "✔ Saved on game over"
                last_save_time = time.time()
                # Auto-reset
                obs, info = env.reset()
                
                loaded_from_file = False
                if level_override is not None:
                    maze_id = get_maze_id(level_override)
                    state_path = os.path.join(os.path.dirname(__file__), f"maze_{maze_id}_state.pkl")
                    if os.path.exists(state_path):
                        try:
                            with open(state_path, "rb") as sf:
                                state_bytes = sf.read()
                            env.unwrapped.restore_state(state_bytes)
                            obs = np.array(env.unwrapped.ale.getRAM(), dtype=np.uint8)
                            loaded_from_file = True
                            print(f"[State Load] Auto-reset using state file: {state_path}")
                        except Exception as le:
                            print(f"[State Load] Auto-reset state restore failed: {le}")
                            
                if not loaded_from_file:
                    raw_level = level_override if level_override is not None else (int(obs[123]) >> 4)
                    env.unwrapped.ale.setRAM(123, (raw_level << 4) | 3)
                    obs[123] = (raw_level << 4) | 3
                    print(f"[Level Auto-Reset] Fallback: Set level {raw_level} in RAM")
                
                raw_level = int(obs[123]) >> 4
                frame      = env.render()
                prev_p     = None
                current_level = raw_level
                prev_lives    = int(obs[123]) & 0x0F
                current_score = 0
                steps         = 0
                episode      += 1

        # ── Render ────────────────────────────────────────────────────────
        screen.fill(BG)

        # Game frame (scale up)
        if frame is not None:
            game_surf = pygame.surfarray.make_surface(
                np.transpose(frame, (1, 0, 2))
            )
            game_scaled = pygame.transform.scale(
                game_surf, (GAME_W * SCALE, GAME_H * SCALE)
            )
            screen.blit(game_scaled, (0, 0))

        # Notification overlay
        if notif_timer > 0:
            alpha = min(255, notif_timer * 3)
            draw_notification(screen, font_lg, notif_text, notif_color, alpha)
            notif_timer -= 1

        # HUD
        maze_nodes = {i: len(maze_graphs[i]) for i in range(1, 5)}
        fade_save  = last_save_msg if (time.time() - last_save_time < 4) else ""
        cur_level  = int(obs[123]) >> 4
        cur_maze   = maze_override if maze_override is not None else get_maze_id(cur_level)
        state = {
            "score":          current_score,
            "lives":          int(obs[123]) & 0x0F,
            "level":          cur_level + 1,       # show 1-indexed for readability
            "raw_level":      cur_level,
            "maze_id":        cur_maze,
            "maze_overridden": maze_override is not None,
            "maze_nodes":     maze_nodes,
            "px":             int(obs[10]),
            "py":             int(obs[16]),
            "episode":        episode,
            "steps":          steps,
            "last_save":      fade_save,
        }
        draw_hud(screen, font_lg, font_md, font_sm, state)

        pygame.display.flip()
        clock.tick(FPS)

    # ── Cleanup ───────────────────────────────────────────────────────────
    save_graphs(maze_graphs)
    env.close()
    pygame.quit()
    print("Saved and exited.")

if __name__ == "__main__":
    main()
