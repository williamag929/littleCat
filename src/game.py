"""
Little Cat Pet Game - Main Game Loop and UI
A learning AI cat pet that grows and learns from human interactions.
"""

import pygame
import sys
import os
import json
import random
import math
from cat_brain import CatBrain
from ui_agent import SeniorUIAgent
import cat_voice
import desktop
from desktop_life import DesktopLife
from autonomy import REASONS as _REASONS
import time
from datetime import datetime
from typing import Dict, Optional, Tuple, List

# Load environment variables (.env file)
try:
    from dotenv import load_dotenv
    if getattr(sys, "frozen", False):  # .exe: read the .env sitting next to it
        load_dotenv(os.path.join(os.path.dirname(sys.executable), ".env"))
    else:
        load_dotenv()
except ImportError:
    pass  # dotenv optional, will try without it

# Chat agent (LARY)
try:
    from chat_agent import create_chat_agent
except ImportError:
    create_chat_agent = None

# Initialize Pygame
pygame.init()

# Game constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 30
GAME_SPEED = 0.0025  # In-game hours per frame (overridden by config.py)
SPEECH_DURATION = 3.5
SPEECH_AMBIENT_COOLDOWN = 25
SPEECH_NEED_COOLDOWN = 60
HOVER_CARD_DELAY = 0.35
DESKTOP_LIFE = True
DESKTOP_SETTINGS = {}
MULTI_MONITOR = True

# Optional behavior settings (can be overridden in config.py)
try:
    import config as cfg
    GAME_SPEED = getattr(cfg, "GAME_SPEED", GAME_SPEED)
    SPEECH_DURATION = getattr(cfg, "SPEECH_DURATION", SPEECH_DURATION)
    SPEECH_AMBIENT_COOLDOWN = getattr(cfg, "SPEECH_AMBIENT_COOLDOWN", SPEECH_AMBIENT_COOLDOWN)
    SPEECH_NEED_COOLDOWN = getattr(cfg, "SPEECH_NEED_COOLDOWN", SPEECH_NEED_COOLDOWN)
    HOVER_CARD_DELAY = getattr(cfg, "HOVER_CARD_DELAY", HOVER_CARD_DELAY)
    DESKTOP_LIFE = getattr(cfg, "DESKTOP_LIFE", DESKTOP_LIFE)
    DESKTOP_SETTINGS = {
        "perch": getattr(cfg, "PERCH_ON_WINDOWS", True),
        "chase": getattr(cfg, "CHASE_CURSOR", True),
        "throw": getattr(cfg, "THROW_PHYSICS", True),
        "gifts": getattr(cfg, "GIFTS", True),
        "gifts_per_day": getattr(cfg, "GIFTS_PER_DAY", 2),
    }
    MULTI_MONITOR = getattr(cfg, "MULTI_MONITOR", MULTI_MONITOR)
    ADULT_AGE_DAYS = getattr(cfg, "ADULT_AGE_DAYS", 199)
    BUSY_THRESHOLD_SECONDS = getattr(cfg, "BUSY_THRESHOLD_SECONDS", 20)
    ADULT_SLEEP_MULTIPLIER = getattr(cfg, "ADULT_SLEEP_MULTIPLIER", 2.5)
    ADULT_REST_MULTIPLIER = getattr(cfg, "ADULT_REST_MULTIPLIER", 1.8)
    ADULT_FIXED_SPOT = getattr(cfg, "ADULT_FIXED_SPOT", True)
    FIXED_SPOT_MARGIN_X = getattr(cfg, "FIXED_SPOT_MARGIN_X", 140)
    FIXED_SPOT_MARGIN_Y = getattr(cfg, "FIXED_SPOT_MARGIN_Y", 160)
    YOUNG_FOLLOW_CURSOR = getattr(cfg, "YOUNG_FOLLOW_CURSOR", True)
    YOUNG_PLAY_DISTANCE = getattr(cfg, "YOUNG_PLAY_DISTANCE", 45)
    YOUNG_PLAY_COOLDOWN = getattr(cfg, "YOUNG_PLAY_COOLDOWN", 6.0)
    # Chat agent settings
    CHAT_ENABLED = getattr(cfg, "CHAT_ENABLED", True)
    CHAT_TOGGLE_KEY = getattr(cfg, "CHAT_TOGGLE_KEY", "?")
    CHAT_MODEL = getattr(cfg, "CHAT_MODEL", "gpt-4-vision-preview")
    CHAT_MAX_TOKENS = getattr(cfg, "CHAT_MAX_TOKENS", 500)
    CHAT_HISTORY_LENGTH = getattr(cfg, "CHAT_HISTORY_LENGTH", 10)
    CHAT_API_TIMEOUT = getattr(cfg, "CHAT_API_TIMEOUT", 5.0)
except Exception:
    ADULT_AGE_DAYS = 199
    BUSY_THRESHOLD_SECONDS = 20
    ADULT_SLEEP_MULTIPLIER = 2.5
    ADULT_REST_MULTIPLIER = 1.8
    ADULT_FIXED_SPOT = True
    FIXED_SPOT_MARGIN_X = 140
    FIXED_SPOT_MARGIN_Y = 160
    YOUNG_FOLLOW_CURSOR = True
    YOUNG_PLAY_DISTANCE = 45
    YOUNG_PLAY_COOLDOWN = 6.0
    CHAT_ENABLED = True
    CHAT_TOGGLE_KEY = "?"
    CHAT_MODEL = "gpt-4-vision-preview"
    CHAT_MAX_TOKENS = 500
    CHAT_HISTORY_LENGTH = 10
    CHAT_API_TIMEOUT = 5.0

# Pixel-art sprite settings (90s style)
USE_PIXEL_SPRITES = True
SPRITE_SIZE = 32
SPRITE_SCALE = 3

# Desktop overlay mode
DESKTOP_OVERLAY = True
OVERLAY_ALWAYS_ON_TOP = True
SHOW_UI = False if DESKTOP_OVERLAY else True
ALLOW_DRAG = True
CLICK_TO_PET = True
CLICK_TO_PLAY = False
TOGGLE_UI_KEY = pygame.K_u
TOGGLE_CLICK_THROUGH_KEY = pygame.K_c
CLICK_THROUGH = False
TRANSPARENT_BACKGROUND = True  # Windows overlay transparency (color key)
TRANSPARENT_COLOR = (255, 0, 255)

# Profiles and exports
if getattr(sys, "frozen", False):
    # Packaged .exe (PyInstaller): keep saves next to the executable, not in the temp unpack dir
    DATA_DIR = os.path.join(os.path.dirname(sys.executable), 'LittleCat-data')
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CATS_DIR = os.path.join(DATA_DIR, 'cats')
EXPORT_DIR = os.path.join(DATA_DIR, 'exports')
PROFILES_INDEX = os.path.join(DATA_DIR, 'profiles.json')

# Context menu
CONTEXT_MENU_WIDTH = 220
RADIAL_MENU_RADIUS = 110
RADIAL_ITEM_RADIUS = 22
RADIAL_HOVER_BUMP = 6

# Sound settings (optional)
SOUND_ENABLED = True
AMBIENT_SOUND_PATH = os.path.join(DATA_DIR, 'sounds', 'ambient.wav')
SOUND_FX_PATHS = {
    "play": os.path.join(DATA_DIR, 'sounds', 'play.wav'),
    "eat": os.path.join(DATA_DIR, 'sounds', 'eat.wav'),
    "sleep": os.path.join(DATA_DIR, 'sounds', 'sleep.wav'),
    "purr": os.path.join(DATA_DIR, 'sounds', 'purr.wav'),
    "groom": os.path.join(DATA_DIR, 'sounds', 'groom.wav'),
    "talk": os.path.join(DATA_DIR, 'sounds', 'talk.wav'),
    "train": os.path.join(DATA_DIR, 'sounds', 'train.wav'),
    "jump": os.path.join(DATA_DIR, 'sounds', 'jump.wav'),
    "hunt": os.path.join(DATA_DIR, 'sounds', 'hunt.wav'),
}
MUTE_KEY = pygame.K_m
SWITCH_CAT_KEY = pygame.K_TAB

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)
BLUE = (100, 149, 237)
GREEN = (144, 238, 144)
RED = (220, 50, 50)


