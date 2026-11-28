"""
pong.py - a tiny one-player "wall pong" (paddle at the bottom, walls elsewhere).

Two jobs:
  1. Benchmark for the screen agent: the game state is known exactly, so we
     can measure how often a policy returns the ball, headless and fast.
  2. The cat's arcade: drawn on the overlay, the cat plays it ("Watch me
     play") or watches you play it and learns your style ("Teach me").

The logic has no pygame dependency. `render()` draws onto a pygame surface
when one is given (pygame is imported lazily).

Run it standalone to play with the arrow keys:
    python src/minigames/pong.py
"""

from __future__ import annotations

import math
import random
from typing import List, Optional

W, H = 320, 240
PADDLE_W, PADDLE_H = 48, 6
PADDLE_Y = H - 18            # top of the paddle
BALL = 6                     # ball size (square)
PADDLE_SPEED = 160.0         # px/s (tuned with screen_agent/bench.py: a real challenge)
BALL_SPEED_START = 190.0
BALL_SPEED_MAX = 420.0
SPEED_UP = 1.06              # per return: rallies get exciting fast

# Palette used by render() and by the screen agent's colour profile
COLORS = {
    "bg": (28, 30, 46),
    "wall": (70, 74, 110),
    "ball": (255, 214, 102),
    "paddle": (247, 160, 72),
    "text": (235, 225, 215),
}


class Pong:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.paddle_x = W / 2
        self.hits = 0
        self.misses = 0
        self.rally = 0
        self.best_rally = 0
        self.serve_delay = 0.0
        self.t = 0.0
        self.serve()

    # ------------------------------------------------------------------ rules
    def serve(self):
        self.ball_x = self.rng.uniform(40, W - 40)
        self.ball_y = 30.0
        angle = math.radians(self.rng.uniform(25, 65)) * self.rng.choice((-1, 1))
        self.speed = BALL_SPEED_START
        self.vx = self.speed * math.sin(angle)
        self.vy = self.speed * math.cos(angle)       # downwards
        self.rally = 0
        self.serve_delay = 0.6

    def step(self, dt: float, action: int) -> List[str]:
        """Advance the game. action: -1 left, 0 stay, +1 right. Returns events."""
        events: List[str] = []
        self.t += dt
        self.paddle_x += max(-1, min(1, int(action))) * PADDLE_SPEED * dt
        self.paddle_x = min(max(self.paddle_x, PADDLE_W / 2), W - PADDLE_W / 2)
        if self.serve_delay > 0:
            self.serve_delay -= dt
            return events

        r = BALL / 2
        prev_y = self.ball_y
        self.ball_x += self.vx * dt
        self.ball_y += self.vy * dt
        if self.ball_x < r:
            self.ball_x, self.vx = 2 * r - self.ball_x, abs(self.vx)
            events.append("wall")
        elif self.ball_x > W - r:
            self.ball_x, self.vx = 2 * (W - r) - self.ball_x, -abs(self.vx)
            events.append("wall")
        if self.ball_y < r:
            self.ball_y, self.vy = 2 * r - self.ball_y, abs(self.vy)
            events.append("wall")

        # Paddle: ball crossing the paddle line while falling
        line = PADDLE_Y - r
        if self.vy > 0 and prev_y <= line <= self.ball_y:
            off = self.ball_x - self.paddle_x
            if abs(off) <= PADDLE_W / 2 + r:
                self.ball_y = line - (self.ball_y - line)
                self.speed = min(BALL_SPEED_MAX, self.speed * SPEED_UP)
                # "english": hitting with the paddle's edge angles the ball
                ang = max(-1.0, min(1.0, off / (PADDLE_W / 2))) * math.radians(55)
                self.vx = self.speed * math.sin(ang)
                self.vy = -self.speed * math.cos(ang)
                self.hits += 1
                self.rally += 1
                self.best_rally = max(self.best_rally, self.rally)
                events.append("hit")
        if self.ball_y > H + BALL:
            self.misses += 1
            events.append("miss")
            self.serve()
        return events

    def state(self) -> dict:
        return {"ball_x": self.ball_x, "ball_y": self.ball_y, "vx": self.vx, "vy": self.vy,
                "paddle_x": self.paddle_x, "paddle_y": PADDLE_Y, "paddle_w": PADDLE_W,
                "width": W, "height": H, "ball": BALL, "serving": self.serve_delay > 0}

    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    # ----------------------------------------------------------------- render
    def render_array(self):
        """The board as an HxWx3 uint8 RGB array (numpy, no pygame) - what a screen capture would see."""
        import numpy as np
        img = np.empty((H, W, 3), dtype=np.uint8)
        img[:] = COLORS["bg"]
        img[:3, :] = img[-3:, :] = img[:, :3] = img[:, -3:] = COLORS["wall"]
        x0 = int(self.paddle_x - PADDLE_W / 2)
        img[PADDLE_Y:PADDLE_Y + PADDLE_H, max(0, x0):x0 + PADDLE_W] = COLORS["paddle"]
        if self.serve_delay <= 0 or int(self.serve_delay * 8) % 2 == 0:
            bx, by = int(self.ball_x - BALL / 2), int(self.ball_y - BALL / 2)
            if by < H:
                img[max(0, by):by + BALL, max(0, bx):bx + BALL] = COLORS["ball"]
        # the rally counter as a little block that changes (like a score would)
        digits = min(9, self.rally)
        img[8:14, W // 2 - 20: W // 2 - 20 + 4 * digits] = COLORS["text"]
        return img

    def render(self, surface, rect=None, font=None):
        """Draw the board into `rect` of a pygame surface (scaled to fit)."""
        import pygame
        if rect is None:
            rect = surface.get_rect()
        board = pygame.Surface((W, H))
        board.fill(COLORS["bg"])
        pygame.draw.rect(board, COLORS["wall"], (0, 0, W, H), 3)
        pygame.draw.rect(board, COLORS["paddle"],
                         (int(self.paddle_x - PADDLE_W / 2), PADDLE_Y, PADDLE_W, PADDLE_H), border_radius=3)
        if self.serve_delay <= 0 or int(self.serve_delay * 8) % 2 == 0:
            pygame.draw.rect(board, COLORS["ball"],
                             (int(self.ball_x - BALL / 2), int(self.ball_y - BALL / 2), BALL, BALL))
        if font is not None:
            txt = font.render(f"{self.rally}", True, COLORS["text"])
            board.blit(txt, txt.get_rect(midtop=(W // 2, 8)))
        if rect.size != (W, H):
            board = pygame.transform.scale(board, rect.size)
        surface.blit(board, rect.topleft)


def main():  # pragma: no cover - interactive
    import sys
    import time
    import pygame
    seconds = float(sys.argv[sys.argv.index("--seconds") + 1]) if "--seconds" in sys.argv else None
    started = time.time()
    pygame.init()
    screen = pygame.display.set_mode((W * 2, H * 2))
    pygame.display.set_caption("LittleCat Pong")
    font = pygame.font.Font(None, 28)
    clock = pygame.time.Clock()
    game = Pong()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
        if seconds and time.time() - started > seconds:
            running = False
        keys = pygame.key.get_pressed()
        action = (1 if keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_LEFT] else 0)
        game.step(1 / 60, action)
        game.render(screen, font=font)
        pygame.display.flip()
        clock.tick(60)
    print(f"hits {game.hits}  misses {game.misses}  best rally {game.best_rally}")
    pygame.quit()


if __name__ == "__main__":
    main()
