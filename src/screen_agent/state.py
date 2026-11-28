"""
state.py - turns noisy positions over time into a game state the policy can use:
ball velocity (least squares over the last frames), hits, misses and rewards.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List, Optional, Tuple


@dataclass
class Observation:
    ball: Optional[Tuple[float, float]]      # centre, in board pixels (None = not seen)
    paddle_x: Optional[float]
    width: float
    height: float
    paddle_y: float                          # y of the paddle's top edge
    paddle_w: float = 48.0
    ball_size: float = 6.0


@dataclass
class TrackedState:
    ball_x: float
    ball_y: float
    vx: float
    vy: float
    paddle_x: float
    width: float
    height: float
    paddle_y: float
    paddle_w: float
    ball_size: float
    visible: bool = True
    events: List[str] = field(default_factory=list)


class StateTracker:
    """Velocity estimate + game events (hit / miss) from observations."""

    def __init__(self, history: int = 5):
        self.trail: Deque[Tuple[float, float, float]] = deque(maxlen=history)
        self.t = 0.0
        self.last_vy = 0.0
        self.lost_for = 0.0
        self.hits = 0
        self.misses = 0
        self.paddle_x: Optional[float] = None

    def reset_trail(self):
        self.trail.clear()

    def update(self, obs: Observation, dt: float) -> Optional[TrackedState]:
        self.t += dt
        events: List[str] = []
        if obs.paddle_x is not None:
            self.paddle_x = obs.paddle_x
        if obs.ball is None:
            self.lost_for += dt
            # The ball vanished while falling near the bottom: that was a miss
            if self.trail and self.lost_for > 0.15:
                _t, _x, y = self.trail[-1]
                if self.last_vy > 0 and y > obs.paddle_y - 4 * obs.ball_size:
                    self.misses += 1
                    events.append("miss")
                self.trail.clear()
            return None if self.paddle_x is None else TrackedState(
                obs.width / 2, obs.height / 2, 0.0, 0.0, self.paddle_x, obs.width, obs.height,
                obs.paddle_y, obs.paddle_w, obs.ball_size, visible=False, events=events)

        x, y = obs.ball
        # A jump much bigger than the ball can travel = a new serve: start over
        if self.trail:
            _t0, px, py = self.trail[-1]
            if abs(x - px) > obs.width * 0.35 or abs(y - py) > obs.height * 0.35:
                if self.last_vy > 0 and py > obs.paddle_y - 4 * obs.ball_size:
                    self.misses += 1
                    events.append("miss")
                self.trail.clear()
        self.lost_for = 0.0
        self.trail.append((self.t, x, y))
        vx, vy = self._velocity()
        # Ball turned from falling to rising just above the paddle: a hit
        if self.last_vy > 0 and vy < 0 and y > obs.paddle_y - obs.height * 0.3:
            self.hits += 1
            events.append("hit")
            # forget the pre-bounce points so the new velocity is clean
            self.trail.clear()
            self.trail.append((self.t, x, y))
        elif vy and self.last_vy and (vy > 0) != (self.last_vy > 0):
            # bounced off the top wall: keep only post-bounce points
            self.trail.clear()
            self.trail.append((self.t, x, y))
        if abs(vy) > 1:
            self.last_vy = vy
        if self.paddle_x is None:
            return None
        return TrackedState(x, y, vx, vy, self.paddle_x, obs.width, obs.height, obs.paddle_y,
                            obs.paddle_w, obs.ball_size, True, events)

    def _velocity(self) -> Tuple[float, float]:
        """Least-squares slope of x(t) and y(t) over the trail (robust to pixel jitter)."""
        n = len(self.trail)
        if n < 2:
            return 0.0, 0.0
        ts = [p[0] for p in self.trail]
        mt = sum(ts) / n
        den = sum((t - mt) ** 2 for t in ts)
        if den <= 1e-9:
            return 0.0, 0.0
        vx = sum((t - mt) * p[1] for t, p in zip(ts, self.trail)) / den
        vy = sum((t - mt) * p[2] for t, p in zip(ts, self.trail)) / den
        # Side wall bounces inside the window bend the line: trust the last two points for x then
        if n >= 3:
            (t1, x1, _), (t2, x2, _) = self.trail[-2], self.trail[-1]
            last_vx = (x2 - x1) / max(1e-6, t2 - t1)
            if (last_vx > 0) != (vx > 0):
                vx = last_vx
                self.trail = deque(list(self.trail)[-2:], maxlen=self.trail.maxlen)
        return vx, vy