class GameDisplay:
    """Handles game UI and rendering."""
    
    def __init__(self):
        # Window sizing (fullscreen desktop overlay or fixed window)
        self.play_areas = []  # per-monitor walk areas in overlay coords (multi-monitor)
        if DESKTOP_OVERLAY:
            info = pygame.display.Info()
            self.window_width = info.current_w
            self.window_height = info.current_h
            flags = pygame.NOFRAME
            vs = desktop.virtual_screen() if MULTI_MONITOR else None
            if vs and (vs[2] - vs[0], vs[3] - vs[1]) != (self.window_width, self.window_height):
                # Span every monitor: one borderless overlay over the whole virtual screen
                os.environ["SDL_VIDEO_WINDOW_POS"] = f"{vs[0]},{vs[1]}"
                self.window_width, self.window_height = vs[2] - vs[0], vs[3] - vs[1]
                for m in desktop.monitors():
                    l, t, r, b = m["work"]
                    self.play_areas.append((l - vs[0] + 150, t - vs[1] + 250, r - vs[0] - 150, b - vs[1] - 150))
                self.play_areas = [a for a in self.play_areas if a[2] > a[0] and a[3] > a[1]]
        else:
            self.window_width = WINDOW_WIDTH
            self.window_height = WINDOW_HEIGHT
            flags = 0

        self.screen = pygame.display.set_mode((self.window_width, self.window_height), flags)
        pygame.display.set_caption("Little Cat - AI Pet Learning Game")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 20)
        self.font_tiny = pygame.font.Font(None, 14)
        # Emoji-capable font for the cat's speech (default font draws emoji as boxes)
        emoji_path = pygame.font.match_font("segoeuiemoji") or pygame.font.match_font("notocoloremoji")
        self.font_speech = pygame.font.Font(emoji_path, 17) if emoji_path else self.font_small
        self.font_speech_small = pygame.font.Font(emoji_path, 14) if emoji_path else self.font_tiny
        self.speech_cache = {}
        self.label_cache = {}
        self.instruction_surfaces = None  # Cache for static instruction text
        
        # Cat visual position and movement
        self.cat_x = self.window_width // 2
        self.cat_y = self.window_height // 2
        self.target_x = self.cat_x
        self.target_y = self.cat_y
        self.cat_speed = 2
        
        # Animation system
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.15
        self.current_pose = "idle"
        self.facing_right = True
        
        # Movement bounds (play area)
        self.min_x = 150
        self.max_x = self.window_width - 150
        self.min_y = 250
        self.max_y = self.window_height - 200

        # Pixel-art sprites
        self.use_pixel_sprites = USE_PIXEL_SPRITES
        self.sprite_scale = SPRITE_SCALE
        self.sprites = {}
        if self.use_pixel_sprites:
            self.init_pixel_sprites()
        self.init_item_sprites()

        # Apply overlay styles (Windows only, optional)
        self.apply_overlay_styles(CLICK_THROUGH)

    def apply_overlay_styles(self, click_through=False):
        """Apply overlay window styles safely (Windows only)."""
        if not DESKTOP_OVERLAY:
            return
        if OVERLAY_ALWAYS_ON_TOP:
            self.set_always_on_top()
        if TRANSPARENT_BACKGROUND:
            self.set_transparent_background(TRANSPARENT_COLOR)
        self.set_click_through(click_through)

    def is_point_on_cat(self, x, y):
        """Check if a point is over the cat sprite/body."""
        size = SPRITE_SIZE * self.sprite_scale if self.use_pixel_sprites else 80
        left = self.cat_x - size / 2
        top = self.cat_y - size / 2
        return left <= x <= left + size and top <= y <= top + size

    def set_always_on_top(self):
        """Try to make the overlay window always on top (Windows)."""
        try:
            import win32gui
            import win32con
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOPMOST,
                    0,
                    0,
                    0,
                    0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
                )
        except Exception:
            pass

    def set_click_through(self, enabled):
        """Enable/disable click-through (Windows only)."""
        try:
            import ctypes
            hwnd = pygame.display.get_wm_info().get("window")
            if not hwnd:
                return

            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020

            user32 = ctypes.windll.user32
            current = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if enabled:
                new_style = current | WS_EX_LAYERED | WS_EX_TRANSPARENT
            else:
                new_style = current & ~WS_EX_TRANSPARENT
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

            if TRANSPARENT_BACKGROUND:
                self.set_transparent_background(TRANSPARENT_COLOR)
        except Exception:
            pass

    def set_transparent_background(self, color_key):
        """Make a color key transparent (Windows only)."""
        try:
            import ctypes
            hwnd = pygame.display.get_wm_info().get("window")
            if not hwnd:
                return

            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            LWA_COLORKEY = 0x00000001

            user32 = ctypes.windll.user32
            current = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, current | WS_EX_LAYERED)

            r, g, b = color_key
            colorref = r | (g << 8) | (b << 16)
            user32.SetLayeredWindowAttributes(hwnd, colorref, 0, LWA_COLORKEY)
        except Exception:
            pass
        
    def draw_cat(self, action, mood, hunger, jump_progress=None):
        """Draw the cat character with animations based on action and mood."""
        # Update pose based on action
        self.update_pose(action)

        jump_offset = 0
        if action == "jump" and jump_progress is not None:
            jump_offset = self.get_jump_offset(jump_progress)

        # Pixel-art sprite render (90s style)
        if self.use_pixel_sprites:
            self.draw_sprite_pose(hunger, y_offset=jump_offset)
            return  # the pose shows the action; words live in the speech bubble
        
        # Draw based on current pose
        if action == "jump" and jump_progress is not None:
            self.draw_jump_cat(mood, hunger, jump_progress)
        elif self.current_pose == "sleep":
            self.draw_sleeping_cat(mood, hunger)
        elif self.current_pose == "eat":
            self.draw_eating_cat(mood, hunger)
        elif self.current_pose == "play":
            self.draw_playing_cat(mood, hunger)
        elif self.current_pose == "sit":
            self.draw_sitting_cat(mood, hunger)
        elif self.current_pose == "walk":
            self.draw_walking_cat(mood, hunger)
        else:  # idle
            self.draw_idle_cat(mood, hunger)

    # Pose -> frame sequence (frames repeat to control rhythm: blinks are rare, tails sway slowly)
    SPRITE_SEQUENCES = {
        "idle": [0, 0, 1, 1, 0, 0, 2, 2, 0, 0, 1, 1, 0, 3],   # tail sway + occasional blink
        "walk": [0, 1, 2, 3],
        "sit": [0, 0, 1, 1],                                   # happy eyes ^^, tail flick
        "sleep": [0, 0, 1, 1],                                 # slow breathing + zZ
        "eat": [0, 1],
        "play": [0, 1, 2, 1],                                  # crouch -> pounce
        "groom": [0, 1],
    }

    def init_pixel_sprites(self):
        """Build pixel-art sprites (right-facing + mirrored) once at startup."""
        counts = {"idle": 4, "walk": 4, "sit": 2, "sleep": 2, "eat": 2, "play": 3, "groom": 2}
        size = SPRITE_SIZE * self.sprite_scale
        self.scaled_sprites, self.scaled_sprites_left = {}, {}
        for pose, n in counts.items():
            frames = [pygame.transform.scale(self.make_cat_sprite(pose, f), (size, size)) for f in range(n)]
            self.scaled_sprites[pose] = frames
            self.scaled_sprites_left[pose] = [pygame.transform.flip(f, True, False) for f in frames]

    def make_cat_sprite(self, pose, frame):
        """Draw one 32x32 pixel-art frame of a ginger tabby, then auto-outline it."""
        S = SPRITE_SIZE
        surf = pygame.Surface((S, S), pygame.SRCALPHA)
        OUT, FUR, DARK = (74, 44, 33), (247, 160, 72), (214, 112, 44)
        CREAM, PINK, EYE, SHINE = (255, 228, 190), (244, 150, 160), (45, 30, 30), (255, 255, 255)

        def px(x, y, c):
            if 0 <= x < S and 0 <= y < S:
                surf.set_at((int(x), int(y)), c)

        def ell(x, y, w, h, c):
            pygame.draw.ellipse(surf, c, (x, y, w, h))

        def rect(x, y, w, h, c):
            pygame.draw.rect(surf, c, (x, y, w, h))

        def tail(points, c=FUR):
            for (x, y) in points:
                pygame.draw.circle(surf, c, (x, y), 1)
                rect(x - 1, y - 1, 2, 2, c)

        def eyes(lx, rx, y, mode):
            for ex in (lx, rx):
                if mode == "open":
                    rect(ex, y, 2, 2, EYE)
                    px(ex, y, SHINE)
                elif mode == "happy":       # ^ ^
                    px(ex, y + 1, EYE); px(ex + 1, y, EYE); px(ex + 2, y + 1, EYE)
                else:                        # closed / blink
                    rect(ex, y + 1, 2, 1, EYE)

        if pose in ("idle", "sit", "eat", "groom"):
            # ---------- front-facing sitting cat ----------
            dip = 3 if pose == "eat" else 0
            sway = [0, 1, 0, -1][frame % 4] if pose == "idle" else (frame % 2)
            if pose == "sit":   # tail wrapped around the paws
                tail([(22, 29), (24, 28), (25, 26 - sway)])
            else:               # tail up, swaying
                tail([(22, 27), (24, 25), (25, 22), (25 + sway, 19), (24 + sway, 17)])
            ell(9, 15, 14, 15, FUR)                     # body
            ell(12, 18, 8, 10, CREAM)                   # chest
            rect(11, 27, 4, 3, CREAM); rect(17, 27, 4, 3, CREAM)  # front paws
            hx, hy = 8, 5 + dip
            if pose == "groom" and frame % 2:           # licking a raised paw
                rect(19, 16, 4, 5, CREAM)
            ear_l = [(hx + 1, hy + 5), (hx + 2, hy - 3), (hx + 7, hy + 1)]
            ear_r = [(hx + 15, hy + 5), (hx + 14, hy - 3), (hx + 9, hy + 1)]
            pygame.draw.polygon(surf, FUR, ear_l); pygame.draw.polygon(surf, FUR, ear_r)
            px(hx + 3, hy, PINK); px(hx + 3, hy + 1, PINK); px(hx + 13, hy, PINK); px(hx + 13, hy + 1, PINK)
            ell(hx, hy, 16, 13, FUR)                    # head
            ell(hx + 4, hy + 7, 8, 5, CREAM)            # muzzle
            for sx in (hx + 6, hx + 8, hx + 10):        # forehead stripes
                rect(sx, hy + 1, 1, 2, DARK)
            rect(hx, hy + 6, 2, 1, DARK); rect(hx + 14, hy + 6, 2, 1, DARK)  # cheek stripes
            if pose == "eat":
                mode = "closed"
            elif pose in ("sit", "groom"):
                mode = "happy"
            else:
                mode = "closed" if frame == 3 else "open"
            eyes(hx + 4, hx + 10, hy + 5, mode)
            MOUTH = (170, 95, 80)
            px(hx + 7, hy + 7, PINK); px(hx + 8, hy + 7, PINK)      # nose
            px(hx + 7, hy + 8, MOUTH); px(hx + 8, hy + 8, MOUTH)    # soft little "w" mouth
            px(hx + 6, hy + 9, MOUTH); px(hx + 9, hy + 9, MOUTH)
            if pose == "eat" and frame % 2 == 0:
                px(hx + 7, hy + 9, PINK); px(hx + 8, hy + 9, PINK)    # chewing tongue
        elif pose == "sleep":
            # ---------- curled-up loaf ----------
            breathe = frame % 2
            ell(6, 17 - breathe, 21, 12 + breathe, FUR)          # body
            for sx in (14, 18, 22):
                rect(sx, 18 - breathe, 1, 3, DARK)                 # back stripes
            tail([(25, 27), (21, 29), (16, 29), (11, 29)])         # tail wrapped in front
            pygame.draw.polygon(surf, FUR, [(5, 17), (6, 11), (10, 15)])
            pygame.draw.polygon(surf, FUR, [(13, 15), (15, 11), (16, 17)])
            px(7, 14, PINK); px(14, 14, PINK)
            ell(3, 14, 14, 11, FUR)                                # head resting on paws
            ell(6, 20, 8, 4, CREAM)
            eyes(6, 11, 17, "closed")
            px(9, 20, PINK)
        else:
            # ---------- side view (walk / play), facing right ----------
            ground = 29
            if pose == "walk":
                bob = frame % 2
                # (x, lift): diagonal leg pairs alternate
                legs = [(8, 0), (12, 2), (19, 2), (23, 0)] if frame in (0, 1) else [(8, 2), (12, 0), (19, 0), (23, 2)]
                body_y, head_y, tail_pts = 14 + bob, 7 + bob, [(6, 17), (4, 14), (3, 11), (4, 8)]
                paws_up = False
            else:  # play: crouch (0), mid (1), pounce with front paws up (2)
                lift = [0, 2, 5][frame % 3]
                body_y, head_y = 16 - lift, 9 - lift
                paws_up = frame % 3 == 2
                legs = [(8, 0), (12, 0)] + ([] if paws_up else [(19, 0), (23, 0)])
                tail_pts = [(6, 18), (4, 15), (3, 11), (5, 8)] if frame % 3 else [(6, 18), (3, 18), (1, 15)]
            tail(tail_pts)
            for (lx, lift_px) in legs:
                top = body_y + 7
                bottom = ground - lift_px
                rect(lx, top, 3, max(2, bottom - top), FUR)
                rect(lx, bottom - 2, 3, 2, CREAM)                # paw
            if paws_up:                                          # front paws reaching forward
                rect(23, body_y + 2, 6, 3, FUR); rect(27, body_y + 2, 2, 3, CREAM)
                rect(22, body_y + 6, 6, 3, FUR); rect(26, body_y + 6, 2, 3, CREAM)
            ell(5, body_y, 21, 11, FUR)                      # body
            ell(9, body_y + 6, 13, 5, CREAM)                 # belly
            for sx in (10, 13, 16):
                rect(sx, body_y + 1, 1, 3, DARK)
            hx, hy = 18, head_y
            pygame.draw.polygon(surf, FUR, [(hx + 1, hy + 4), (hx + 2, hy - 3), (hx + 6, hy + 1)])
            pygame.draw.polygon(surf, FUR, [(hx + 7, hy + 1), (hx + 10, hy - 3), (hx + 11, hy + 4)])
            px(hx + 3, hy, PINK); px(hx + 9, hy, PINK)
            ell(hx, hy, 13, 11, FUR)                         # head
            ell(hx + 7, hy + 5, 6, 4, CREAM)                 # muzzle
            rect(hx + 4, hy + 1, 1, 2, DARK); rect(hx + 6, hy + 1, 1, 2, DARK)
            eyes(hx + 8, hx + 8, hy + 4, "open")
            px(hx + 12, hy + 6, PINK)                        # nose

        # Auto-outline: every empty pixel touching fur becomes a dark outline pixel
        filled = {(x, y) for x in range(S) for y in range(S) if surf.get_at((x, y)).a > 0}
        for (x, y) in list(filled):
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < S and 0 <= ny < S and (nx, ny) not in filled:
                    surf.set_at((nx, ny), OUT)

        if pose == "sleep":  # floating zZ (after outline so letters stay thin)
            z_y = 6 - frame * 2
            for (zx, zy, n) in ((24, z_y + 4, 3), (27, z_y, 4)):
                rect(zx, zy, n, 1, (120, 130, 200)); rect(zx, zy + n - 1, n, 1, (120, 130, 200))
                for i in range(n):
                    px(zx + n - 1 - i, zy + i, (120, 130, 200))
        return surf

    def draw_sprite_pose(self, hunger, y_offset=0):
        """Draw current sprite pose with animation frame, mirrored when walking left."""
        pose = self.current_pose
        bank = self.scaled_sprites if self.facing_right else self.scaled_sprites_left
        frames = bank.get(pose) or bank.get("idle", [])
        if not frames:
            return
        seq = self.SPRITE_SEQUENCES.get(pose, list(range(len(frames))))
        frame = frames[seq[self.animation_frame % len(seq)] % len(frames)]
        x = int(self.cat_x - (SPRITE_SIZE * self.sprite_scale) / 2)
        y = int(self.cat_y - (SPRITE_SIZE * self.sprite_scale) / 2 + y_offset)
        self.screen.blit(frame, (x, y))

    def update_pose(self, action):
        """Update current pose based on action."""
        pose_map = {
            'sleep': 'sleep',
            'eat': 'eat',
            'play': 'play',
            'purr': 'sit',
            'hide': 'sit',
            'rest': 'sleep',
            'groom': 'groom',
            'talk': 'sit',
            'train': 'play',
            'jump': 'play',
            'walk': 'walk',
            'sit': 'sit',
            'idle': 'idle'
        }
        self.current_pose = pose_map.get(action, 'idle')
    
    def draw_idle_cat(self, mood, hunger):
        """Draw cat in idle/standing position."""
        # Body
        body_y = self.cat_y
        pygame.draw.ellipse(self.screen, ORANGE, 
                          (self.cat_x - 25, body_y - 20, 50, 45))
        
        # Head
        head_y = body_y - 35
        pygame.draw.circle(self.screen, ORANGE, (self.cat_x, head_y), 30)
        
        # Ears with animation wiggle
        wiggle = int(self.animation_frame * 2) % 3 - 1
        self.draw_ears(self.cat_x, head_y - 25, wiggle)
        
        # Face
        self.draw_face(self.cat_x, head_y, mood, hunger)
        
        # Tail (animated swaying)
        tail_sway = int(self.animation_frame * 5) % 20 - 10
        tail_x = self.cat_x + 20 + tail_sway
        tail_y = body_y
        pygame.draw.arc(self.screen, ORANGE,
                       (tail_x - 15, tail_y - 30, 30, 50), 0, 3.14, 5)
    
    def draw_sleeping_cat(self, mood, hunger):
        """Draw cat sleeping (lying down)."""
        # Body (horizontal oval)
        body_y = self.cat_y + 10
        pygame.draw.ellipse(self.screen, ORANGE,
                          (self.cat_x - 40, body_y - 15, 80, 35))
        
        # Head (resting on paws)
        head_x = self.cat_x - 25
        head_y = body_y - 5
        pygame.draw.circle(self.screen, ORANGE, (head_x, head_y), 25)
        
        # Closed eyes (sleeping)
        pygame.draw.line(self.screen, BLACK,
                        (head_x - 10, head_y - 5), (head_x - 5, head_y - 5), 2)
        pygame.draw.line(self.screen, BLACK,
                        (head_x + 5, head_y - 5), (head_x + 10, head_y - 5), 2)
        
        # Sleeping Z's animation
        z_offset = int(self.animation_frame * 3) % 15
        z_text = self.font_small.render("Z z z", True, DARK_GRAY)
        self.screen.blit(z_text, (self.cat_x + 20, self.cat_y - 40 - z_offset))
        
        # Tail curled
        pygame.draw.circle(self.screen, ORANGE, (self.cat_x + 35, body_y), 8)
    
    def draw_eating_cat(self, mood, hunger):
        """Draw cat eating (head down)."""
        # Body
        body_y = self.cat_y
        pygame.draw.ellipse(self.screen, ORANGE,
                          (self.cat_x - 25, body_y - 20, 50, 45))
        
        # Head tilted down
        head_y = body_y + 5
        pygame.draw.circle(self.screen, ORANGE, (self.cat_x, head_y), 28)
        
        # Ears
        self.draw_ears(self.cat_x, head_y - 23, 0)
        
        # Eyes looking down
        pygame.draw.circle(self.screen, WHITE, (self.cat_x - 10, head_y - 5), 5)
        pygame.draw.circle(self.screen, WHITE, (self.cat_x + 10, head_y - 5), 5)
        pygame.draw.circle(self.screen, BLACK, (self.cat_x - 10, head_y - 2), 3)
        pygame.draw.circle(self.screen, BLACK, (self.cat_x + 10, head_y - 2), 3)
        
        # Food bowl
        bowl_y = body_y + 25
        pygame.draw.arc(self.screen, BLUE,
                       (self.cat_x - 20, bowl_y, 40, 20), 0, 3.14, 3)
        
        # Chomping animation
        if int(self.animation_frame * 2) % 2 == 0:
            pygame.draw.arc(self.screen, BLACK,
                           (self.cat_x - 8, head_y + 5, 16, 10), 0, 3.14, 2)
    
    def draw_playing_cat(self, mood, hunger):
        """Draw cat playing (jumping/bouncing)."""
        # Bounce animation
        bounce = abs(int(self.animation_frame * 10) % 20 - 10)
        play_y = self.cat_y - bounce
        
        # Body (stretched)
        pygame.draw.ellipse(self.screen, ORANGE,
                          (self.cat_x - 22, play_y - 25, 44, 50))
        
        # Head
        head_y = play_y - 40
        pygame.draw.circle(self.screen, ORANGE, (self.cat_x, head_y), 28)
        
        # Excited ears (perked up)
        self.draw_ears(self.cat_x, head_y - 25, 5)
        
        # Happy face
        self.draw_face(self.cat_x, head_y, "HAPPY", hunger)
        
        # Tail up (excited)
        pygame.draw.line(self.screen, ORANGE,
                        (self.cat_x + 20, play_y),
                        (self.cat_x + 25, play_y - 35), 6)
        
        # Paws reaching
        paw_offset = int(self.animation_frame * 5) % 10 - 5
        pygame.draw.circle(self.screen, ORANGE, (self.cat_x - 20 + paw_offset, play_y + 15), 8)
        pygame.draw.circle(self.screen, ORANGE, (self.cat_x + 20 - paw_offset, play_y + 15), 8)
    
    def draw_sitting_cat(self, mood, hunger):
        """Draw cat sitting."""
        # Body (sitting position)
        body_y = self.cat_y + 5
        pygame.draw.ellipse(self.screen, ORANGE,
                          (self.cat_x - 28, body_y - 15, 56, 40))
        
        # Head
        head_y = body_y - 30
        pygame.draw.circle(self.screen, ORANGE, (self.cat_x, head_y), 30)
        
        # Ears
        self.draw_ears(self.cat_x, head_y - 25, 0)
        
        # Face
        self.draw_face(self.cat_x, head_y, mood, hunger)
        
        # Tail wrapped around
        pygame.draw.arc(self.screen, ORANGE,
                       (self.cat_x - 35, body_y - 10, 40, 40), 0, 4.71, 5)
    
    def draw_walking_cat(self, mood, hunger):
        """Draw cat walking."""
        # Body
        body_y = self.cat_y
        pygame.draw.ellipse(self.screen, ORANGE,
                          (self.cat_x - 25, body_y - 20, 50, 45))
        
        # Head
        head_y = body_y - 30
        pygame.draw.circle(self.screen, ORANGE, (self.cat_x, head_y), 28)
        
        # Ears
        self.draw_ears(self.cat_x, head_y - 23, 0)
        
        # Face
        self.draw_face(self.cat_x, head_y, mood, hunger)
        
        # Legs (walking animation)
        leg_frame = int(self.animation_frame * 8) % 4
        leg_positions = [
            (-15, 0, -12, 15),  # Left front, Left back
            (-15, -5, -12, 10),
            (-15, 0, -12, 15),
            (-15, 5, -12, 20)
        ]
        lf_y, lb_y, rf_y, rb_y = leg_positions[leg_frame]
        
        # Draw legs
        pygame.draw.line(self.screen, ORANGE,
                        (self.cat_x - 15, body_y + 10),
                        (self.cat_x - 15, body_y + 25 + lf_y), 5)
        pygame.draw.line(self.screen, ORANGE,
                        (self.cat_x + 15, body_y + 10),
                        (self.cat_x + 15, body_y + 25 + rf_y), 5)
        
        # Tail swishing
        tail_swing = int(self.animation_frame * 10) % 30 - 15
        pygame.draw.line(self.screen, ORANGE,
                        (self.cat_x + 20, body_y),
                        (self.cat_x + 30 + tail_swing, body_y - 20), 5)
    
    def draw_ears(self, x, y, offset=0):
        """Draw cat ears."""
        # Left ear
        pygame.draw.polygon(self.screen, ORANGE,
                          [(x - 18 + offset, y),
                           (x - 12, y + 15),
                           (x - 22, y + 10)])
        # Right ear
        pygame.draw.polygon(self.screen, ORANGE,
                          [(x + 18 - offset, y),
                           (x + 12, y + 15),
                           (x + 22, y + 10)])
        
        # Inner ear (pink)
        pygame.draw.polygon(self.screen, PINK,
                          [(x - 18 + offset, y + 3),
                           (x - 15, y + 10),
                           (x - 20, y + 8)], 0)
        pygame.draw.polygon(self.screen, PINK,
                          [(x + 18 - offset, y + 3),
                           (x + 15, y + 10),
                           (x + 20, y + 8)], 0)
    
    def draw_face(self, x, y, mood, hunger):
        """Draw cat's face based on mood and hunger."""
        # Eyes
        eye_size = 6
        pupil_size = 3
        
        if "GRUMPY" in mood:
            # Narrowed eyes (grumpy)
            pygame.draw.line(self.screen, BLACK, (x - 15, y - 6), (x - 8, y - 9), 2)
            pygame.draw.line(self.screen, BLACK, (x + 8, y - 9), (x + 15, y - 6), 2)
        elif "HAPPY" in mood:
            # Wide happy eyes
            pygame.draw.circle(self.screen, WHITE, (x - 12, y - 5), eye_size)
            pygame.draw.circle(self.screen, WHITE, (x + 12, y - 5), eye_size)
            pygame.draw.circle(self.screen, BLACK, (x - 12, y - 5), pupil_size)
            pygame.draw.circle(self.screen, BLACK, (x + 12, y - 5), pupil_size)
        else:
            # Normal eyes
            pygame.draw.circle(self.screen, WHITE, (x - 12, y - 5), eye_size - 1)
            pygame.draw.circle(self.screen, WHITE, (x + 12, y - 5), eye_size - 1)
            pygame.draw.circle(self.screen, BLACK, (x - 12, y - 5), pupil_size)
            pygame.draw.circle(self.screen, BLACK, (x + 12, y - 5), pupil_size)
            # Subtle raised brows to look friendly
            pygame.draw.line(self.screen, BLACK, (x - 18, y - 12), (x - 8, y - 12), 2)
            pygame.draw.line(self.screen, BLACK, (x + 8, y - 12), (x + 18, y - 12), 2)
        
        # Nose
        pygame.draw.polygon(self.screen, PINK,
                          [(x, y + 5),
                           (x - 4, y + 2),
                           (x + 4, y + 2)])
        
        # Mouth
        mouth_pulse = abs(int(self.animation_frame * 3) % 6 - 3)
        mouth_w = 24 + mouth_pulse
        mouth_h = 12 + mouth_pulse // 2
        mouth_x = x - (mouth_w // 2)
        mouth_y = y + 2
        if hunger >= 70:
            # Hungry "Mau Mau" mouth animation (opening/closing)
            open_amount = abs(int(self.animation_frame * 2) % 6 - 3)
            open_h = 6 + open_amount
            pygame.draw.arc(self.screen, BLACK,
                          (x - 8, y + 6, 16, open_h), 0, 3.14, 2)
        elif "GRUMPY" in mood:
            # Slight frown (less sad)
            pygame.draw.arc(self.screen, BLACK,
                          (x - 9, y + 8, 18, 8), 3.14, 6.28, 2)
        else:
            # Default to a happy smile for all other moods (animated)
            pygame.draw.arc(self.screen, BLACK,
                          (mouth_x, mouth_y, mouth_w, mouth_h), 0, 3.14, 2)
    
    def update_animation(self):
        """Update animation frame."""
        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1:
            self.animation_frame += 1
            self.animation_timer = 0

    def get_jump_offset(self, progress):
        """Get vertical offset for jump (negative = up)."""
        peak = 40
        if progress < 0.5:
            t = progress / 0.5
            return -peak * (t * t)
        t = (progress - 0.5) / 0.5
        return -peak * (1 - t * t)

    def draw_claws(self, pos):
        """Draw three claw lines below the paws."""
        x, y = pos
        for i in (-10, 0, 10):
            pygame.draw.line(self.screen, BLACK, (x + i, y), (x + i, y + 10), 2)

    def draw_jump_cat(self, mood, hunger, progress):
        """Draw cat jumping with slow fall and claws."""
        y_offset = self.get_jump_offset(progress)
        base_y = self.cat_y + y_offset

        # Body
        pygame.draw.ellipse(self.screen, ORANGE,
                          (self.cat_x - 25, base_y - 20, 50, 45))

        # Head
        head_y = base_y - 35
        pygame.draw.circle(self.screen, ORANGE, (self.cat_x, head_y), 28)
        self.draw_ears(self.cat_x, head_y - 23, 4)
        self.draw_face(self.cat_x, head_y, "HAPPY", hunger)

        # Legs tucked
        pygame.draw.circle(self.screen, ORANGE, (self.cat_x - 12, base_y + 18), 6)
        pygame.draw.circle(self.screen, ORANGE, (self.cat_x + 12, base_y + 18), 6)

        # Claws during fall
        if progress >= 0.5:
            self.draw_claws((self.cat_x, base_y + 22))

    def draw_label(self, text, center_pos):
        """Draw a high-contrast label for better visibility with improved caching.
        
        Note: Cache uses insertion order (MRU - Most Recently Used) for eviction,
        not true LRU. This is acceptable since labels are typically accessed in similar
        patterns each frame.
        """
        if not text:
            return
        # Soft pill in the same palette as the speech bubble (was a black box)
        text_surf = self._speech_surface(text, self.font_speech_small)
        text_rect = text_surf.get_rect(center=center_pos)
        bg_rect = self._clamp_rect(text_rect.inflate(18, 8))
        text_rect.center = bg_rect.center
        pygame.draw.rect(self.screen, (255, 250, 244), bg_rect, border_radius=bg_rect.height // 2)
        pygame.draw.rect(self.screen, (235, 170, 150), bg_rect, 1, border_radius=bg_rect.height // 2)
        self.screen.blit(text_surf, text_rect)
    
    def _speech_surface(self, text, font):
        key = (text, id(font))
        surf = self.speech_cache.get(key)
        if surf is None:
            surf = font.render(text, True, (60, 45, 40))
            if len(self.speech_cache) > 60:
                self.speech_cache.clear()
            self.speech_cache[key] = surf
        return surf

    def _clamp_rect(self, rect):
        rect.left = max(6, min(rect.left, self.window_width - rect.width - 6))
        rect.top = max(6, min(rect.top, self.window_height - rect.height - 6))
        return rect

    # One bubble style for everything the cat says or thinks (same card as the hover card)
    BUBBLE_FILL = (255, 250, 244)
    BUBBLE_BORDER = (235, 170, 150)
    BUBBLE_SHADOW = (120, 100, 95)
    THOUGHT_TEXT = (130, 110, 105)

    def _bubble_rect(self, surf, rise=0):
        w, h = surf.get_width() + 24, surf.get_height() + 14
        return self._clamp_rect(pygame.Rect(self.cat_x - w // 2, self.cat_y - 105 + rise, w, h))

    def _bubble_card(self, rect):
        pygame.draw.rect(self.screen, self.BUBBLE_SHADOW, rect.move(2, 3), border_radius=12)
        pygame.draw.rect(self.screen, self.BUBBLE_FILL, rect, border_radius=12)
        pygame.draw.rect(self.screen, self.BUBBLE_BORDER, rect, 2, border_radius=12)

    def draw_speech_bubble(self, text, alpha=1.0):
        """Rounded speech bubble with a tail pointing at the cat."""
        surf = self._speech_surface(text, self.font_speech)
        rise = int((1.0 - alpha) * 8)  # tiny pop-in
        rect = self._bubble_rect(surf, rise)
        tail_x = max(rect.left + 14, min(self.cat_x, rect.right - 14))
        tail = [(tail_x - 7, rect.bottom - 2), (tail_x + 7, rect.bottom - 2), (tail_x + 2, rect.bottom + 10)]
        self._bubble_card(rect)
        pygame.draw.polygon(self.screen, self.BUBBLE_FILL, tail)
        pygame.draw.lines(self.screen, self.BUBBLE_BORDER, False, [tail[0], tail[2], tail[1]], 2)
        self.screen.blit(surf, (rect.left + 12, rect.top + 7))

    def draw_thought_bubble(self, text):
        """Same card as speech, but a trail of little bubbles and softer text: the cat is thinking."""
        surf = self._speech_surface(text, self.font_speech)
        if not hasattr(self, "_thought_cache") or self._thought_cache[0] != text:
            soft = self.font_speech.render(text, True, self.THOUGHT_TEXT)
            self._thought_cache = (text, soft)
        soft = self._thought_cache[1]
        rect = self._bubble_rect(surf)
        cx = max(rect.left + 14, min(self.cat_x, rect.right - 14))
        for (dx, dy, r) in ((-2, 9, 5), (2, 20, 3)):   # bubbles shrinking towards the cat's head
            pos = (cx + dx, rect.bottom + dy)
            pygame.draw.circle(self.screen, self.BUBBLE_FILL, pos, r)
            pygame.draw.circle(self.screen, self.BUBBLE_BORDER, pos, r, 2 if r > 3 else 1)
        self._bubble_card(rect)
        self.screen.blit(soft, (rect.left + 12, rect.top + 7))

    def draw_hover_card(self, cat_status, health):
        """Cute status card next to the cat while the mouse hovers it."""
        rows = [
            ("💚", "Health", health, (120, 200, 140)),
            ("❤️", "Happy", cat_status['happiness'], (240, 120, 140)),
            ("🍗", "Tummy", 100 - cat_status['hunger'], (245, 175, 90)),
            ("⚡", "Energy", cat_status['energy'], (250, 210, 90)),
            ("🤝", "Bond", cat_status['trust'], (170, 150, 230)),
        ]
        title = self._speech_surface(f"{cat_status['name']} · {cat_voice.mood_word(cat_status)}", self.font_speech)
        width = max(190, title.get_width() + 24)
        height = 38 + len(rows) * 22 + 8
        side = 1 if self.cat_x + 60 + width < self.window_width else -1
        left = self.cat_x + 55 if side > 0 else self.cat_x - 55 - width
        rect = self._clamp_rect(pygame.Rect(left, self.cat_y - 40, width, height))  # below the speech bubble
        pygame.draw.rect(self.screen, (120, 100, 95), rect.move(2, 3), border_radius=12)
        pygame.draw.rect(self.screen, (255, 250, 244), rect, border_radius=12)
        pygame.draw.rect(self.screen, (235, 170, 150), rect, 2, border_radius=12)
        self.screen.blit(title, (rect.left + 12, rect.top + 8))
        y = rect.top + 38
        for icon, name, value, color in rows:
            self.screen.blit(self._speech_surface(icon, self.font_speech_small), (rect.left + 10, y - 2))
            self.screen.blit(self._speech_surface(name, self.font_speech_small), (rect.left + 32, y - 1))
            bar = pygame.Rect(rect.left + 90, y + 3, width - 104, 10)
            pygame.draw.rect(self.screen, (238, 230, 225), bar, border_radius=5)
            fill = bar.copy()
            fill.width = max(0, int(bar.width * max(0, min(100, value)) / 100))
            if fill.width:
                pygame.draw.rect(self.screen, color, fill, border_radius=5)
            y += 22

    def move_cat_to_random_position(self):
        """Make cat walk to a random position (on a real monitor when there are several)."""
        if self.play_areas:
            # mostly stay on the current monitor, sometimes wander over to another one
            here = [a for a in self.play_areas if a[0] - 150 <= self.cat_x <= a[2] + 150]
            l, t, r, b = random.choice(here or self.play_areas) if random.random() < 0.85 else random.choice(self.play_areas)
            self.target_x, self.target_y = random.randint(l, r), random.randint(t, b)
            return
        self.target_x = random.randint(self.min_x, self.max_x)
        self.target_y = random.randint(self.min_y, self.max_y)
    
    def update_cat_movement(self):
        """Update cat position (walking animation)."""
        # Move towards target
        dx = self.target_x - self.cat_x
        dy = self.target_y - self.cat_y
        distance = (dx**2 + dy**2) ** 0.5
        
        if distance > 5:
            # Moving
            self.cat_x += (dx / distance) * self.cat_speed
            self.cat_y += (dy / distance) * self.cat_speed
            
            # Update facing direction
            if dx > 0:
                self.facing_right = True
            elif dx < 0:
                self.facing_right = False
            
            return True  # Is moving
        return False  # Reached target
        
    def draw_stats(self, cat_status, ui_agent=None):
        """Draw cat statistics on screen."""
        # Title
        title = self.font_large.render(f"{cat_status['name']} - Day {int(cat_status['age_days'])}", True, BLACK)
        self.screen.blit(title, (20, 20))
        
        # Mood
        mood_text = self.font_medium.render(cat_status['mood'], True, BLACK)
        self.screen.blit(mood_text, (self.window_width - 220, 20))
        
        # Stats bars with UI Agent enhanced colors and emoji indicators
        y_offset = 80
        stats = [
            ('Happiness', cat_status['happiness'], GREEN),
            ('Hunger', cat_status['hunger'], BLUE),
            ('Energy', cat_status['energy'], ORANGE),
            ('Trust', cat_status['trust'], PINK),
        ]
        
        # Get emoji-enhanced labels from UI Agent if available
        emoji_labels = None
        if ui_agent:
            emoji_labels = ui_agent.format_status_text(type('obj', (object,), {
                'happiness': cat_status['happiness'],
                'hunger': cat_status['hunger'],
                'energy': cat_status['energy'],
                'trust': cat_status['trust'],
            })())
        
        for i, (stat_name, value, default_color) in enumerate(stats):
            # Use UI Agent to determine color based on value if available
            if ui_agent:
                color = ui_agent.get_status_color(value)
            else:
                color = default_color
            
            # Label with emoji indicators from UI Agent
            if emoji_labels and i < len(emoji_labels):
                label_text = emoji_labels[i]
            else:
                label_text = f"{stat_name}: {value}"
            label = self.font_small.render(label_text, True, BLACK)
            self.screen.blit(label, (20, y_offset))
            
            # Bar background
            pygame.draw.rect(self.screen, LIGHT_GRAY, (200, y_offset, 200, 20))
            
            # Bar fill
            fill_width = int(200 * value / 100)
            pygame.draw.rect(self.screen, color, (200, y_offset, fill_width, 20))
            
            y_offset += 30
    
    def draw_instructions(self):
        """Draw game instructions with caching for performance."""
        if self.instruction_surfaces is None:
            # Cache instruction text surfaces since they never change
            instructions = [
                "Press: [P]lay(toy menu) [F]eed [S]leep [T]pet [H]ide [R]est [G]room [Y]talk [N]train",
                "Press [ESC] to exit  |  [E] to export brain  |  [L] to load brain",
                "Press [TAB] to switch cat  |  [M] to mute/unmute"
            ]
            self.instruction_surfaces = [
                self.font_small.render(text, True, DARK_GRAY) 
                for text in instructions
            ]
        
        for i, instr_surf in enumerate(self.instruction_surfaces):
            self.screen.blit(instr_surf, (20, self.window_height - 50 + i * 25))

    def draw_toy_menu(self):
        """Draw toy selection menu overlay."""
        menu_lines = [
            "Choose a toy to play with:",
            "========================================",
            "1) Ball 🔴 - Fast bouncing fun!",
            "2) Fish 🐟 - Wiggly and fun!",
            "3) Mouse 🐭 - Small and sneaky!",
            "4) Bird 🐦 - Flying and exciting!",
            "========================================",
            "Press 1-4 to choose or ESC to cancel"
        ]

        # Semi-transparent background box
        box_width = 520
        box_height = 220
        box_x = (WINDOW_WIDTH - box_width) // 2
        box_y = 120
        overlay = pygame.Surface((box_width, box_height))
        overlay.set_alpha(220)
        overlay.fill(WHITE)
        self.screen.blit(overlay, (box_x, box_y))

        # Border
        pygame.draw.rect(self.screen, DARK_GRAY, (box_x, box_y, box_width, box_height), 2)

        # Text
        for i, line in enumerate(menu_lines):
            color = BLACK if i not in (1, 6) else DARK_GRAY
            text_surf = self.font_small.render(line, True, color)
            self.screen.blit(text_surf, (box_x + 20, box_y + 20 + i * 22))

    def radial_layout(self, menu_pos, count):
        """Shared geometry for drawing and clicking the radial menu.

        Returns ([(x, y) per item], (cx, cy)). The ring grows with the number of
        items so buttons never overlap, and is nudged to stay on screen.
        """
        spacing = RADIAL_ITEM_RADIUS * 2 + 12
        radius = max(RADIAL_MENU_RADIUS, int(count * spacing / (2 * math.pi)))
        margin = radius + RADIAL_ITEM_RADIUS + 34
        cx = max(margin, min(self.window_width - margin, menu_pos[0]))
        cy = max(margin, min(self.window_height - margin, menu_pos[1]))
        step = (2 * math.pi) / max(1, count)
        points = [(cx + math.cos(-math.pi / 2 + i * step) * radius,
                   cy + math.sin(-math.pi / 2 + i * step) * radius) for i in range(count)]
        return points, (cx, cy)

    def draw_context_menu(self, menu_pos, items, mouse_pos=None, opened_ms=None):
        """Cute radial menu: cream emoji buttons in a ring around the cat.

        Everything is opaque on purpose: alpha-blending over the magenta
        color-key turns into a purple halo on the real desktop.
        """
        if not items:
            return
        points, (cx, cy) = self.radial_layout(menu_pos, len(items))
        # Pop-open animation (~150 ms): buttons slide out from the cat
        t = 1.0
        if opened_ms is not None:
            t = max(0.0, min(1.0, (pygame.time.get_ticks() - opened_ms) / 150.0))
        ease = 1 - (1 - t) ** 3

        hovered_index = None
        for i, (ix, iy) in enumerate(points):
            if mouse_pos and (mouse_pos[0] - ix) ** 2 + (mouse_pos[1] - iy) ** 2 <= (RADIAL_ITEM_RADIUS + 4) ** 2:
                hovered_index = i

        for i, (item, (ix, iy)) in enumerate(zip(items, points)):
            x = int(cx + (ix - cx) * ease)
            y = int(cy + (iy - cy) * ease)
            hovered = i == hovered_index
            r = RADIAL_ITEM_RADIUS + (RADIAL_HOVER_BUMP if hovered else 0)
            is_nav = item.get("keep_open")
            fill = (255, 226, 214) if hovered else ((246, 240, 255) if is_nav else (255, 250, 244))
            border = (235, 140, 120) if hovered else ((190, 180, 220) if is_nav else (235, 170, 150))
            pygame.draw.circle(self.screen, (150, 120, 110), (x + 1, y + 3), r)  # soft shadow
            pygame.draw.circle(self.screen, fill, (x, y), r)
            pygame.draw.circle(self.screen, border, (x, y), r, 2)
            icon = self._speech_surface(item.get("icon", "•"), self.font_speech)
            self.screen.blit(icon, icon.get_rect(center=(x, y + 1)))

        # Name of the hovered button in a pill, pushed outward from the ring
        if hovered_index is not None and t >= 1.0:
            ix, iy = points[hovered_index]
            dx, dy = ix - cx, iy - cy
            dist = max(1.0, math.hypot(dx, dy))
            off = RADIAL_ITEM_RADIUS + RADIAL_HOVER_BUMP + 18
            self.draw_label(items[hovered_index].get("label", ""),
                            (int(ix + dx / dist * off), int(iy + dy / dist * off)))

    
    def draw_chat_ui(self, response_text, input_text, waiting, frame_count):
        """
        Draw chat overlay UI (LARY Agent).
        Appears as a box in the lower portion of the screen.
        
        Args:
            response_text: AI response to display
            input_text: Current user input being typed
            waiting: Bool if waiting for API response
            frame_count: Animation frame (for cursor blink)
        """
        # Chat box dimensions
        chat_width = 760
        chat_height = 280
        chat_x = (WINDOW_WIDTH - chat_width) // 2
        chat_y = WINDOW_HEIGHT - chat_height - 20
        
        # Dim background
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        # Chat box background
        pygame.draw.rect(self.screen, (30, 30, 30), (chat_x, chat_y, chat_width, chat_height))
        pygame.draw.rect(self.screen, (100, 150, 255), (chat_x, chat_y, chat_width, chat_height), 3)
        
        # Title
        title = "🤖 LARY Agent - Ask for help (Press ? to close)"
        title_surf = self.font_small.render(title, True, (100, 180, 255))
        self.screen.blit(title_surf, (chat_x + 10, chat_y + 5))
        
        # Response area (if response exists)
        response_y = chat_y + 35
        if response_text:
            # Wrap text into lines
            words = response_text.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                test_surf = self.font_tiny.render(test_line, True, WHITE)
                if test_surf.get_width() > chat_width - 30:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                lines.append(current_line)
            
            # Draw response lines (max 8 lines visible)
            for i, line in enumerate(lines[:8]):
                line_surf = self.font_tiny.render(line, True, (200, 200, 200))
                self.screen.blit(line_surf, (chat_x + 15, response_y + i * 18))
            
            if waiting:
                # Show "thinking" indicator
                thinking_text = "⏳ Thinking..."
                think_surf = self.font_small.render(thinking_text, True, (200, 150, 100))
                self.screen.blit(think_surf, (chat_x + 15, response_y + min(len(lines), 8) * 18))
        else:
            # No response yet - show placeholder
            placeholder = "Ask LARY anything about your cat or the game!"
            placeholder_surf = self.font_small.render(placeholder, True, (100, 150, 150))
            self.screen.blit(placeholder_surf, (chat_x + 15, response_y))
        
        # Input line
        input_y = chat_y + chat_height - 50
        prompt = "You: "
        prompt_surf = self.font_small.render(prompt, True, (100, 200, 255))
        self.screen.blit(prompt_surf, (chat_x + 10, input_y))
        
        # Input text
        input_surf = self.font_small.render(input_text, True, (200, 200, 200))
        self.screen.blit(input_surf, (chat_x + 50, input_y))
        
        # Blinking cursor
        if frame_count % 60 > 30:
            cursor_x = chat_x + 50 + input_surf.get_width() + 2
            pygame.draw.line(
                self.screen,
                (200, 200, 200),
                (cursor_x, input_y),
                (cursor_x, input_y + 16),
                2
            )
        
        # Instructions at bottom
        instructions = "Press ENTER to send | ESC to close | Max 100 chars"
        inst_surf = self.font_tiny.render(instructions, True, (150, 150, 150))
        self.screen.blit(inst_surf, (chat_x + 10, chat_y + chat_height - 20))
    
    def render(self, cat_status, current_action, show_toy_menu=False, context_menu=None, overlay_labels=None, visual_state=None, ui_agent=None):
        """Render complete game frame."""
        if DESKTOP_OVERLAY and TRANSPARENT_BACKGROUND:
            self.screen.fill(TRANSPARENT_COLOR)
        else:
            self.screen.fill(WHITE)
        
        # Update animations
        self.update_animation()
        
        # Draw ground/play area
        if SHOW_UI:
            pygame.draw.rect(self.screen, LIGHT_GRAY,
                            (self.min_x - 20, self.min_y - 20,
                             self.max_x - self.min_x + 40,
                             self.max_y - self.min_y + 40), 2)
        
        jump_progress = None
        if visual_state:
            jump_progress = visual_state.get("jump_progress")
            gift = visual_state.get("gift")
            if gift:  # a little present left on the taskbar, gently bobbing
                frames = self.item_sprites.get(gift["kind"])
                if frames:
                    bob = (self.animation_frame // 4) % 2 * 2
                    frame = frames[(self.animation_frame // 6) % len(frames)]
                    self.screen.blit(frame, frame.get_rect(center=(int(gift["x"]), int(gift["y"]) - bob)))
        self.draw_cat(current_action, cat_status['mood'], cat_status['hunger'], jump_progress)
        if visual_state:
            if visual_state.get("toy"):
                self.draw_toy(visual_state["toy"], (self.cat_x + 70, self.cat_y + 42))
            if visual_state.get("food_level", 0) > 0:
                self.draw_food(visual_state["food_level"], (self.cat_x - 66, self.cat_y + 42))
            if visual_state.get("show_stats"):
                self.draw_stats_panel(cat_status, (self.cat_x + 120, self.cat_y - 40))
        if SHOW_UI:
            self.draw_stats(cat_status, ui_agent)
            self.draw_instructions()
        if show_toy_menu:
            self.draw_toy_menu()
        if context_menu:
            self.draw_context_menu(context_menu["pos"], context_menu["items"], context_menu.get("mouse_pos"),
                                   context_menu.get("opened"))
        if overlay_labels:
            for text, pos in overlay_labels:
                self.draw_label(text, pos)

        # The cat's single voice: speech bubble > thought bubble; hover card on mouse-over
        if visual_state:
            if visual_state.get("hover_card"):
                self.draw_hover_card(cat_status, visual_state.get("health", 0))
            if visual_state.get("speech"):
                self.draw_speech_bubble(visual_state["speech"], visual_state.get("speech_alpha", 1.0))
            elif visual_state.get("thought") and not visual_state.get("hover_card"):
                self.draw_thought_bubble(visual_state["thought"])

        # Chat UI overlay
        if visual_state and visual_state.get("chat_active"):
            self.draw_chat_ui(
                visual_state.get("chat_response", ""),
                visual_state.get("chat_input", ""),
                visual_state.get("chat_waiting", False),
                self.animation_frame
            )
        
        pygame.display.flip()

    @staticmethod
    def _auto_outline(surf, color=(74, 44, 33)):
        """Pixel-art outline: every empty pixel touching a filled one gets `color`."""
        w, h = surf.get_size()
        filled = {(x, y) for x in range(w) for y in range(h) if surf.get_at((x, y)).a > 0}
        for (x, y) in list(filled):
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in filled:
                    surf.set_at((nx, ny), color)
        return surf

    def make_item_sprite(self, kind, frame=0):
        """16x16 pixel-art props in the same style/palette as the cat."""
        S = 16
        s = pygame.Surface((S, S), pygame.SRCALPHA)
        px = lambda x, y, c: s.set_at((x, y), c) if 0 <= x < S and 0 <= y < S else None
        rect = lambda x, y, w, h, c: pygame.draw.rect(s, c, (x, y, w, h))
        ell = lambda x, y, w, h, c: pygame.draw.ellipse(s, c, (x, y, w, h))
        EYE, WHITE_, PINK = (45, 30, 30), (255, 255, 255), (244, 150, 160)

        if kind.startswith("bowl"):
            level = int(kind[-1])            # bowl0..bowl3
            BLUE_, BLUE_D, BLUE_L = (110, 170, 230), (80, 130, 200), (170, 210, 245)
            KIB, KIB_D = (205, 130, 70), (160, 95, 50)
            if level:                        # kibble mound (drawn first, sits behind the rim)
                top = 7 - level * 2
                ell(3, top, 10, 4 + level * 2, KIB)
                for (kx, ky) in ((5, top + 1), (8, top + 1), (10, top + 2), (6, top + 3), (9, top + 3), (7, top + 2)):
                    px(kx, ky, KIB_D)
                if level == 3:               # a little fish treat on top
                    rect(7, top - 1, 3, 2, (150, 200, 230)); px(10, top - 2, (150, 200, 230)); px(10, top, (150, 200, 230))
            pygame.draw.polygon(s, BLUE_, [(1, 9), (14, 9), (12, 14), (3, 14)])
            rect(1, 8, 14, 2, BLUE_L)        # rim
            rect(3, 11, 10, 1, BLUE_D)       # band
            px(7, 12, WHITE_); px(8, 12, WHITE_); px(6, 11, WHITE_); px(9, 11, WHITE_)  # paw decal
        elif kind == "ball":                 # yarn ball with a loose thread
            RED_, RED_D = (232, 92, 110), (190, 60, 85)
            ell(3, 3, 10, 10, RED_)
            for yy in range(3, 13):          # diagonal yarn strands inside the ball
                for xx in range(3, 13):
                    if s.get_at((xx, yy)).a and (xx + yy) % 4 == 0:
                        px(xx, yy, RED_D)
            px(5, 5, (250, 170, 180)); px(6, 4, (250, 170, 180))   # shine
            tail = [(12, 11), (13, 13), (15, 14)] if frame % 2 == 0 else [(12, 11), (14, 12), (15, 14)]
            for (tx, ty) in tail:
                px(tx, ty, RED_D)
        elif kind == "fish":                 # plush fish, tail wiggles
            TEAL, TEAL_D = (100, 190, 210), (60, 150, 180)
            ell(3, 5, 9, 7, TEAL)
            up = frame % 2
            pygame.draw.polygon(s, TEAL, [(11, 8), (15, 5 + up), (15, 11 + up)])
            rect(6, 6, 1, 5, TEAL_D); rect(8, 6, 1, 5, TEAL_D)
            px(4, 7, EYE); px(3, 9, PINK)
        elif kind == "mouse":                # grey toy mouse, tail swish
            GREY, GREY_L = (170, 165, 175), (205, 200, 210)
            ell(4, 7, 9, 6, GREY)
            ell(10, 9, 4, 3, GREY)
            pygame.draw.circle(s, GREY_L, (10, 7), 2)   # ear, next to the head
            px(10, 7, PINK)
            px(11, 9, EYE); px(14, 10, PINK)
            tail = [(3, 11), (2, 12), (1, 11), (0, 10)] if frame % 2 == 0 else [(3, 11), (2, 13), (1, 13), (0, 14)]
            for (tx, ty) in tail:
                px(tx, ty, PINK)
        elif kind == "bird":                 # little chick toy, flapping
            YEL, YEL_D, ORANGE_ = (250, 210, 90), (225, 170, 50), (240, 140, 60)
            ell(4, 6, 9, 8, YEL)
            pygame.draw.circle(s, YEL, (10, 6), 3)
            if frame % 2 == 0:
                pygame.draw.polygon(s, YEL_D, [(5, 9), (8, 9), (6, 5)])     # wing up
            else:
                pygame.draw.polygon(s, YEL_D, [(5, 9), (9, 10), (6, 12)])   # wing down
            px(11, 5, EYE)
            rect(13, 6, 2, 1, ORANGE_)
            px(7, 14, ORANGE_); px(9, 14, ORANGE_)
        elif kind == "feather":              # gift: a soft blue feather
            SKY, SKY_D, QUILL = (140, 190, 240), (95, 150, 215), (240, 235, 220)
            pygame.draw.polygon(s, SKY, [(3, 13), (6, 6), (11, 2), (13, 3), (10, 9)])
            for (fx, fy) in ((6, 9), (8, 7), (10, 5)):
                px(fx, fy, SKY_D); px(fx + 1, fy + 1, SKY_D)
            for i in range(11):              # quill along the middle
                px(3 + i, 13 - i, QUILL)
            if frame % 2:
                px(12, 2, WHITE_)            # sparkle
        elif kind == "flower":               # gift: a little pink daisy
            PETAL, PETAL_D, LEAF, CORE = (250, 170, 200), (225, 120, 160), (120, 190, 110), (250, 210, 90)
            rect(7, 8, 2, 7, LEAF)
            pygame.draw.polygon(s, LEAF, [(8, 12), (12, 10), (11, 13)])
            for (cx, cy) in ((8, 3), (5, 5), (11, 5), (6, 8), (10, 8)):
                pygame.draw.circle(s, PETAL, (cx, cy), 2)
            px(5, 6, PETAL_D); px(11, 6, PETAL_D)
            pygame.draw.circle(s, CORE, (8, 6), 2)
            if frame % 2:
                px(13, 2, WHITE_)
        elif kind == "paperfish":            # gift: an origami fish folded from a note
            PAPER, PAPER_D = (250, 245, 230), (215, 205, 185)
            pygame.draw.polygon(s, PAPER, [(1, 8), (6, 4), (11, 8), (6, 12)])
            pygame.draw.polygon(s, PAPER_D, [(6, 4), (11, 8), (6, 8)])
            pygame.draw.polygon(s, PAPER, [(11, 8), (15, 4 + frame % 2), (15, 12 + frame % 2)])
            px(4, 7, EYE)
            rect(3, 10, 3, 1, PINK)          # a tiny heart-pink stripe
        return self._auto_outline(s)

    def init_item_sprites(self):
        scale = self.sprite_scale
        kinds = {"bowl1": 1, "bowl2": 1, "bowl3": 1, "bowl0": 1, "ball": 2, "fish": 2, "mouse": 2, "bird": 2,
                 "feather": 2, "flower": 2, "paperfish": 2}
        self.item_sprites = {
            k: [pygame.transform.scale(self.make_item_sprite(k, f), (16 * scale, 16 * scale)) for f in range(n)]
            for k, n in kinds.items()
        }

    def draw_toy(self, toy, pos):
        """Draw the toy the cat is playing with (pixel-art, animated)."""
        frames = self.item_sprites.get(toy)
        if not frames:
            return
        x, y = pos
        t = self.animation_frame
        if toy == "ball":
            y -= abs(((t * 3) % 12) - 6) * 2          # bounce
        elif toy == "bird":
            y -= 6 + (t % 2) * 3                       # hovering
        elif toy == "mouse":
            x += ((t % 4) - 2) * 2                     # scurry
        frame = frames[t % len(frames)]
        self.screen.blit(frame, frame.get_rect(midbottom=(int(x), int(y))))

    def draw_food(self, level, pos):
        """Food bowl: kibble mound shrinks as the cat eats."""
        level = max(0.0, min(1.0, level))
        key = f"bowl{min(3, math.ceil(level * 3))}"
        frame = self.item_sprites[key][0]
        self.screen.blit(frame, frame.get_rect(midbottom=(int(pos[0]), int(pos[1]))))

    def draw_interest(self, pos):
        """Draw a small curiosity bubble."""
        if (self.animation_frame % 12) < 6:
            self.draw_label("?", pos)
        else:
            self.draw_label("!", pos)

    def draw_stats_panel(self, cat_status, pos):
        """Draw compact stats panel near the cat."""
        x, y = pos
        lines = [
            f"Age: {cat_status['age_days']}",
            f"Hunger: {cat_status['hunger']}",
            f"Energy: {cat_status['energy']}",
            f"Trust: {cat_status['trust']}",
            f"Happy: {cat_status['happiness']}",
            f"Learn: {cat_status['memories_count']}",
        ]
        width = 150
        height = 18 * len(lines) + 10
        panel = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, WHITE, panel)
        pygame.draw.rect(self.screen, DARK_GRAY, panel, 2)
        for i, line in enumerate(lines):
            surf = self.font_small.render(line, True, BLACK)
            self.screen.blit(surf, (x + 8, y + 6 + i * 18))


class LittleCatGame:
    """Main game controller."""
    
    def __init__(self):
        os.makedirs(CATS_DIR, exist_ok=True)
        os.makedirs(EXPORT_DIR, exist_ok=True)

        self.profile_names = self.load_profiles_index()
        if not self.profile_names:
            self.profile_names = ["Whiskers"]

        self.cats = []
        for name in self.profile_names:
            cat = CatBrain(name)
            save_path = self.get_cat_save_path(name)
            if os.path.exists(save_path):
                cat.load_brain(save_path)
            self.cats.append(cat)

        self.active_index = 0
        self.cat = self.cats[self.active_index]
        self.display = GameDisplay()
        self.running = True
        self.game_time = 0  # In-game time
        self.current_action = "idle"
        self.action_timer = 0
        self.save_path = self.get_cat_save_path(self.cat.name)
        
        # Movement timer
        self.movement_timer = 0
        self.is_moving = False
        self.ai_timer = 0

        # Toy selection
        self.waiting_for_toy = False
        self.selected_toy = None

        # Desktop overlay interaction
        self.dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.click_through = CLICK_THROUGH
        self.mouse_pos = (self.display.cat_x, self.display.cat_y)

        # Apply initial click-through state
        self.display.apply_overlay_styles(self.click_through)

        # Living on the real desktop: windows to sit on, throws, cursor chasing, gifts
        self.life = None
        if DESKTOP_OVERLAY and DESKTOP_LIFE and desktop.available():
            try:
                hwnd = pygame.display.get_wm_info().get("window") or 0
                self.life = DesktopLife((self.display.window_width, self.display.window_height),
                                        overlay_hwnd=int(hwnd), settings=DESKTOP_SETTINGS,
                                        gifts_path=os.path.join(DATA_DIR, "gifts.json"))
            except Exception as e:
                print(f"Desktop life disabled: {e}")
                self.life = None

        # Context menu
        self.context_menu_active = False
        self.context_menu_pos = (0, 0)
        self.context_menu_items = []
        self.context_menu_page = "care"
        self.context_menu_pages = {}
        self.context_menu_opened = None

        # Needs/routine checks and achievements (shown through self.say)
        self.reminder_timer = 0
        self.achievement_timer = 0

        # Mini-game state
        self.mini_game = None

        # Visual interaction state
        self.toy_visual = None
        self.toy_visual_timer = 0
        self.food_level = 0.0
        self.curiosity_timer = 0
        self.curiosity_pause = 0
        self.last_mouse_pos = (self.display.cat_x, self.display.cat_y)
        self.hunt_timer = 0
        self.hunt_target = None
        self.jump_timer = 0.0
        self.jump_duration = 1.2
        self.jump_progress = 0.0
        self.show_stats_panel = False
        self.stats_panel_timer = 0.0

        # UI Agent - intelligent UI enhancement system
        self.ui_agent = SeniorUIAgent()
        # One voice for the cat: a single speech bubble with priorities + cooldowns
        # priority: 1 ambient chatter/hints, 2 reply to you, 3 gentle need, 4 celebration
        self.speech = None            # {'text', 'expires', 'priority', 'born'}
        self.last_ambient_speech = -999.0
        self.need_cooldowns = {}
        self.thought_bubble = None
        self.thought_timer = 0.0
        self.hint_timer = 0.0
        self.chatter_timer = 0.0
        self.hover_time = 0.0
        self.last_hover_greet = -999.0
        self.last_input_time = time.time()
        self.young_play_cooldown = 0.0

        # Sound
        self.sound_enabled = SOUND_ENABLED
        self.muted = False
        self.ambient_sound = None
        self.ambient_channel = None
        self.sfx = {}
        self.sfx_volume = 0.5
        self.init_sound()

        # Chat Agent (LARY) - AI Helper
        self.chat_agent = None
        self.chat_active = False
        self.chat_input_text = ""
        self.chat_response = ""
        self.chat_cursor_blink = 0
        self.chat_waiting_for_response = False
        
        if CHAT_ENABLED and create_chat_agent:
            try:
                self.chat_agent = create_chat_agent({
                    "model": CHAT_MODEL,
                    "max_tokens": CHAT_MAX_TOKENS,
                    "timeout": CHAT_API_TIMEOUT,
                    "max_history": CHAT_HISTORY_LENGTH
                })
                if self.chat_agent:
                    print(f"✨ Chat Agent (LARY) initialized. Press '{CHAT_TOGGLE_KEY}' for help!")
            except Exception as e:
                print(f"⚠️  Chat agent setup failed: {e}")

        print(f"Loaded {self.cat.name}! Age: {self.cat.age:.1f} days")
    
    def handle_input(self):
        """Handle player input (keyboard interactions)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.KEYDOWN):
                self.last_input_time = time.time()

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Block all mouse clicks when chat is active
                if self.chat_active:
                    continue
                
                if self.mini_game and event.button == 1:
                    if self.display.is_point_on_cat(*event.pos):
                        self.resolve_mini_game(True)
                        continue
                # Left click selects context menu item
                if event.button == 1 and self.context_menu_active:
                    self.handle_context_menu_click(event.pos)
                    continue

                if event.button == 1 and self.life and self.life.gift_hit(*event.pos):
                    self.open_gift()
                    continue

                if event.button == 1 and ALLOW_DRAG:
                    if self.display.is_point_on_cat(*event.pos):
                        self.dragging = True
                        self.drag_offset_x = self.display.cat_x - event.pos[0]
                        self.drag_offset_y = self.display.cat_y - event.pos[1]
                        if self.life:
                            self.life.grab()
                            self.life.track_drag(self.display.cat_x, self.display.cat_y)
                elif event.button == 1 and CLICK_TO_PET:
                    if self.display.is_point_on_cat(*event.pos):
                        self.perform_action('purr', "You petted the cat!")
                    elif self.is_mouse_near_cat(event.pos):
                        self.start_hunt(event.pos)
                elif event.button == 3 and CLICK_TO_PLAY:
                    if self.display.is_point_on_cat(*event.pos):
                        self.show_toy_menu()
                elif event.button == 3:
                    if self.display.is_point_on_cat(*event.pos):
                        self.open_context_menu(event.pos)

            if event.type == pygame.MOUSEBUTTONUP:
                # Block mouse up when chat is active
                if self.chat_active:
                    continue
                
                if event.button == 1 and self.dragging:
                    self.end_drag()

            if event.type == pygame.MOUSEMOTION:
                # Block mouse motion when chat is active
                if self.chat_active:
                    continue
                
                self.mouse_pos = event.pos
                self.last_mouse_pos = event.pos
                self.mouse_seen = True
                if self.dragging:
                    self.drag_to(event.pos)
            
            if event.type == pygame.KEYDOWN:
                if event.key == TOGGLE_UI_KEY:
                    global SHOW_UI
                    SHOW_UI = not SHOW_UI
                    continue
                if event.key == SWITCH_CAT_KEY:
                    self.next_cat()
                    continue
                if event.key == MUTE_KEY:
                    self.toggle_mute()
                    continue
                if event.key == TOGGLE_CLICK_THROUGH_KEY:
                    self.click_through = not self.click_through
                    if self.click_through:
                        self.context_menu_active = False
                        self.dragging = False
                    self.display.apply_overlay_styles(self.click_through)
                    continue
                if event.key == pygame.K_ESCAPE and self.context_menu_active:
                    self.context_menu_active = False
                    continue
                
                # Chat Agent Toggle (?)
                if self.chat_agent and event.unicode == '?' and not self.chat_active:
                    self.chat_active = True
                    self.chat_input_text = ""
                    self.chat_response = ""
                    self.chat_waiting_for_response = False
                    continue
                
                # Chat input handling (when chat active)
                if self.chat_active:
                    if event.key == pygame.K_RETURN:
                        # Send message to LARY agent
                        if self.chat_input_text.strip():
                            game_state = self.get_game_state_for_agent()
                            self.chat_agent.request_help(
                                self.chat_input_text,
                                game_state,
                                include_screenshot=True
                            )
                            self.chat_input_text = ""
                            self.chat_waiting_for_response = True
                        continue
                    elif event.key == pygame.K_BACKSPACE:
                        self.chat_input_text = self.chat_input_text[:-1]
                        continue
                    elif event.key == pygame.K_ESCAPE:
                        self.chat_active = False
                        continue
                    elif event.unicode.isprintable():
                        if len(self.chat_input_text) < 100:  # Max input length
                            self.chat_input_text += event.unicode
                        continue
                
                # Handle toy selection if waiting (keys 1-4 on the toy ring)
                if self.waiting_for_toy or (self.context_menu_active and self.context_menu_page == "toys"):
                    if event.key == pygame.K_1:
                        self.play_with_toy('ball')
                    elif event.key == pygame.K_2:
                        self.play_with_toy('fish')
                    elif event.key == pygame.K_3:
                        self.play_with_toy('mouse')
                    elif event.key == pygame.K_4:
                        self.play_with_toy('bird')
                    elif event.key == pygame.K_ESCAPE:
                        self.waiting_for_toy = False
                        print("Play cancelled!")
                    continue
                
                # Normal game controls
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                # Play interaction - show toy menu
                elif event.key == pygame.K_p:
                    self.show_toy_menu()
                
                # Feed interaction
                elif event.key == pygame.K_f:
                    self.perform_action('eat', "You fed the cat!")
                
                # Sleep interaction
                elif event.key == pygame.K_s:
                    self.perform_action('sleep', "Cat is sleeping peacefully")
                
                # Pet/Affection interaction
                elif event.key == pygame.K_t:
                    self.perform_action('purr', "The cat purrs with delight!")
                
                # Hide interaction
                elif event.key == pygame.K_h:
                    self.perform_action('hide', "Cat hides away")
                
                # Rest interaction
                elif event.key == pygame.K_r:
                    self.perform_action('rest', "Cat is resting")

                # Groom interaction
                elif event.key == pygame.K_g:
                    self.perform_action('groom', "You gently groomed the cat")

                # Talk interaction
                elif event.key == pygame.K_y:
                    self.perform_action('talk', "You calmly talked to the cat")

                # Train interaction
                elif event.key == pygame.K_n:
                    self.perform_action('train', "You did a short training session")
                
                # Save brain
                elif event.key == pygame.K_e:
                    self.cat.save_brain(self.save_path)
                    print(f"Saved {self.cat.name}'s brain!")
                
                # Load brain
                elif event.key == pygame.K_l:
                    self.cat.load_brain(self.save_path)
                    print(f"Loaded {self.cat.name}!")

    def open_context_menu(self, pos):
        """Open the radial menu as a ring around the cat (which holds still)."""
        self.context_menu_active = True
        self.context_menu_pos = (int(self.display.cat_x), int(self.display.cat_y))
        act = lambda a, msg: (lambda: self.perform_action(a, msg))
        nav = lambda page: (lambda: self.set_menu_page(page))
        self.context_menu_pages = {
            # Page 1: caring for the cat (what you do 95% of the time)
            "care": [
                {"label": "Pet", "icon": "🤚", "action": act('purr', "You petted the cat!")},
                {"label": "Feed", "icon": "🐟", "action": act('eat', "You fed the cat!")},
                {"label": "Play", "icon": "🧶", "action": self.open_toy_page, "keep_open": True},
                {"label": "Groom", "icon": "✨", "action": act('groom', "You gently groomed the cat")},
                {"label": "Talk", "icon": "💬", "action": act('talk', "You calmly talked to the cat")},
                {"label": "Train", "icon": "⭐", "action": act('train', "You did a short training session")},
                {"label": "Nap", "icon": "💤", "action": act('sleep', "Cat is sleeping peacefully")},
                {"label": "More", "icon": "⚙️", "action": nav("more"), "keep_open": True},
            ],
            "toys": [
                {"label": "Ball", "icon": "🔴", "action": lambda: self.play_with_toy('ball')},
                {"label": "Fish", "icon": "🐠", "action": lambda: self.play_with_toy('fish')},
                {"label": "Mouse", "icon": "🐭", "action": lambda: self.play_with_toy('mouse')},
                {"label": "Bird", "icon": "🐦", "action": lambda: self.play_with_toy('bird')},
                {"label": "Back", "icon": "↩️", "action": nav("care"), "keep_open": True},
            ],
            "more": [
                {"label": "Rest", "icon": "☁️", "action": act('rest', "Cat is resting")},
                {"label": "Stats", "icon": "📊", "action": self.toggle_stats_panel},
                {"label": "Next cat", "icon": "🔁", "action": self.next_cat},
                {"label": "New cat", "icon": "🐱", "action": self.create_new_cat},
                {"label": "Save", "icon": "💾", "action": lambda: self.cat.save_brain(self.save_path)},
                {"label": "Load", "icon": "📂", "action": lambda: self.cat.load_brain(self.save_path)},
                {"label": "Export", "icon": "📤", "action": self.export_profile},
                {"label": "Import", "icon": "📥", "action": self.import_profile},
                {"label": "Export all", "icon": "📦", "action": self.export_all_profiles},
                {"label": "Goodnight (exit)", "icon": "🌙", "action": self.hibernate_game},
                {"label": "Back", "icon": "↩️", "action": nav("care"), "keep_open": True},
            ],
        }
        if self.chat_agent:
            self.context_menu_pages["more"].insert(0, {"label": "Ask LARY", "icon": "🤖", "action": self.open_chat_ui})
        self.set_menu_page("care")

    def set_menu_page(self, page):
        """Switch radial menu page (replays the pop-open animation)."""
        self.context_menu_page = page
        self.context_menu_items = list(self.context_menu_pages.get(page, []))
        self.context_menu_opened = pygame.time.get_ticks()

    def open_toy_page(self):
        if self.cat.energy < 20:
            self.context_menu_active = False
            self.perform_action('sleep', "Cat is too tired to play")
            return
        self.set_menu_page("toys")

    def handle_context_menu_click(self, pos):
        """Click a button (same geometry as drawing); clicking elsewhere closes."""
        points, _ = self.display.radial_layout(self.context_menu_pos, len(self.context_menu_items))
        for item, (ix, iy) in zip(self.context_menu_items, points):
            if (pos[0] - ix) ** 2 + (pos[1] - iy) ** 2 <= (RADIAL_ITEM_RADIUS + RADIAL_HOVER_BUMP) ** 2:
                action = item.get("action")
                if action:
                    action()
                if item.get("keep_open") and self.context_menu_active:
                    return
                break
        self.context_menu_active = False

    def is_mouse_near_cat(self, pos, radius=70):
        """Check if a position is near the cat for hunting interaction."""
        dx = pos[0] - self.display.cat_x
        dy = pos[1] - self.display.cat_y
        return (dx * dx + dy * dy) <= radius * radius

    def start_hunt(self, pos):
        """Start a short hunting/chase interaction toward the mouse."""
        self.hunt_timer = 2.2
        self.hunt_target = pos
        self.current_action = "play"
        self.action_timer = 1.2
        self.play_sfx("hunt")

    def start_jump(self):
        """Trigger a jump animation."""
        self.jump_timer = self.jump_duration
        self.play_sfx("jump")

    def get_fixed_spot(self):
        """Get a fixed resting spot near the bottom-right."""
        x = self.display.window_width - FIXED_SPOT_MARGIN_X
        y = self.display.window_height - FIXED_SPOT_MARGIN_Y
        return (x, y)

    def toggle_stats_panel(self):
        """Toggle temporary stats panel near the cat."""
        self.show_stats_panel = True
        self.stats_panel_timer = 6.0

    def load_profiles_index(self):
        """Load list of cat profiles."""
        os.makedirs(CATS_DIR, exist_ok=True)
        os.makedirs(EXPORT_DIR, exist_ok=True)
        if not os.path.exists(PROFILES_INDEX):
            return []
        try:
            with open(PROFILES_INDEX, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                # De-dup and remove missing files
                cleaned = []
                for name in data:
                    if name in cleaned:
                        continue
                    save_path = self.get_cat_save_path(name)
                    if os.path.exists(save_path):
                        cleaned.append(name)
                return cleaned
        except Exception:
            pass
        return []

    def save_profiles_index(self):
        """Persist list of cat profiles."""
        try:
            os.makedirs(CATS_DIR, exist_ok=True)
            with open(PROFILES_INDEX, 'w') as f:
                json.dump(self.profile_names, f, indent=2)
        except Exception:
            pass

    def get_cat_save_path(self, name):
        """Get per-cat save path (safe filename)."""
        safe = "".join(ch for ch in name if ch.isalnum() or ch in ("_", "-"))
        if not safe:
            safe = "Cat"
        return os.path.join(CATS_DIR, f"{safe}.json")

    def set_active_cat(self, index):
        """Switch active cat by index."""
        if not self.cats:
            return
        self.active_index = index % len(self.cats)
        self.cat = self.cats[self.active_index]
        self.save_path = self.get_cat_save_path(self.cat.name)
        if self.cat.name not in self.profile_names:
            self.profile_names.append(self.cat.name)
            self.save_profiles_index()
        self.current_action = "idle"
        self.action_timer = 0
        self.mini_game = None
        print(f"Switched to {self.cat.name}!")

    def next_cat(self):
        """Switch to the next cat profile."""
        self.set_active_cat(self.active_index + 1)

    def create_new_cat(self):
        """Create a new cat profile and switch to it."""
        new_name = self.generate_new_cat_name()
        new_cat = CatBrain(new_name)
        self.cats.append(new_cat)
        self.profile_names.append(new_name)
        self.save_profiles_index()
        self.set_active_cat(len(self.cats) - 1)

    def generate_new_cat_name(self):
        """Generate a unique cat name."""
        base = "Whiskers"
        if base not in self.profile_names:
            return base
        i = 2
        while True:
            candidate = f"{base}{i}"
            if candidate not in self.profile_names:
                return candidate
            i += 1

    def export_profile(self):
        """Export the active cat profile."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"profile_{self.cat.name}_{timestamp}.json"
        export_path = os.path.join(EXPORT_DIR, filename)
        self.cat.save_brain(export_path)
        print(f">>> Exported profile to {export_path}")
        if self.cat.name not in self.profile_names:
            self.profile_names.append(self.cat.name)
            self.save_profiles_index()

    def import_profile(self):
        """Import the most recent profile for the active cat."""
        try:
            os.makedirs(EXPORT_DIR, exist_ok=True)
            files = [f for f in os.listdir(EXPORT_DIR) if f.startswith(f"profile_{self.cat.name}_")]
            if not files:
                print(">>> No exported profile found for this cat")
                return
            latest = sorted(files)[-1]
            self.cat.load_brain(os.path.join(EXPORT_DIR, latest))
            print(f">>> Imported profile from {latest}")
            if self.cat.name not in self.profile_names:
                self.profile_names.append(self.cat.name)
                self.save_profiles_index()
        except Exception:
            print(">>> Import failed")

    def export_all_profiles(self):
        """Export all cat profiles to the exports folder."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        for cat in self.cats:
            filename = f"profile_{cat.name}_{timestamp}.json"
            export_path = os.path.join(EXPORT_DIR, filename)
            cat.save_brain(export_path)
        print(">>> Exported all profiles")

    def save_all_profiles(self):
        """Save all cat profiles and index."""
        for cat in self.cats:
            save_path = self.get_cat_save_path(cat.name)
            cat.save_brain(save_path)
        self.save_profiles_index()

    def init_sound(self):
        """Initialize ambient sound if available with optimized batch loading."""
        if not self.sound_enabled:
            return
        try:
            pygame.mixer.init()
            # Load ambient sound
            if os.path.exists(AMBIENT_SOUND_PATH):
                self.ambient_sound = pygame.mixer.Sound(AMBIENT_SOUND_PATH)
                self.ambient_channel = self.ambient_sound.play(-1)
                if self.ambient_channel:
                    self.ambient_channel.set_volume(0.25)
            # Batch load sound effects with error handling
            for key, path in SOUND_FX_PATHS.items():
                if os.path.exists(path):
                    try:
                        self.sfx[key] = pygame.mixer.Sound(path)
                    except pygame.error:
                        # Skip sounds that can't be loaded
                        continue
        except pygame.error:
            self.sound_enabled = False

    def play_sfx(self, key):
        """Play a sound effect if available."""
        if not self.sound_enabled or self.muted:
            return
        sound = self.sfx.get(key)
        if sound:
            sound.set_volume(self.sfx_volume)
            sound.play()

    def toggle_mute(self):
        """Toggle ambient sound mute."""
        if not self.sound_enabled or not self.ambient_channel:
            return
        self.muted = not self.muted
        volume = 0.0 if self.muted else 0.25
        self.ambient_channel.set_volume(volume)
        print(">>> Muted" if self.muted else ">>> Unmuted")

    def say(self, text, priority=1, duration=None):
        """Let the cat speak. One bubble at a time; lower priority never interrupts.

        Ambient lines (priority 1) also respect a global cooldown so the cat
        talks like a pet, not like a notification center.
        """
        if not text:
            return False
        now = self.game_time
        active = self.speech and self.speech['expires'] > now
        if active and priority < self.speech['priority']:
            return False
        if priority <= 1 and (active or now - self.last_ambient_speech < SPEECH_AMBIENT_COOLDOWN):
            return False
        if priority <= 1:
            self.last_ambient_speech = now
        self.speech = {'text': text, 'priority': priority, 'born': now,
                       'expires': now + (duration or SPEECH_DURATION)}
        return True

    def ask_for_need(self, key, kind):
        """Gently ask for something, at most once per SPEECH_NEED_COOLDOWN."""
        # A patient cat: waits 3x longer while you're busy, and never stacks requests
        user_busy = (time.time() - self.last_input_time) >= BUSY_THRESHOLD_SECONDS
        cooldown = SPEECH_NEED_COOLDOWN * (3 if user_busy else 1)
        last = self.need_cooldowns.get(key, -999)
        last_any = max(self.need_cooldowns.values(), default=-999)
        if self.game_time - last < cooldown or self.game_time - last_any < cooldown / 2:
            return
        if self.say(cat_voice.say(kind, self.cat), priority=3):
            self.need_cooldowns[key] = self.game_time

    def update_reminders(self):
        """Needs and routines become sweet requests in the speech bubble."""
        self.reminder_timer += 1 / FPS
        if self.reminder_timer < 2:
            return
        self.reminder_timer = 0
        kind = cat_voice.need_kind(self.cat)
        if kind:
            self.ask_for_need(kind, kind)
            return
        cat_hour = (self.cat.age * 24) % 24
        if 7 <= cat_hour <= 9 and self.cat.hunger > 50:
            self.ask_for_need('breakfast', 'breakfast')
        elif 20 <= cat_hour <= 22 and self.cat.energy < 60:
            self.ask_for_need('bedtime', 'bedtime')

    def award_achievement(self, key, text):
        """Award an achievement to the active cat."""
        if key in self.cat.achievements:
            return
        self.cat.achievements.add(key)
        self.say(cat_voice.say("achievement", self.cat, name=text), priority=4, duration=4.5)

    def update_achievements(self):
        """Check and award achievements periodically."""
        self.achievement_timer += 1 / FPS
        if self.achievement_timer >= 3:
            self.achievement_timer = 0
            if self.cat.happiness >= 85:
                self.award_achievement('happy_85', 'Sunbeam Smile')
            if self.cat.trust >= 60:
                self.award_achievement('trust_60', 'Trusted Friend')
            if self.cat.trick_level >= 2:
                self.award_achievement('trick_2', 'Trickster')
            if self.cat.age >= 1:
                self.award_achievement('first_day', 'First Day')

    def start_mini_game(self, toy_type):
        """Start a simple toy mini-game (click the cat in time)."""
        prompts = {
            'ball': "Mini-game: Click the cat to catch the ball!",
            'fish': "Mini-game: Click the cat to snag the fish!",
            'mouse': "Mini-game: Click the cat to grab the mouse!",
            'bird': "Mini-game: Click the cat to catch the bird!",
        }
        self.mini_game = {
            'toy': toy_type,
            'timer': 2.5,
            'prompt': prompts.get(toy_type, "Mini-game: Click the cat!")
        }

    def resolve_mini_game(self, success, force=False):
        """Resolve the current mini-game with a reward or penalty."""
        if not self.mini_game and not force:
            return
        if success:
            self.cat.happiness = min(100, self.cat.happiness + 6)
            self.cat.trust = min(100, self.cat.trust + 3)
            self.cat.learn_from_interaction('play', 'Mini-game success', 0.6)
            self.say(cat_voice.say('minigame_win', self.cat), priority=2)
            self.award_achievement('mini_game', 'Quick Paws')
            self.start_jump()
        else:
            # A miss is not a punishment: no happiness loss, just a funny line
            self.cat.learn_from_interaction('play', 'Mini-game missed', -0.1)
            self.say(cat_voice.say('minigame_miss', self.cat), priority=2)
        self.mini_game = None

    def get_overlay_labels(self):
        """Build overlay labels for reminders, achievements, and mini-games."""
        # Everything the cat "says" now lives in the speech bubble above it.
        # Only the mini-game call-to-action stays as a small label under the cat.
        labels = []
        if self.mini_game:
            labels.append(("click me!", (self.display.cat_x, self.display.cat_y + 55)))
        return labels
    
    def perform_action(self, action, message):
        """Player performs an action with the cat."""
        print(f">>> {message}")
        self.play_sfx(action)
        self.cat.current_intent = None  # player-driven, not the cat's own idea
        
        # Determine reward based on action and cat state
        reward = self.calculate_reward(action)
        
        # Cat learns from this interaction
        self.cat.learn_from_interaction(action, message, reward, source="player", context="human_nearby")

        # Update cat state based on action
        if action == 'play':
            self.cat.happiness = min(100, self.cat.happiness + 20)
            self.cat.energy = max(0, self.cat.energy - 15)
            self.cat.hunger = min(100, self.cat.hunger + 10)
        elif action == 'eat':
            self.cat.hunger = max(0, self.cat.hunger - 30)
            self.cat.happiness = min(100, self.cat.happiness + 5)
            self.food_level = 1.0
        elif action == 'sleep':
            self.cat.energy = min(100, self.cat.energy + 40)
            self.cat.hunger = min(100, self.cat.hunger + 20)
        elif action == 'purr':
            self.cat.happiness = min(100, self.cat.happiness + 15)
            self.cat.trust = min(100, self.cat.trust + 20)
        elif action == 'hide':
            self.cat.happiness = max(0, self.cat.happiness - 10)
        elif action == 'rest':
            self.cat.energy = min(100, self.cat.energy + 20)
        elif action == 'groom':
            self.cat.happiness = min(100, self.cat.happiness + 10)
            self.cat.trust = min(100, self.cat.trust + 10)
            self.cat.energy = max(0, self.cat.energy - 5)
        elif action == 'talk':
            self.cat.trust = min(100, self.cat.trust + 8)
            self.cat.happiness = min(100, self.cat.happiness + 3)
        elif action == 'train':
            self.cat.trust = min(100, self.cat.trust + 15)
            self.cat.happiness = min(100, self.cat.happiness + 5)
            self.cat.energy = max(0, self.cat.energy - 10)
            self.cat.hunger = min(100, self.cat.hunger + 5)

        # The cat answers in its own voice
        self.say(cat_voice.say(action, self.cat), priority=2)

        # Action-based achievements
        if action == 'eat':
            self.award_achievement('first_feed', 'First Meal')
        elif action == 'play':
            self.award_achievement('first_play', 'Playtime!')
        elif action == 'groom':
            self.award_achievement('first_groom', 'Well Groomed')
        elif action == 'train':
            self.award_achievement('first_train', 'Training Begins')
        
        self.current_action = action
        self.action_timer = 2  # Show action for 2 seconds

    def hibernate_game(self):
        """Exit from the context menu with a friendly message."""
        print(">>> Hibernate: saving and exiting")
        self.running = False
    
    def show_toy_menu(self):
        """Display toy selection menu for play interaction."""
        if self.mini_game:
            return
        if self.cat.energy < 20:
            self.perform_action('sleep', "Cat is too tired to play")
            return
        # Same cute toy ring as the right-click menu (keys 1-4 still work)
        self.open_context_menu(None)
        self.set_menu_page("toys")
    
    def open_chat_ui(self):
        """Open the chat/screen agent UI."""
        if not self.chat_agent:
            return
        self.chat_active = True
        self.chat_input_text = ""
        self.chat_response = ""
        self.chat_waiting_for_response = False
        self.context_menu_active = False
    
    def play_with_toy(self, toy_type):
        """Handle playing with a specific toy."""
        self.waiting_for_toy = False
        self.context_menu_active = False
        
        # Toy descriptions and effects
        toys = {
            'ball': {
                'name': 'Ball',
                'emoji': '🔴',
                'message': "You bounced the ball! The cat chases it excitedly!",
                'happiness_gain': 25,
                'energy_cost': 18,
                'hunger_cost': 12
            },
            'fish': {
                'name': 'Fish',
                'emoji': '🐟',
                'message': "You wiggled the fish toy! The cat pounces on it!",
                'happiness_gain': 22,
                'energy_cost': 16,
                'hunger_cost': 10
            },
            'mouse': {
                'name': 'Mouse',
                'emoji': '🐭',
                'message': "You made the mouse squeak! The cat goes crazy hunting it!",
                'happiness_gain': 24,
                'energy_cost': 17,
                'hunger_cost': 11
            },
            'bird': {
                'name': 'Bird',
                'emoji': '🐦',
                'message': "You flew the bird around! The cat jumps and pounces!",
                'happiness_gain': 26,
                'energy_cost': 19,
                'hunger_cost': 13
            }
        }
        
        toy = toys.get(toy_type)
        if not toy:
            return
        
        print(f">>> {toy['message']}")
        self.cat.current_intent = None
        self.say(f"{toy['emoji']}! {cat_voice.say('play', self.cat)}", priority=2)
        
        # Calculate reward
        reward = self.calculate_reward('play')
        
        # Cat learns from this interaction
        message = f"Played with {toy['name']} {toy['emoji']}"
        self.cat.learn_from_interaction('play', message, reward, source="player", context="human_nearby")
        
        # Update cat state based on toy choice
        self.cat.happiness = min(100, self.cat.happiness + toy['happiness_gain'])
        self.cat.energy = max(0, self.cat.energy - toy['energy_cost'])
        self.cat.hunger = min(100, self.cat.hunger + toy['hunger_cost'])
        
        # Set animation
        self.current_action = 'play'
        self.action_timer = 2.5
        
        # Update toy for display
        self.selected_toy = toy_type

        # Visual toy indicator
        self.toy_visual = toy_type
        self.toy_visual_timer = 3.2

        # Start a simple mini-game
        self.start_mini_game(toy_type)

        # Jump during play for flair
        if random.random() < 0.5:
            self.start_jump()
    
    def calculate_reward(self, action):
        """Calculate reward for an action based on cat state."""
        reward = 0.5  # Base reward
        
        # Reward matches cat needs
        if action == 'eat' and self.cat.hunger > 50:
            reward = 1.0
        elif action == 'sleep' and self.cat.energy < 40:
            reward = 1.0
        elif action == 'play' and self.cat.energy > 50 and self.cat.hunger < 60:
            reward = 0.8
        elif action == 'hide' and self.cat.trust < 40:
            reward = -0.5  # Cat doesn't want to hide if it trusts you
        elif action == 'groom' and self.cat.happiness < 50:
            reward = 0.9
        elif action == 'talk' and self.cat.trust < 50:
            reward = 0.7
        elif action == 'train' and self.cat.trust < 60 and self.cat.energy > 30:
            reward = 0.85
        
        return reward
    
    def auto_perform_action(self, action):
        """Cat performs an action autonomously (not from player)."""
        # Calculate reward for this action
        reward = self.calculate_reward(action)
        
        # Cat learns from this interaction
        messages = {
            'play': "Cat is playing with a toy!",
            'eat': "Cat meows for food...",
            'sleep': "Cat yawns and sleeps",
            'purr': "Cat purrs happily",
            'scratch': "Cat scratches the furniture",
            'hide': "Cat hides in a corner",
            'rest': "Cat is resting",
            'groom': "Cat starts grooming itself",
            'talk': "Cat chirps back at you",
            'train': "Cat practices a little trick"
        }
        message = messages.get(action, f"Cat is {action}ing")
        self.cat.learn_from_interaction(action, message, reward, source="self",
                                        context="human_nearby" if self.is_mouse_near_cat(self.mouse_pos, radius=150) else "alone")
        
        # Update cat state based on action
        if action == 'play':
            self.cat.happiness = min(100, self.cat.happiness + 20)
            self.cat.energy = max(0, self.cat.energy - 15)
            self.cat.hunger = min(100, self.cat.hunger + 10)
        elif action == 'eat':
            self.cat.hunger = max(0, self.cat.hunger - 30)
            self.cat.happiness = min(100, self.cat.happiness + 5)
        elif action == 'sleep':
            self.cat.energy = min(100, self.cat.energy + 40)
            self.cat.hunger = min(100, self.cat.hunger + 20)
        elif action == 'purr':
            self.cat.happiness = min(100, self.cat.happiness + 15)
            self.cat.trust = min(100, self.cat.trust + 20)
        elif action == 'hide':
            self.cat.happiness = max(0, self.cat.happiness - 10)
        elif action == 'rest':
            self.cat.energy = min(100, self.cat.energy + 20)
        elif action == 'groom':
            self.cat.happiness = min(100, self.cat.happiness + 6)
            self.cat.trust = min(100, self.cat.trust + 4)
        elif action == 'talk':
            self.cat.trust = min(100, self.cat.trust + 5)
        elif action == 'train':
            self.cat.trust = min(100, self.cat.trust + 8)
            self.cat.energy = max(0, self.cat.energy - 8)
            self.cat.hunger = min(100, self.cat.hunger + 4)
    
    # ------------------------------------------------------------ desktop life
    def drag_to(self, pos):
        d = self.display
        d.cat_x = pos[0] + self.drag_offset_x
        d.cat_y = pos[1] + self.drag_offset_y
        if self.life:  # anywhere on screen, so it can be placed on a window
            d.cat_x = max(40, min(d.cat_x, d.window_width - 40))
            d.cat_y = max(40, min(d.cat_y, d.window_height - 40))
            self.life.track_drag(d.cat_x, d.cat_y)
        else:
            d.cat_x = max(d.min_x, min(d.cat_x, d.max_x))
            d.cat_y = max(d.min_y, min(d.cat_y, d.max_y))
        d.target_x, d.target_y = d.cat_x, d.cat_y

    def end_drag(self):
        self.dragging = False
        if self.life:
            result = self.life.release(self.display.cat_x, self.display.cat_y)
            if result == "set_down":
                self.display.target_x, self.display.target_y = self.display.cat_x, self.display.cat_y

    def open_gift(self):
        self.life.open_gift()
        self.say(cat_voice.gift_memory(self.cat), priority=3, duration=6.0)
        self.cat.happiness = min(100, self.cat.happiness + 5)
        self.cat.memory_graph.record("gift", "you opened my gift", 0.8, age=self.cat.age, source="player",
                                     context="human_nearby")
        self.play_sfx("purr")

    def remember_desktop(self, action, response, reward):
        """Desktop adventures go to the associative memory (not the Q-table)."""
        try:
            self.cat.memory_graph.record(action, response, reward, age=self.cat.age, source="self",
                                         context="alone",
                                         state={'happiness': self.cat.happiness, 'hunger': self.cat.hunger,
                                                'energy': self.cat.energy, 'trust': self.cat.trust})
        except Exception:
            pass

    def update_desktop_life(self, dt, is_busy):
        """Returns True when desktop physics owns the cat's position this frame."""
        life = self.life
        if not life:
            return False
        d = self.display

        # The release may happen off the cat (transparent pixels don't send events): poll globally
        if self.dragging:
            cur = desktop.cursor_pos()
            if cur is not None:
                self.drag_to(life.to_local(*cur))
            if not desktop.left_button_down():
                self.end_drag()
            life.refresh(dt=dt)
            return True

        frozen = self.context_menu_active or self.chat_active or self.mini_game is not None
        if frozen and life.mode in ("free", "chase", "approach"):
            life.mode = "free"
            return False

        x, y, owns = life.update(dt, d.cat_x, d.cat_y)
        if owns or life.mode == "perched":
            d.cat_x, d.cat_y = x, y
        if owns:
            d.target_x, d.target_y = x, y

        if life.mode == "approach":
            d.target_x, d.target_y = life.approach_point()
            d.cat_speed = max(d.cat_speed, 2.6)
            if self.action_timer <= 0:
                self.current_action = "walk"
        elif life.mode == "chase" and life.cursor:
            d.target_x, d.target_y = life.chase_target(d.cat_x, d.cat_y)
            d.cat_speed = max(d.cat_speed, 4.5)
            self.current_action = "walk"
            self.action_timer = 0.2
        elif life.mode == "perched":
            d.target_x, d.target_y = life.constrain_target(d.target_x, d.target_y)
            # Time to come down: bored of the view, or hungry (but never wake a sleeping cat)
            if self.current_action != "sleep" and (life.perch_timer <= 0 or self.cat.hunger > 75):
                life.leave_perch()

        if owns and life.mode in ("airborne", "hop"):
            self.current_action = "play"   # side view, paws out
            self.action_timer = 0.15

        can_start = (not is_busy and self.action_timer <= 0 and self.hunt_timer <= 0
                     and self.current_action in ("idle", "walk") and self.cat.energy > 25
                     and self.cat.hunger < 75)
        life.wants_desktop(self.cat, dt, d.cat_x, d.cat_y, can_start)
        life.maybe_gift(dt, d.cat_x,
                        lambda: cat_voice.wellbeing({"hunger": self.cat.hunger, "energy": self.cat.energy,
                                                     "happiness": self.cat.happiness}),
                        user_present=lambda: desktop.idle_seconds() < 60)

        for ev in life.pop_events():
            self.on_desktop_event(ev)
        return owns

    def on_desktop_event(self, ev):
        lines = {"thrown": ("thrown", 2), "bonk": ("bonk", 2), "landed": ("landed", 2),
                 "perch_fall": ("perch_fall", 2), "chase_tired": ("chase_tired", 1),
                 "chase_caught": ("chase", 2), "gift_drop": ("gift_drop", 3)}
        if ev == "perched":
            self.current_action = "sit"
            self.action_timer = 2.0
            if random.random() < 0.6:
                self.say(cat_voice.say("perch", self.cat), priority=1)
            self.remember_desktop("perch", "nice view from the window", 0.4)
        elif ev == "chase_start":
            self.cat.current_intent = _REASONS["chase_cursor"]
        elif ev == "chase_caught":
            self.current_action = "play"
            self.action_timer = 1.2
            self.cat.happiness = min(100, self.cat.happiness + 4)
            self.cat.energy = max(0, self.cat.energy - 3)
            self.remember_desktop("chase_cursor", "caught the cursor", 0.5)
        elif ev == "thrown":
            self.play_sfx("jump")
        elif ev == "approach":
            self.cat.current_intent = _REASONS["perch"]
        if ev in lines:
            kind, prio = lines[ev]
            if ev == "landed" and random.random() < 0.5:
                return
            line = cat_voice.say(kind, self.cat)
            if line:
                self.say(line, priority=prio, duration=2.5 if prio < 3 else 4.0)

    def is_hovering_cat(self):
        return (getattr(self, "mouse_seen", False) and not self.dragging and not self.context_menu_active
                and self.display.is_point_on_cat(*self.mouse_pos))

    def update_voice(self):
        """Speech, thoughts, hover card and gentle chatter - one calm channel."""
        dt = 1 / FPS
        if self.speech and self.speech['expires'] <= self.game_time:
            self.speech = None

        # Hover: show the status card and say hi (not too often)
        if self.is_hovering_cat():
            self.hover_time += dt
            if self.hover_time >= HOVER_CARD_DELAY and self.game_time - self.last_hover_greet > 40:
                self.last_hover_greet = self.game_time
                kind = "hover_sleepy" if self.current_action == "sleep" else "hover"
                self.say(cat_voice.say(kind, self.cat), priority=2, duration=2.5)
        else:
            self.hover_time = 0.0

        # Thought bubble: stable for a few seconds instead of re-rolling every frame
        self.thought_timer -= dt
        if self.cat.current_intent and self.action_timer > 0:
            self.thought_bubble = self.cat.current_intent
        elif self.thought_timer <= 0:
            self.thought_timer = 6.0
            self.thought_bubble = self.ui_agent.get_thought_bubble(self.cat) if random.random() < 0.35 else None

        # Respect a busy human and a sleeping cat: no small talk then
        user_busy = (time.time() - self.last_input_time) >= BUSY_THRESHOLD_SECONDS
        if user_busy or self.current_action == "sleep":
            return

        # First minutes only: a few tutorial whispers, in the cat's voice
        self.hint_timer += dt
        if self.game_time < 600 and self.hint_timer >= 90:
            self.hint_timer = 0
            hint = self.ui_agent.get_hint({'cat_brain': self.cat})
            if hint:
                for prefix in ("💡 Tip: ", "💡 Hint: ", "💡 Info: "):
                    hint = hint.replace(prefix, "psst... ")
                self.say(hint, priority=1, duration=5.0)

        # Occasional happy chatter / memories (global cooldown applies in say())
        self.chatter_timer += dt
        if self.chatter_timer >= 15:
            self.chatter_timer = 0
            if random.random() < 0.5:
                self.say(cat_voice.idle_chatter(self.cat), priority=1)

    def update(self):
        """Update game state."""
        # Update cat internal state
        delta_time = GAME_SPEED
        self.cat.update_state(delta_time)

        self.update_voice()

        is_adult = self.cat.age >= ADULT_AGE_DAYS
        is_busy = (time.time() - self.last_input_time) >= BUSY_THRESHOLD_SECONDS

        # Age-based pacing (older cats move and act less)
        age_days = self.cat.age
        move_interval = min(12, 5 + age_days * 0.2)  # seconds
        ai_interval = min(10, 3 + age_days * 0.25)   # seconds
        self.display.cat_speed = max(0.8, 2.0 - age_days * 0.03)

        # Real desktop: perching, flying after a throw, chasing the cursor, gifts
        owns_position = self.update_desktop_life(1 / FPS, is_busy)
        desktop_mode = self.life.mode if self.life else "free"
        desktop_free = desktop_mode in ("free", "perched") and not self.dragging

        # Hunting interaction (mouse chase)
        if self.hunt_timer > 0:
            self.hunt_timer -= 1 / FPS
            target = self.last_mouse_pos if self.last_mouse_pos else self.display.target_x
            self.display.target_x, self.display.target_y = target
            self.display.cat_speed = max(self.display.cat_speed, 3.0)
            self.current_action = "play"
            if self.is_mouse_near_cat(target, radius=25):
                self.resolve_mini_game(True, force=True)
                self.hunt_timer = 0

        # Adult behavior: stay near fixed spot and sleep more when user busy
        if is_adult and is_busy and ADULT_FIXED_SPOT and desktop_free:
            fixed_x, fixed_y = self.get_fixed_spot()
            self.display.target_x, self.display.target_y = fixed_x, fixed_y
            self.display.cat_speed = min(self.display.cat_speed, 1.2)
            if self.action_timer <= 0:
                if self.cat.hunger > 70:
                    self.ask_for_need("need_hungry", "need_hungry")
                    self.current_action = "talk"
                    self.action_timer = 2.5
                elif self.cat.energy < 40:
                    self.current_action = "sleep"
                    self.action_timer = 3.5 * ADULT_SLEEP_MULTIPLIER
                else:
                    self.current_action = "rest"
                    self.action_timer = 2.5 * ADULT_REST_MULTIPLIER
        
        # Young cat behavior: follow cursor and try to play
        if not is_adult and YOUNG_FOLLOW_CURSOR and self.last_mouse_pos and desktop_free:
            mx, my = self.last_mouse_pos
            self.display.target_x, self.display.target_y = mx, my
            if self.young_play_cooldown > 0:
                self.young_play_cooldown -= 1 / FPS
            if self.is_mouse_near_cat(self.last_mouse_pos, radius=YOUNG_PLAY_DISTANCE):
                if self.young_play_cooldown <= 0 and self.cat.energy > 40 and self.cat.hunger < 70:
                    self.cat.current_intent = "gonna catch it!"
                    self.auto_perform_action("play")
                    self.current_action = "play"
                    self.action_timer = 1.5
                    self.young_play_cooldown = YOUNG_PLAY_COOLDOWN

        # Jump animation progress
        if self.jump_timer > 0:
            self.jump_timer -= 1 / FPS
            self.jump_progress = 1 - (self.jump_timer / self.jump_duration)
            self.current_action = "jump"
        else:
            self.jump_progress = 0.0
        
        # Update cat movement animation
        if self.context_menu_active:
            # Hold still while the menu ring is open around the cat
            self.display.target_x, self.display.target_y = self.context_menu_pos
            self.display.cat_x, self.display.cat_y = self.context_menu_pos
            self.is_moving = False
        elif owns_position or self.dragging:
            self.is_moving = False
        elif self.current_action in ("idle", "walk") or self.hunt_timer > 0:
            if desktop_mode == "perched":  # walk along the title bar, never off into the air
                self.display.target_x, self.display.target_y = self.life.constrain_target(
                    self.display.target_x, self.display.target_y)
            self.is_moving = self.display.update_cat_movement()

            # Randomly wander
            self.movement_timer += 1 / FPS
            if (self.movement_timer > move_interval and not self.is_moving and self.hunt_timer <= 0
                    and self.curiosity_pause <= 0 and not (is_adult and is_busy) and desktop_free):
                self.display.move_cat_to_random_position()
                self.movement_timer = 0

        # Curiosity pause while walking
        if self.hunt_timer <= 0 and desktop_free:
            curiosity = 0.5
            if hasattr(self.cat, "personality"):
                curiosity = self.cat.personality.get("curious", 0.5)
            self.curiosity_timer += 1 / FPS
            if self.curiosity_pause <= 0 and self.is_moving and self.curiosity_timer > 5:
                chance = 0.06 + (curiosity * 0.10)
                if random.random() < chance:
                    self.curiosity_pause = 0.8 + (curiosity * 1.2)
                    self.curiosity_timer = 0
                    # Really stop: "sit" for the whole pause, so the walk code leaves it alone
                    # (before, the pose said sit while the cat kept sliding to its target)
                    self.current_action = "sit"
                    self.action_timer = max(self.action_timer, self.curiosity_pause)
            if self.curiosity_pause > 0:
                self.curiosity_pause -= 1 / FPS
                self.is_moving = False
        
        # Decrease action timer
        if self.action_timer > 0:
            self.action_timer -= 1 / FPS
        else:
            # Return to idle or walking
            if self.is_moving:
                self.current_action = "walk"
            else:
                self.current_action = "idle"
        
        # AI decides action if too much time has passed
        if not (is_adult and is_busy) and desktop_free:
            self.ai_timer += 1 / FPS
            if self.ai_timer >= ai_interval:
                self.ai_timer = 0
                context = "human_nearby" if self.action_timer > 0 else "alone"
                action, confidence = self.cat.decide_action(context)
                
                # Prevent auto-play when energy is low
                if action == "play" and self.cat.energy < 35:
                    action = "sleep" if self.cat.energy < 20 else "rest"
                
                if confidence > 0.6 and self.action_timer <= 0:
                    # Auto-perform action (with state changes!)
                    self.auto_perform_action(action)
                    self.current_action = action
                    self.action_timer = 2.5
                    # Stop where it is: an eating/sleeping cat must not glide on afterwards
                    self.display.target_x, self.display.target_y = self.display.cat_x, self.display.cat_y
                    self.is_moving = False

        # Mini-game timer
        if self.mini_game:
            self.mini_game['timer'] -= 1 / FPS
            if self.mini_game['timer'] <= 0:
                self.resolve_mini_game(False)

        # Visual toy and food timers
        if self.toy_visual_timer > 0:
            self.toy_visual_timer -= 1 / FPS
        else:
            self.toy_visual = None
        if self.food_level > 0:
            self.food_level = max(0.0, self.food_level - (0.25 / FPS))

        # Stats panel timer
        if self.stats_panel_timer > 0:
            self.stats_panel_timer -= 1 / FPS
            self.show_stats_panel = True
        else:
            self.show_stats_panel = False

        # Routines and achievements
        self.update_reminders()
        self.update_achievements()
        
        # Chat agent update (check for responses from async AI)
        if self.chat_active:
            self.update_chat_response()
        
        self.game_time += 1 / FPS
    
    def run(self):
        """Main game loop."""
        print("\n=== LITTLE CAT PET GAME ===")
        print(f"Meet {self.cat.name}! This cat will learn from your interactions.")
        print("The more you interact, the more the cat learns!\n")
        
        while self.running:
            self.handle_input()
            self.update()
            
            cat_status = self.cat.get_status()
            context_menu = None
            if self.context_menu_active:
                context_menu = {"pos": self.context_menu_pos, "items": self.context_menu_items,
                                "mouse_pos": self.mouse_pos, "opened": getattr(self, "context_menu_opened", None)}
            overlay_labels = self.get_overlay_labels()
            visual_state = {
                "toy": self.toy_visual,
                "food_level": self.food_level,
                "curious": self.curiosity_pause > 0 and not self.speech,
                "jump_progress": self.jump_progress,
                "gift": self.life.gift if self.life else None,
                "show_stats": self.show_stats_panel,
                "speech": self.speech['text'] if self.speech else None,
                "speech_alpha": min(1.0, (self.game_time - self.speech['born']) / 0.2) if self.speech else 1.0,
                "thought": self.thought_bubble if not SHOW_UI else None,
                "hover_card": self.hover_time >= HOVER_CARD_DELAY,
                "health": cat_voice.wellbeing(cat_status),
                "chat_active": self.chat_active,
                "chat_response": self.chat_response,
                "chat_input": self.chat_input_text,
                "chat_waiting": self.chat_waiting_for_response
            }
            self.display.render(cat_status, self.current_action, self.waiting_for_toy, context_menu, overlay_labels, visual_state, self.ui_agent)
            
            self.display.clock.tick(FPS)
        
        # Save before exit
        self.save_all_profiles()
        print(f"\nSaved {self.cat.name}'s brain. Goodbye!")
        pygame.quit()
        sys.exit()
    
    def get_game_state_for_agent(self) -> Dict:
        """
        Snapshot current game state for LARY agent context.
        Called ONLY when user requests help (not every frame).
        
        Returns:
            Dict with cat stats and game info
        """
        cat = self.cat
        return {
            "timestamp": datetime.now().isoformat(),
            "cat_name": cat.name,
            "age": cat.age,
            "hunger": cat.hunger,
            "energy": cat.energy,
            "happiness": cat.happiness,
            "trust": cat.trust,
            "personality": list(cat.personality.keys()) if hasattr(cat, 'personality') else [],
            "last_action": self.current_action,
            "trick_level": cat.trick_level if hasattr(cat, 'trick_level') else 1,
            "achievements": list(cat.achievements) if hasattr(cat, 'achievements') else [],
            "q_learning_active": True if hasattr(cat, 'q_table') else False,
        }
    
    def update_chat_response(self):
        """
        Check for incoming chat responses from async API.
        Called every frame while chat is active.
        """
        if not self.chat_agent or not self.chat_active:
            return
        
        # Check for new response
        response = self.chat_agent.get_response()
        if response:
            self.chat_response = response
            self.chat_waiting_for_response = False
        
        # Update cursor blink animation
        self.chat_cursor_blink = (self.chat_cursor_blink + 1) % 60


if __name__ == "__main__":
    game = LittleCatGame()
    game.run()
