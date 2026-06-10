#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 MsPacman RL Training Visualizer
----------------------------------
Runs training with a GUI window displaying:
  1. The game frame (left panel) with overlaid debug info:
       - Cyan circle: Pac-Man's aligned graph node
       - Red circles: Ghost safety margin radius
       - Green ring: Closest remaining pellet
       - Yellow ring: Closest remaining energizer
  2. Right panel — Status & Action Masks
  3. Right panel — All 36 input feature values (labelled)

Layout:
  [   Game (160×210 @ 3x)  ] [ Status/Masks | 36 Features ]
  640 px                       520 px = 220 + 300

Press Q / ESC inside the window to stop training.
"""

import os
import sys
import numpy as np
import pygame
import ale_py
import gymnasium as gym

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from train import PacmanStrategicWrapper, EntropyDecayCallback
from model import (
    ALGORITHM, POLICY, POLICY_KWARGS, PPO_HYPERPARAMS,
    align_coordinates_to_graph, dijkstra_closest_target, dijkstra_from_pacman
)

# ── Layout constants ────────────────────────────────────────────────────────
GAME_W, GAME_H = 160, 210
SCALE          = 3                       # 3× → 480 × 630

PANEL_STATUS_W = 220                     # Status + Action Masks
PANEL_FEAT_W   = 300                     # 36-dim feature panel

WIN_W = GAME_W * SCALE + PANEL_STATUS_W + PANEL_FEAT_W
WIN_H = GAME_H * SCALE                  # 630 px

FPS = 30

# ── Overlay Calibration ──────────────────────────────────────────────────────
# 調整這些數值讓 overlay 圓圈與遊戲畫面對齊。
# 所有數值在 SCALE 套用「之後」計算（螢幕像素單位）。
#
#  OVERLAY_X_SCALE / OVERLAY_Y_SCALE
#    通常等於 SCALE（3）；若遊戲座標系與像素比例不一致時可單獨調整。
#  OVERLAY_X_OFFSET / OVERLAY_Y_OFFSET
#    向右(+) / 向下(+) 平移所有 overlay 標記。
#  GRID_STEP
#    網格線間距（遊戲像素）；按 G 鍵顯示/隱藏網格。
OVERLAY_X_SCALE  = SCALE   # ← 可調：X 軸縮放
OVERLAY_Y_SCALE  = SCALE   # ← 可調：Y 軸縮放
OVERLAY_X_OFFSET = 0       # ← 可調：X 平移（螢幕像素）
OVERLAY_Y_OFFSET = 0       # ← 可調：Y 平移（螢幕像素）
GRID_STEP        = 8        # ← 可調：網格間距（遊戲像素）
GRID_COLOR       = (45, 45, 70)   # 網格線顏色
GRID_LABEL_STEP  = 16             # 每隔多少 game-px 標一次座標

def gp(gx, gy):
    """遊戲像素座標 → 螢幕像素座標（含 offset / scale 校準）。"""
    return (
        int(gx * OVERLAY_X_SCALE) + OVERLAY_X_OFFSET,
        int(gy * OVERLAY_Y_SCALE) + OVERLAY_Y_OFFSET,
    )

# ── Colours ─────────────────────────────────────────────────────────────────
BG        = (12,  12,  22)
HUD_BG    = (20,  20,  35)
PANEL_BG  = (16,  16,  28)
BORDER    = (55,  55,  95)
WHITE     = (235, 235, 245)
YELLOW    = (255, 215,  45)
CYAN      = ( 70, 210, 210)
GREEN     = ( 50, 205,  90)
RED       = (215,  60,  60)
ORANGE    = (255, 150,  35)
GRAY      = (115, 115, 135)
DARK_GRAY = ( 35,  35,  50)
BLUE_C    = ( 90, 140, 255)
PURPLE    = (170,  90, 230)

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
    # 33: Active blue ghosts ratio
    "f33 #Blue/4",
    # 34: Fruit distance
    "f34 FruitDist↑",
    # 35: Fruit exists flag
    "f35 FruitExists",
    # 36-37: Fruit position normalized (obs[11]/160, obs[17]/160)
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


class GuiPacmanWrapper(PacmanStrategicWrapper):
    """PacmanStrategicWrapper with Pygame debug overlay."""

    def __init__(self, env):
        super().__init__(env)

        pygame.init()
        pygame.display.set_caption("🤖 MsPacman RL Training Visualizer")
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        self.clock  = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_md    = pygame.font.SysFont("Arial", 13, bold=True)
        self.font_sm    = pygame.font.SysFont("Arial", 11)
        self.font_xs    = pygame.font.SysFont("Arial", 10)

        # State
        self.current_score    = 0.0
        self.episode_steps    = 0
        self.episode_num      = 1
        self.last_macro_action = -1
        self.action_masks_cache = np.ones(6, dtype=bool)
        self.last_features    = np.zeros(44, dtype=np.float32)
        self.show_grid        = False   # toggle with G key

    # ── Gym interface ──────────────────────────────────────────────────────

    def reset(self, **kwargs):
        feats, info = super().reset(**kwargs)
        self.last_features      = feats
        self.current_score      = 0.0
        self.episode_steps      = 0
        self.action_masks_cache = self.action_masks()
        self._render()
        return feats, info

    def step(self, strategy_id):
        self.last_macro_action  = strategy_id
        self.action_masks_cache = self.action_masks()

        feats, reward, terminated, truncated, info = super().step(strategy_id)
        self.last_features  = feats
        self.current_score += reward
        self.episode_steps += 1

        self._render()
        self._handle_events()
        self.clock.tick(FPS)

        if terminated or truncated:
            self.episode_num += 1

        return feats, reward, terminated, truncated, info

    # ── Internal helpers ───────────────────────────────────────────────────

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    raise KeyboardInterrupt
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid

    def _render(self):
        self.screen.fill(BG)
        self._draw_game_panel()
        self._draw_status_panel()
        self._draw_features_panel()
        pygame.display.flip()

    # ── Game panel (left) ──────────────────────────────────────────────────

    def _draw_game_panel(self):
        frame = self.env.render()
        if frame is not None:
            surf = pygame.surfarray.make_surface(np.transpose(frame, (1, 0, 2)))
            self.screen.blit(
                pygame.transform.scale(surf, (GAME_W * SCALE, GAME_H * SCALE)),
                (0, 0)
            )

        # ── 座標校準網格（按 G 切換）──────────────────────────────────────
        if self.show_grid:
            for sgx in range(0, GAME_W + 1, GRID_STEP):
                sx, _ = gp(sgx, 0)
                if 0 <= sx <= GAME_W * SCALE:
                    pygame.draw.line(self.screen, GRID_COLOR, (sx, 0), (sx, GAME_H * SCALE))
            for sgy in range(0, GAME_H + 1, GRID_STEP):
                _, sy = gp(0, sgy)
                if 0 <= sy <= GAME_H * SCALE:
                    pygame.draw.line(self.screen, GRID_COLOR, (0, sy), (GAME_W * SCALE, sy))
            # 座標標籤（每 GRID_LABEL_STEP 個遊戲像素標一次）
            for sgx in range(0, GAME_W + 1, GRID_LABEL_STEP):
                for sgy in range(0, GAME_H + 1, GRID_LABEL_STEP):
                    sx, sy = gp(sgx, sgy)
                    if 0 <= sx < GAME_W * SCALE and 0 <= sy < GAME_H * SCALE:
                        lbl = self.font_xs.render(f"{sgx},{sgy}", True, (90, 90, 120))
                        self.screen.blit(lbl, (sx + 1, sy + 1))

        obs = self.last_raw_obs
        if obs is None:
            # Still draw divider
            pygame.draw.line(self.screen, BORDER,
                             (GAME_W * SCALE, 0), (GAME_W * SCALE, WIN_H), 2)
            return

        blue_timer = int(obs[116]) & 0x3F
        px = int(obs[10]); py = int(obs[16])
        aligned_px, aligned_py = align_coordinates_to_graph(self.graph, px, py)

        # Pac-Man 對齊節點（青色）
        pygame.draw.circle(self.screen, CYAN, gp(aligned_px, aligned_py), 6)
        # 原始 RAM 座標（白色小點）
        pygame.draw.circle(self.screen, WHITE, gp(px, py), 3)

        # Ghost 安全裕度圓
        for i in range(4):
            gx = int(obs[6 + i]); gy = int(obs[12 + i])
            in_h = (75 <= gx <= 101) and (72 <= gy <= 88)
            blue  = (blue_timer > 0) and not in_h
            col   = BLUE_C if blue else RED
            r     = max(2, int(self.safety_margin * OVERLAY_X_SCALE))
            pygame.draw.circle(self.screen, col, gp(gx, gy), r, 1)

        # 尋路目標
        pacman_paths = dijkstra_from_pacman(self.graph, (aligned_px, aligned_py))
        if self.remaining_pellets:
            best_p, _, _ = dijkstra_closest_target(
                pacman_paths, self.remaining_pellets, (aligned_px, aligned_py), self.graph)
            if best_p:
                pygame.draw.circle(self.screen, GREEN, gp(best_p[0], best_p[1]), 7, 2)
        if self.remaining_energizers:
            best_e, _, _ = dijkstra_closest_target(
                pacman_paths, self.remaining_energizers, (aligned_px, aligned_py), self.graph)
            if best_e:
                pygame.draw.circle(self.screen, YELLOW, gp(best_e[0], best_e[1]), 9, 2)

        # 分隔線
        pygame.draw.line(self.screen, BORDER,
                         (GAME_W * SCALE, 0), (GAME_W * SCALE, WIN_H), 2)

        # 提示（網格開啟時顯示）
        if self.show_grid:
            hint = self.font_xs.render(
                f"GRID ON  X_OFF={OVERLAY_X_OFFSET} Y_OFF={OVERLAY_Y_OFFSET}"
                f"  Xs={OVERLAY_X_SCALE} Ys={OVERLAY_Y_SCALE}  [G]=hide",
                True, YELLOW)
            self.screen.blit(hint, (4, GAME_H * SCALE - 14))

    # ── Status + Masks panel (centre) ─────────────────────────────────────

    def _draw_status_panel(self):
        sx = GAME_W * SCALE + 2
        pygame.draw.rect(self.screen, PANEL_BG, (sx, 0, PANEL_STATUS_W, WIN_H))

        obs = self.last_raw_obs
        raw_level = (int(obs[123]) >> 4) if obs is not None else 0
        lives     = (int(obs[123]) & 0x0F) if obs is not None else 0

        y = 8
        pw = PANEL_STATUS_W - 8   # usable width

        def title(text, col=CYAN):
            nonlocal y
            pygame.draw.rect(self.screen, DARK_GRAY, (sx + 4, y, pw, 18), border_radius=3)
            self.screen.blit(self.font_title.render(text, True, col), (sx + 8, y + 1))
            y += 22

        def row(label, val, vc=WHITE, lc=GRAY):
            nonlocal y
            self.screen.blit(self.font_xs.render(label, True, lc),      (sx + 6, y))
            self.screen.blit(self.font_sm.render(str(val), True, vc),   (sx + 6, y + 11))
            y += 24

        def sep():
            nonlocal y
            pygame.draw.line(self.screen, BORDER, (sx + 4, y), (sx + pw, y))
            y += 6

        # ── Title ──
        self.screen.blit(
            self.font_title.render("🤖 RL Visualizer", True, YELLOW),
            (sx + 6, y)
        )
        y += 20; sep()

        # ── Game status ──
        title("GAME STATUS")
        row("Episode",    self.episode_num, CYAN)
        row("Ep Steps / Total", f"{self.episode_steps} / {self.num_steps_total}", WHITE)
        row("Score",      f"{self.current_score:.1f}",
            GREEN if self.current_score >= 0 else RED)
        row("Lives | Level", f"♥ {lives}  |  L{raw_level + 1}", YELLOW)
        row("Safety Margin", f"{self.safety_margin:.2f} px", ORANGE)
        sep()

        # ── Pellet info ──
        title("PELLET TRACKING", GREEN)
        soft_count = len(self.remaining_pellets)
        ram_val    = int(obs[117]) if obs is not None else 0
        row("Soft Count (graph)", soft_count, GREEN)
        row("RAM obs[117] (real)", ram_val, CYAN)
        sep()

        # ── Action masks ──
        title("MACRO ACTIONS & MASKS")
        anames = ["0 Eat Pellet", "1 Eat Energy", "2 Escape",
                  "3 Chase Blue", "4 Lure/Wait", "5 Fruit"]
        for act_id, aname in enumerate(anames):
            safe     = self.action_masks_cache[act_id]
            selected = (act_id == self.last_macro_action)
            bg       = (50, 70, 50) if selected and safe else (70, 30, 30) if selected else PANEL_BG
            fc       = YELLOW if selected else (WHITE if safe else GRAY)
            badge_c  = GREEN if safe else RED
            badge    = "●" if safe else "✗"
            if selected:
                pygame.draw.rect(self.screen, bg, (sx + 4, y - 1, pw, 16), border_radius=2)
            self.screen.blit(self.font_xs.render(badge, True, badge_c), (sx + 6, y + 1))
            self.screen.blit(self.font_sm.render(aname, True, fc),      (sx + 18, y))
            y += 17

    # ── Features panel (right) ────────────────────────────────────────────

    def _draw_features_panel(self):
        fx_base = GAME_W * SCALE + PANEL_STATUS_W + 2
        pygame.draw.rect(self.screen, HUD_BG, (fx_base, 0, PANEL_FEAT_W, WIN_H))
        pygame.draw.line(self.screen, BORDER, (fx_base, 0), (fx_base, WIN_H), 2)

        y = 8
        # Title
        pygame.draw.rect(self.screen, DARK_GRAY, (fx_base + 4, y, PANEL_FEAT_W - 8, 18), border_radius=3)
        self.screen.blit(
            self.font_title.render("44-DIM INPUT FEATURES", True, PURPLE),
            (fx_base + 8, y + 1)
        )
        y += 24

        # Column layout: 2 columns of 22
        ROWS_PER_COL = 22
        COL_W = (PANEL_FEAT_W - 16) // 2
        ROW_H = 17

        feats = self.last_features
        for i in range(44):
            col_idx = i // ROWS_PER_COL
            row_idx = i % ROWS_PER_COL
            rx = fx_base + 8 + col_idx * COL_W
            ry = y + row_idx * ROW_H

            val = feats[i]
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

            self.screen.blit(
                self.font_xs.render(label, True, GRAY),
                (rx, ry)
            )
            self.screen.blit(
                self.font_sm.render(f"{val:+.3f}", True, vc),
                (rx + COL_W - 52, ry)
            )


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    print("Initializing training GUI...")
    from train import make_vec_env

    env = make_vec_env(
        "ALE/MsPacman-v5",
        n_envs=1,
        env_kwargs={"obs_type": "ram", "render_mode": "rgb_array"},
        wrapper_class=GuiPacmanWrapper,
    )

    model_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model.zip"
    )
    if os.path.exists(model_path):
        print(f"Resuming from {model_path}")
        model = ALGORITHM.load(model_path, env=env, device="cpu", **PPO_HYPERPARAMS)
    else:
        print("No model.zip found — starting fresh.")
        model = ALGORITHM(
            POLICY, env,
            policy_kwargs=POLICY_KWARGS or None,
            verbose=1,
            **PPO_HYPERPARAMS
        )

    print("Training started — press Q / ESC in the window to stop.")
    total_timesteps = 2_000_000
    cb = EntropyDecayCallback(
        initial_ent_coef=PPO_HYPERPARAMS.get("ent_coef", 0.015),
        total_timesteps=total_timesteps,
    )
    try:
        model.learn(total_timesteps=total_timesteps, callback=cb)
        print("Training completed. Saving model...")
        from model import SAVE_PATH
        model.save(SAVE_PATH)
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        env.close()
        pygame.quit()
        print("Exited.")


if __name__ == "__main__":
    main()
