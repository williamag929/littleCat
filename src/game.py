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
import time
from datetime import datetime
from typing import Dict, Optional, Tuple, List

# Load environment variables (.env file)
try:
    from dotenv import load_dotenv
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
GAME_SPEED = 0.02  # Time multiplier for simulation (slower days)

# Optional behavior settings (can be overridden in config.py)
try:
    import config as cfg
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
SPRITE_SCALE = 2

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
        if DESKTOP_OVERLAY:
            info = pygame.display.Info()
            self.window_width = info.current_w
            self.window_height = info.current_h
            flags = pygame.NOFRAME
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
        self.label_cache = {}
        
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
            if action == "jump" and jump_progress is not None and jump_progress >= 0.5:
                self.draw_claws((self.cat_x, self.cat_y + jump_offset + 10))
            if action != "idle":
                action_text = f"{action.upper()}"
                self.draw_label(action_text, (self.cat_x, self.cat_y - 100))
            return
        
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
        
        # Action indicator above cat
        if action != "idle":
            action_text = f"{action.upper()}"
            self.draw_label(action_text, (self.cat_x, self.cat_y - 100))

    def init_pixel_sprites(self):
        """Generate simple 90s-style pixel sprites for the cat."""
        self.sprites = {
            "idle": [self.make_cat_sprite("idle", f) for f in range(4)],
            "walk": [self.make_cat_sprite("walk", f) for f in range(4)],
            "sit": [self.make_cat_sprite("sit", f) for f in range(2)],
            "sleep": [self.make_cat_sprite("sleep", f) for f in range(2)],
            "eat": [self.make_cat_sprite("eat", f) for f in range(2)],
            "play": [self.make_cat_sprite("play", f) for f in range(3)],
        }
        self.scaled_sprites = {
            pose: [
                pygame.transform.scale(frame, (SPRITE_SIZE * self.sprite_scale, SPRITE_SIZE * self.sprite_scale))
                for frame in frames
            ]
            for pose, frames in self.sprites.items()
        }

    def make_cat_sprite(self, pose, frame):
        """Create a single pixel-art frame for a pose."""
        surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)

        def px(x, y, color):
            if 0 <= x < SPRITE_SIZE and 0 <= y < SPRITE_SIZE:
                surf.set_at((x, y), color)

        def rect(x, y, w, h, color):
            pygame.draw.rect(surf, color, (x, y, w, h))

        # Body base
        if pose == "sleep":
            rect(6, 16, 20, 8, ORANGE)
            rect(2, 17, 8, 6, ORANGE)
            # Eyes closed
            px(5, 19, BLACK)
            px(7, 19, BLACK)
            # Tail curl
            rect(24, 18, 4, 4, ORANGE)
        else:
            rect(8, 14, 16, 12, ORANGE)
            rect(10, 6, 12, 10, ORANGE)

            # Ears
            px(11, 4, ORANGE)
            px(20, 4, ORANGE)
            px(12, 5, ORANGE)
            px(19, 5, ORANGE)

            # Eyes
            px(13, 10, BLACK)
            px(18, 10, BLACK)

            # Mouth (pose-based)
            if pose == "eat" and frame % 2 == 0:
                px(15, 12, BLACK)
            elif pose == "play":
                px(14, 12, BLACK)
                px(16, 12, BLACK)
            else:
                px(15, 12, BLACK)

            # Tail
            tail_shift = (frame % 3) - 1
            rect(24 + tail_shift, 16, 4, 8, ORANGE)

            # Legs (walk frames)
            if pose == "walk":
                if frame % 2 == 0:
                    rect(10, 26, 2, 4, ORANGE)
                    rect(20, 24, 2, 6, ORANGE)
                else:
                    rect(10, 24, 2, 6, ORANGE)
                    rect(20, 26, 2, 4, ORANGE)
            elif pose == "sit":
                rect(12, 24, 8, 6, ORANGE)

        # Play pose: slight bounce
        if pose == "play":
            bounce = (frame % 3)
            bounced = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
            bounced.blit(surf, (0, -bounce))
            surf = bounced

        return surf

    def draw_sprite_pose(self, hunger, y_offset=0):
        """Draw current sprite pose with animation frame."""
        pose = self.current_pose
        frames = self.scaled_sprites.get(pose, self.scaled_sprites.get("idle", []))
        if not frames:
            return

        frame = frames[self.animation_frame % len(frames)]
        x = int(self.cat_x - (SPRITE_SIZE * self.sprite_scale) / 2)
        y = int(self.cat_y - (SPRITE_SIZE * self.sprite_scale) / 2 + y_offset)
        self.screen.blit(frame, (x, y))

        # Hungry "Mau Mau" bubble
        if hunger >= 70:
            self.draw_label("Mau Mau", (x + 58, y - 28))
    
    def update_pose(self, action):
        """Update current pose based on action."""
        pose_map = {
            'sleep': 'sleep',
            'eat': 'eat',
            'play': 'play',
            'purr': 'sit',
            'hide': 'sit',
            'rest': 'sit',
            'groom': 'sit',
            'talk': 'sit',
            'train': 'play',
            'jump': 'play',
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
            # Small "Mau Mau" text bubble
            self.draw_label("Mau Mau", (x + 40, y - 20))
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
        """Draw a high-contrast label for better visibility."""
        if text in self.label_cache:
            text_surf = self.label_cache[text]
        else:
            text_surf = self.font_small.render(text, True, BLACK)
            self.label_cache[text] = text_surf
            if len(self.label_cache) > 40:
                self.label_cache.clear()
        text_rect = text_surf.get_rect(center=center_pos)

        padding_x = 8
        padding_y = 4
        bg_rect = pygame.Rect(
            text_rect.left - padding_x,
            text_rect.top - padding_y,
            text_rect.width + padding_x * 2,
            text_rect.height + padding_y * 2
        )

        pygame.draw.rect(self.screen, WHITE, bg_rect)
        pygame.draw.rect(self.screen, BLACK, bg_rect, 2)
        self.screen.blit(text_surf, text_rect)
    
    def move_cat_to_random_position(self):
        """Make cat walk to a random position."""
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
        
    def draw_stats(self, cat_status):
        """Draw cat statistics on screen."""
        # Title
        title = self.font_large.render(f"{cat_status['name']} - Day {int(cat_status['age_days'])}", True, BLACK)
        self.screen.blit(title, (20, 20))
        
        # Mood
        mood_text = self.font_medium.render(cat_status['mood'], True, BLACK)
        self.screen.blit(mood_text, (self.window_width - 220, 20))
        
        # Stats bars
        y_offset = 80
        stats = [
            ('Happiness', cat_status['happiness'], GREEN),
            ('Hunger', cat_status['hunger'], BLUE),
            ('Energy', cat_status['energy'], ORANGE),
            ('Trust', cat_status['trust'], PINK),
        ]
        
        for stat_name, value, color in stats:
            # Label
            label = self.font_small.render(f"{stat_name}: {value}", True, BLACK)
            self.screen.blit(label, (20, y_offset))
            
            # Bar background
            pygame.draw.rect(self.screen, LIGHT_GRAY, (200, y_offset, 200, 20))
            
            # Bar fill
            fill_width = int(200 * value / 100)
            pygame.draw.rect(self.screen, color, (200, y_offset, fill_width, 20))
            
            y_offset += 30
    
    def draw_instructions(self):
        """Draw game instructions."""
        instructions = [
            "Press: [P]lay(toy menu) [F]eed [S]leep [T]pet [H]ide [R]est [G]room [Y]talk [N]train",
            "Press [ESC] to exit  |  [E] to export brain  |  [L] to load brain",
            "Press [TAB] to switch cat  |  [M] to mute/unmute"
        ]
        
        for i, text in enumerate(instructions):
            instr_surf = self.font_small.render(text, True, DARK_GRAY)
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

    def draw_context_menu(self, menu_pos, items, mouse_pos=None):
        """Draw improved circular menu with gradient background and text labels."""
        if not items:
            return

        cx, cy = menu_pos
        count = len(items)
        if count == 0:
            return

        # Keep within window bounds by nudging center
        margin = RADIAL_MENU_RADIUS + 40
        cx = max(margin, min(self.window_width - margin, cx))
        cy = max(margin, min(self.window_height - margin, cy))

        # Draw semi-transparent gradient background circle (dimmed)
        background_radius = RADIAL_MENU_RADIUS + 50
        overlay = pygame.Surface((background_radius * 2, background_radius * 2), pygame.SRCALPHA)
        
        # Gradient effect: dark center fading out
        for r in range(background_radius, 0, -5):
            alpha = int(120 * (1 - r / background_radius))  # Fade from 120 to 0
            color = (20, 20, 30, alpha)  # Dark blue-gray
            pygame.draw.circle(overlay, color, (background_radius, background_radius), r)
        
        self.screen.blit(overlay, (int(cx - background_radius), int(cy - background_radius)))

        base_angle = -math.pi / 2
        step = (2 * math.pi) / count

        # Draw connecting lines from center (optional subtle feature)
        for i in range(count):
            angle = base_angle + i * step
            ix = cx + math.cos(angle) * RADIAL_MENU_RADIUS
            iy = cy + math.sin(angle) * RADIAL_MENU_RADIUS
            pygame.draw.line(self.screen, (80, 80, 100, 100), (int(cx), int(cy)), (int(ix), int(iy)), 1)

        # Draw center dot with glow effect
        pygame.draw.circle(self.screen, (100, 150, 255), (int(cx), int(cy)), 14)
        pygame.draw.circle(self.screen, (150, 200, 255), (int(cx), int(cy)), 14, 2)

        # Draw menu items
        for i, item in enumerate(items):
            angle = base_angle + i * step
            ix = cx + math.cos(angle) * RADIAL_MENU_RADIUS
            iy = cy + math.sin(angle) * RADIAL_MENU_RADIUS

            hovered = False
            if mouse_pos:
                dx = mouse_pos[0] - ix
                dy = mouse_pos[1] - iy
                hovered = (dx * dx + dy * dy) <= (RADIAL_ITEM_RADIUS + RADIAL_HOVER_BUMP) ** 2

            radius = RADIAL_ITEM_RADIUS + (RADIAL_HOVER_BUMP if hovered else 0)
            
            # Draw item button with gradient effect
            if hovered:
                # Brighter on hover - gradient from blue to cyan
                pygame.draw.circle(self.screen, (120, 180, 255), (int(ix), int(iy)), radius)
                pygame.draw.circle(self.screen, (150, 200, 255), (int(ix), int(iy)), radius, 3)
                glow_radius = int(radius * 1.15)
                pygame.draw.circle(self.screen, (120, 180, 255, 100), (int(ix), int(iy)), glow_radius, 1)
            else:
                # Dark gradient blue
                pygame.draw.circle(self.screen, (60, 100, 150), (int(ix), int(iy)), radius)
                pygame.draw.circle(self.screen, (100, 150, 200), (int(ix), int(iy)), radius, 2)

            # Draw text label
            label = item.get("label", "")
            if label:
                text_color = (255, 255, 255) if hovered else (200, 220, 240)
                label_surf = self.font_small.render(label, True, text_color)
                label_rect = label_surf.get_rect(center=(int(ix), int(iy)))
                
                # Add slight shadow effect for better readability
                shadow_surf = self.font_small.render(label, True, (20, 20, 30, 180))
                shadow_rect = shadow_surf.get_rect(center=(int(ix) + 1, int(iy) + 1))
                self.screen.blit(shadow_surf, shadow_rect)
                self.screen.blit(label_surf, label_rect)

            # Show tooltip on hover
            if hovered and label:
                tooltip_y = int(iy + radius + 20)
                tooltip_text = item.get("tooltip", label)
                tooltip_surf = self.font_tiny.render(tooltip_text, True, (200, 220, 240))
                tooltip_rect = tooltip_surf.get_rect(center=(int(ix), tooltip_y))
                
                # Tooltip background
                tooltip_bg = pygame.Surface((tooltip_rect.width + 16, tooltip_rect.height + 8), pygame.SRCALPHA)
                pygame.draw.rect(tooltip_bg, (30, 50, 80, 200), tooltip_bg.get_rect(), border_radius=4)
                self.screen.blit(tooltip_bg, (tooltip_rect.x - 8, tooltip_rect.y - 4))
                self.screen.blit(tooltip_surf, tooltip_rect)
    
    
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
    
    def render(self, cat_status, current_action, show_toy_menu=False, context_menu=None, overlay_labels=None, visual_state=None):
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
        self.draw_cat(current_action, cat_status['mood'], cat_status['hunger'], jump_progress)
        if visual_state:
            if visual_state.get("toy"):
                self.draw_toy(visual_state["toy"], (self.cat_x + 40, self.cat_y + 20))
            if visual_state.get("food_level", 0) > 0:
                self.draw_food(visual_state["food_level"], (self.cat_x - 50, self.cat_y + 30))
            if visual_state.get("curious"):
                self.draw_interest((self.cat_x + 10, self.cat_y - 80))
            if visual_state.get("show_stats"):
                self.draw_stats_panel(cat_status, (self.cat_x + 120, self.cat_y - 40))
        if SHOW_UI:
            self.draw_stats(cat_status)
            self.draw_instructions()
        if show_toy_menu:
            self.draw_toy_menu()
        if context_menu:
            self.draw_context_menu(context_menu["pos"], context_menu["items"], context_menu.get("mouse_pos"))
        if overlay_labels:
            for text, pos in overlay_labels:
                self.draw_label(text, pos)
        
        # Chat UI overlay
        if visual_state and visual_state.get("chat_active"):
            self.draw_chat_ui(
                visual_state.get("chat_response", ""),
                visual_state.get("chat_input", ""),
                visual_state.get("chat_waiting", False),
                self.animation_frame
            )
        
        pygame.display.flip()

    def draw_toy(self, toy, pos):
        """Draw a simple toy icon near the cat."""
        x, y = pos
        wobble = (self.animation_frame % 6) - 3
        y += wobble // 2
        if toy == "ball":
            pygame.draw.circle(self.screen, RED, (x, y), 8)
            pygame.draw.line(self.screen, DARK_GRAY, (x - 10, y + 8), (x - 16, y + 12), 2)
            pygame.draw.line(self.screen, DARK_GRAY, (x + 10, y + 8), (x + 16, y + 12), 2)
        elif toy == "fish":
            pygame.draw.ellipse(self.screen, BLUE, (x - 10, y - 4, 20, 8))
            pygame.draw.circle(self.screen, BLUE, (x - 12, y), 3)
            pygame.draw.line(self.screen, DARK_GRAY, (x + 10, y - 2), (x + 15, y - 6), 2)
        elif toy == "mouse":
            pygame.draw.ellipse(self.screen, DARK_GRAY, (x - 8, y - 5, 16, 10))
            pygame.draw.circle(self.screen, DARK_GRAY, (x + 6, y - 5), 3)
            pygame.draw.line(self.screen, DARK_GRAY, (x - 10, y + 2), (x - 18, y + 6), 2)
        elif toy == "bird":
            pygame.draw.circle(self.screen, GREEN, (x, y), 6)
            pygame.draw.polygon(self.screen, GREEN, [(x + 6, y), (x + 12, y - 3), (x + 12, y + 3)])
            pygame.draw.line(self.screen, DARK_GRAY, (x - 6, y - 2), (x - 12, y - 6), 2)

    def draw_food(self, level, pos):
        """Draw a food bowl that empties as level decreases."""
        x, y = pos
        pygame.draw.arc(self.screen, BLUE, (x - 18, y - 4, 36, 16), 0, 3.14, 3)
        fill_width = int(28 * max(0.0, min(1.0, level)))
        if fill_width > 0:
            pygame.draw.rect(self.screen, ORANGE, (x - 14, y - 8, fill_width, 6))
        if level > 0.2 and (self.animation_frame % 10) < 5:
            pygame.draw.line(self.screen, DARK_GRAY, (x - 6, y - 14), (x - 2, y - 18), 2)
            pygame.draw.line(self.screen, DARK_GRAY, (x + 6, y - 14), (x + 2, y - 18), 2)

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

        # Context menu
        self.context_menu_active = False
        self.context_menu_pos = (0, 0)
        self.context_menu_items = []
        self.context_menu_page = 0

        # Reminders and achievements
        self.reminders = []
        self.reminder_cooldowns = {}
        self.reminder_timer = 0
        self.achievement_notifications = []
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

                if event.button == 1 and ALLOW_DRAG:
                    if self.display.is_point_on_cat(*event.pos):
                        self.dragging = True
                        self.drag_offset_x = self.display.cat_x - event.pos[0]
                        self.drag_offset_y = self.display.cat_y - event.pos[1]
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
                    self.dragging = False

            if event.type == pygame.MOUSEMOTION:
                # Block mouse motion when chat is active
                if self.chat_active:
                    continue
                
                self.mouse_pos = event.pos
                self.last_mouse_pos = event.pos
                if self.dragging:
                    self.display.cat_x = event.pos[0] + self.drag_offset_x
                    self.display.cat_y = event.pos[1] + self.drag_offset_y
                    self.display.cat_x = max(self.display.min_x, min(self.display.cat_x, self.display.max_x))
                    self.display.cat_y = max(self.display.min_y, min(self.display.cat_y, self.display.max_y))
            
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
                
                # Handle toy selection if waiting
                if self.waiting_for_toy:
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
        """Open context menu near the mouse cursor."""
        self.context_menu_active = True
        self.context_menu_pos = pos
        self.context_menu_page = 0
        self.context_menu_pages = [
            [
                {"label": "Ask LARY", "icon": "🤖", "action": self.open_chat_ui},
                {"label": "Pet", "icon": "😺", "action": lambda: self.perform_action('purr', "You petted the cat!")},
                {"label": "Feed", "icon": "🍖", "action": lambda: self.perform_action('eat', "You fed the cat!")},
                {"label": "Play", "icon": "🎾", "action": self.show_toy_menu},
                {"label": "Groom", "icon": "🧼", "action": lambda: self.perform_action('groom', "You gently groomed the cat")},
                {"label": "Talk", "icon": "💬", "action": lambda: self.perform_action('talk', "You calmly talked to the cat")},
                {"label": "Train", "icon": "⭐", "action": lambda: self.perform_action('train', "You did a short training session")},
                {"label": "Sleep", "icon": "💤", "action": lambda: self.perform_action('sleep', "Cat is sleeping peacefully")},
                {"label": "Rest", "icon": "🛋️", "action": lambda: self.perform_action('rest', "Cat is resting")},
                {"label": "Stats", "icon": "📊", "action": self.toggle_stats_panel},
            ],
            [
                {"label": "Next Cat", "icon": "🔁", "action": self.next_cat},
                {"label": "New Cat", "icon": "➕", "action": self.create_new_cat},
                {"label": "Export", "icon": "⤴", "action": self.export_profile},
                {"label": "Import", "icon": "⤵", "action": self.import_profile},
                {"label": "Export All", "icon": "📦", "action": self.export_all_profiles},
                {"label": "Save", "icon": "💾", "action": lambda: self.cat.save_brain(self.save_path)},
                {"label": "Load", "icon": "📂", "action": lambda: self.cat.load_brain(self.save_path)},
                {"label": "Hibernate", "icon": "🌙", "action": self.hibernate_game},
            ]
        ]
        self.context_menu_items = self.build_radial_menu_items()

    def build_radial_menu_items(self):
        """Build current page items with navigation arrows."""
        pages = getattr(self, "context_menu_pages", [])
        if not pages:
            return []
        items = list(pages[self.context_menu_page])
        if len(pages) > 1:
            items.append({"label": "Prev", "icon": "<", "action": self.prev_menu_page, "keep_open": True})
            items.append({"label": "Next", "icon": ">", "action": self.next_menu_page, "keep_open": True})
        return items

    def next_menu_page(self):
        """Go to next radial menu page."""
        pages = getattr(self, "context_menu_pages", [])
        if not pages:
            return
        self.context_menu_page = (self.context_menu_page + 1) % len(pages)
        self.context_menu_items = self.build_radial_menu_items()

    def prev_menu_page(self):
        """Go to previous radial menu page."""
        pages = getattr(self, "context_menu_pages", [])
        if not pages:
            return
        self.context_menu_page = (self.context_menu_page - 1) % len(pages)
        self.context_menu_items = self.build_radial_menu_items()

    def handle_context_menu_click(self, pos):
        """Handle clicks on context menu items."""
        cx, cy = self.context_menu_pos
        count = len(self.context_menu_items)
        if count == 0:
            self.context_menu_active = False
            return

        # Keep within window bounds by nudging center (match draw logic)
        margin = RADIAL_MENU_RADIUS + 40
        cx = max(margin, min(self.display.window_width - margin, cx))
        cy = max(margin, min(self.display.window_height - margin, cy))

        base_angle = -math.pi / 2
        step = (2 * math.pi) / count

        for i, item in enumerate(self.context_menu_items):
            angle = base_angle + i * step
            ix = cx + math.cos(angle) * RADIAL_MENU_RADIUS
            iy = cy + math.sin(angle) * RADIAL_MENU_RADIUS
            dx = pos[0] - ix
            dy = pos[1] - iy
            if (dx * dx + dy * dy) <= (RADIAL_ITEM_RADIUS + RADIAL_HOVER_BUMP) ** 2:
                action = item.get("action")
                if action:
                    action()
                if item.get("keep_open"):
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
        """Initialize ambient sound if available."""
        if not self.sound_enabled:
            return
        try:
            pygame.mixer.init()
            if os.path.exists(AMBIENT_SOUND_PATH):
                self.ambient_sound = pygame.mixer.Sound(AMBIENT_SOUND_PATH)
                self.ambient_channel = self.ambient_sound.play(-1)
                if self.ambient_channel:
                    self.ambient_channel.set_volume(0.25)
            for key, path in SOUND_FX_PATHS.items():
                if os.path.exists(path):
                    self.sfx[key] = pygame.mixer.Sound(path)
        except Exception:
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

    def add_reminder(self, text, duration=4.0):
        """Add a short reminder message."""
        expires_at = self.game_time + duration
        self.reminders.append({'text': text, 'expires': expires_at})
        if len(self.reminders) > 3:
            self.reminders.pop(0)

    def update_reminders(self):
        """Update reminder queue and add routine reminders."""
        self.reminder_timer += 1 / FPS
        if self.reminder_timer >= 2:
            self.reminder_timer = 0
            cat_hour = (self.cat.age * 24) % 24

            def can_remind(key, cooldown=15):
                last = self.reminder_cooldowns.get(key, -999)
                return (self.game_time - last) >= cooldown

            if self.cat.hunger > 75 and can_remind('hungry'):
                self.add_reminder("Reminder: I'm hungry!")
                self.reminder_cooldowns['hungry'] = self.game_time
            if self.cat.energy < 25 and can_remind('tired'):
                self.add_reminder("Reminder: I need sleep")
                self.reminder_cooldowns['tired'] = self.game_time
            if self.cat.trust < 30 and can_remind('social'):
                self.add_reminder("Reminder: Talk or pet me")
                self.reminder_cooldowns['social'] = self.game_time

            if 7 <= cat_hour <= 9 and self.cat.hunger > 50 and can_remind('breakfast'):
                self.add_reminder("Routine: Breakfast time")
                self.reminder_cooldowns['breakfast'] = self.game_time
            if 20 <= cat_hour <= 22 and self.cat.energy < 60 and can_remind('bedtime'):
                self.add_reminder("Routine: Bedtime soon")
                self.reminder_cooldowns['bedtime'] = self.game_time

        self.reminders = [r for r in self.reminders if r['expires'] > self.game_time]

    def award_achievement(self, key, text):
        """Award an achievement to the active cat."""
        if key in self.cat.achievements:
            return
        self.cat.achievements.add(key)
        expires_at = self.game_time + 5.0
        self.achievement_notifications.append({'text': text, 'expires': expires_at})
        if len(self.achievement_notifications) > 3:
            self.achievement_notifications.pop(0)

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

        self.achievement_notifications = [a for a in self.achievement_notifications if a['expires'] > self.game_time]

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
            self.award_achievement('mini_game', 'Quick Paws')
            self.start_jump()
        else:
            self.cat.happiness = max(0, self.cat.happiness - 2)
            self.cat.learn_from_interaction('play', 'Mini-game missed', -0.1)
        self.mini_game = None

    def get_overlay_labels(self):
        """Build overlay labels for reminders, achievements, and mini-games."""
        labels = []
        y = 60
        for reminder in self.reminders:
            labels.append((reminder['text'], (180, y)))
            y += 28
        for ach in self.achievement_notifications:
            labels.append((f"Achievement: {ach['text']}", (220, y)))
            y += 28
        if self.mini_game:
            labels.append((self.mini_game['prompt'], (self.display.window_width // 2, 80)))
        return labels
    
    def perform_action(self, action, message):
        """Player performs an action with the cat."""
        print(f">>> {message}")
        self.play_sfx(action)
        
        # Determine reward based on action and cat state
        reward = self.calculate_reward(action)
        
        # Cat learns from this interaction
        self.cat.learn_from_interaction(action, message, reward)
        
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
        
        print("\n" + "="*40)
        print("Choose a toy to play with:")
        print("="*40)
        print("1) Ball 🔴 - Fast bouncing fun!")
        print("2) Fish 🐟 - Wiggly and fun!")
        print("3) Mouse 🐭 - Small and sneaky!")
        print("4) Bird 🐦 - Flying and exciting!")
        print("="*40)
        print("Press: 1, 2, 3, or 4 to select toy (ESC to cancel)")
        print("="*40 + "\n")
        
        self.waiting_for_toy = True
    
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
        
        # Calculate reward
        reward = self.calculate_reward('play')
        
        # Cat learns from this interaction
        message = f"Played with {toy['name']} {toy['emoji']}"
        self.cat.learn_from_interaction('play', message, reward)
        
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
        self.cat.learn_from_interaction(action, message, reward)
        
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
    
    def update(self):
        """Update game state."""
        # Update cat internal state
        delta_time = GAME_SPEED
        self.cat.update_state(delta_time)

        is_adult = self.cat.age >= ADULT_AGE_DAYS
        is_busy = (time.time() - self.last_input_time) >= BUSY_THRESHOLD_SECONDS

        # Age-based pacing (older cats move and act less)
        age_days = self.cat.age
        move_interval = min(12, 5 + age_days * 0.2)  # seconds
        ai_interval = min(10, 3 + age_days * 0.25)   # seconds
        self.display.cat_speed = max(0.8, 2.0 - age_days * 0.03)

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
        if is_adult and is_busy and ADULT_FIXED_SPOT:
            fixed_x, fixed_y = self.get_fixed_spot()
            self.display.target_x, self.display.target_y = fixed_x, fixed_y
            self.display.cat_speed = min(self.display.cat_speed, 1.2)
            if self.action_timer <= 0:
                if self.cat.hunger > 70:
                    self.add_reminder("Adult cat: hungry")
                    self.current_action = "talk"
                    self.action_timer = 2.5
                elif self.cat.energy < 40:
                    self.current_action = "sleep"
                    self.action_timer = 3.5 * ADULT_SLEEP_MULTIPLIER
                else:
                    self.current_action = "rest"
                    self.action_timer = 2.5 * ADULT_REST_MULTIPLIER
        
        # Young cat behavior: follow cursor and try to play
        if not is_adult and YOUNG_FOLLOW_CURSOR and self.last_mouse_pos:
            mx, my = self.last_mouse_pos
            self.display.target_x, self.display.target_y = mx, my
            if self.young_play_cooldown > 0:
                self.young_play_cooldown -= 1 / FPS
            if self.is_mouse_near_cat(self.last_mouse_pos, radius=YOUNG_PLAY_DISTANCE):
                if self.young_play_cooldown <= 0 and self.cat.energy > 40 and self.cat.hunger < 70:
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
        if self.current_action in ("idle", "walk") or self.hunt_timer > 0:
            self.is_moving = self.display.update_cat_movement()
            
            # Randomly wander
            self.movement_timer += 1 / FPS
            if self.movement_timer > move_interval and not self.is_moving and self.hunt_timer <= 0 and self.curiosity_pause <= 0 and not (is_adult and is_busy):
                self.display.move_cat_to_random_position()
                self.movement_timer = 0

        # Curiosity pause while walking
        if self.hunt_timer <= 0:
            curiosity = 0.5
            if hasattr(self.cat, "personality"):
                curiosity = self.cat.personality.get("curious", 0.5)
            self.curiosity_timer += 1 / FPS
            if self.curiosity_pause <= 0 and self.is_moving and self.curiosity_timer > 5:
                chance = 0.06 + (curiosity * 0.10)
                if random.random() < chance:
                    self.curiosity_pause = 0.8 + (curiosity * 1.2)
                    self.curiosity_timer = 0
            if self.curiosity_pause > 0:
                self.curiosity_pause -= 1 / FPS
                self.current_action = "sit"
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
        if not (is_adult and is_busy):
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
                context_menu = {"pos": self.context_menu_pos, "items": self.context_menu_items, "mouse_pos": self.mouse_pos}
            overlay_labels = self.get_overlay_labels()
            visual_state = {
                "toy": self.toy_visual,
                "food_level": self.food_level,
                "curious": self.curiosity_pause > 0,
                "jump_progress": self.jump_progress,
                "show_stats": self.show_stats_panel,
                "chat_active": self.chat_active,
                "chat_response": self.chat_response,
                "chat_input": self.chat_input_text,
                "chat_waiting": self.chat_waiting_for_response
            }
            self.display.render(cat_status, self.current_action, self.waiting_for_toy, context_menu, overlay_labels, visual_state)
            
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
