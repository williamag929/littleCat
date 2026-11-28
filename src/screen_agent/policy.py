"""
policy.py - how the paddle decides where to go.

* ChaseBallPolicy     the old prototype: follow the ball's current x
* PredictivePolicy    simulate the ball (with wall bounces) to where it will
                      cross the paddle line and wait there; `error` adds a
                      human-like aiming mistake so the cat can miss sometimes
* ImitationPolicy     learns YOUR style from recorded (state, key) pairs with
                      a small softmax regression (numpy only)
"""

from __future__ import annotations

import json
import math
import os
import random
from typing import List, Optional, Sequence, Tuple

import numpy as np

from .state import TrackedState

LEFT, STAY, RIGHT = -1, 0, 1


def fold(x: float, lo: float, hi: float) -> float:
    """Reflect x into [lo, hi] as a ball bouncing between two walls would."""
    span = hi - lo
    if span <= 0:
        return lo
    m = (x - lo) % (2 * span)
    return lo + (m if m <= span else 2 * span - m)


def predict_landing_x(s: TrackedState) -> Optional[float]:
    """Where the ball will cross the paddle line (None if it can't be predicted)."""
    r = s.ball_size / 2
    line = s.paddle_y - r
    if abs(s.vy) < 1:
        return None
    if s.vy > 0:
        t = (line - s.ball_y) / s.vy
    else:  # going up: travel to the top wall and back down
        t = (s.ball_y - r) / -s.vy + (line - r) / -s.vy
    if t < 0:
        return None
    return fold(s.ball_x + s.vx * t, r, s.width - r)


def steer(target: float, paddle_x: float, deadzone: float) -> int:
    diff = target - paddle_x
    if abs(diff) <= deadzone:
        return STAY
    return RIGHT if diff > 0 else LEFT


class ChaseBallPolicy:
    name = "chase"

    def __init__(self, deadzone: float = 6.0):
        self.deadzone = deadzone

    def act(self, s: TrackedState) -> int:
        if not s.visible:
            return STAY
        return steer(s.ball_x, s.paddle_x, self.deadzone)


class PredictivePolicy:
    name = "predict"

    def __init__(self, error: float = 0.0, deadzone: float = 4.0, rng: Optional[random.Random] = None):
        """error: std-dev of the aiming mistake as a fraction of the paddle width."""
        self.error = error
        self.deadzone = deadzone
        self.rng = rng or random.Random()
        self._falling = False
        self._mistake = 0.0

    def act(self, s: TrackedState) -> int:
        if not s.visible:
            return steer(s.width / 2, s.paddle_x, self.deadzone * 3)
        falling = s.vy > 0
        if falling and not self._falling:          # new approach: decide how sloppy this one is
            self._mistake = self.rng.gauss(0, self.error * s.paddle_w) if self.error else 0.0
        self._falling = falling
        target = predict_landing_x(s)
        if target is None:
            return steer(s.ball_x, s.paddle_x, self.deadzone)
        if not falling:                               # ball going away: drift to where it'll come back
            target = 0.5 * target + 0.5 * s.width / 2
        return steer(target + self._mistake, s.paddle_x, self.deadzone)


# ---------------------------------------------------------------- imitation
def features(s: TrackedState) -> np.ndarray:
    """Small, game-size independent description of the situation."""
    pred = predict_landing_x(s)
    pred = s.ball_x if pred is None else pred
    w = max(1.0, s.width)
    return np.array([
        (pred - s.paddle_x) / w,
        (s.ball_x - s.paddle_x) / w,
        1.0 if s.vy > 0 else -1.0,
        s.ball_y / max(1.0, s.height),
        (s.paddle_x - w / 2) / w,
        1.0,
    ], dtype=np.float64)


class ImitationPolicy:
    """Softmax regression over 3 actions, trained on your recorded play."""
    name = "imitation"
    ACTIONS = (LEFT, STAY, RIGHT)

    def __init__(self, max_samples: int = 20000):
        self.X: List[np.ndarray] = []
        self.y: List[int] = []
        self.max_samples = max_samples
        self.W: Optional[np.ndarray] = None
        self.games_recorded = 0

    def record(self, s: TrackedState, action: int):
        if not s.visible:
            return
        self.X.append(features(s))
        self.y.append(self.ACTIONS.index(action))
        if len(self.X) > self.max_samples:
            self.X = self.X[-self.max_samples:]
            self.y = self.y[-self.max_samples:]

    @property
    def trained(self) -> bool:
        return self.W is not None

    def train(self, epochs: int = 300, lr: float = 0.5, l2: float = 1e-3) -> float:
        """Fit the weights. Returns training accuracy."""
        if len(self.X) < 50:
            return 0.0
        X = np.stack(self.X)
        Y = np.eye(3)[np.array(self.y)]
        # balance the classes: people mostly "stay", but moving is what matters
        counts = Y.sum(axis=0) + 1.0
        weights = (Y / counts).sum(axis=1) * len(Y) / 3.0
        W = np.zeros((X.shape[1], 3)) if self.W is None or self.W.shape[0] != X.shape[1] else self.W.copy()
        for _ in range(epochs):
            logits = X @ W
            logits -= logits.max(axis=1, keepdims=True)
            P = np.exp(logits)
            P /= P.sum(axis=1, keepdims=True)
            grad = X.T @ ((P - Y) * weights[:, None]) / len(X) + l2 * W
            W -= lr * grad
        self.W = W
        return float(((X @ W).argmax(axis=1) == np.array(self.y)).mean())

    def act(self, s: TrackedState) -> int:
        if self.W is None or not s.visible:
            return STAY
        return self.ACTIONS[int((features(s) @ self.W).argmax())]

    # persistence --------------------------------------------------------
    def to_dict(self) -> dict:
        return {"schema": "littlecat.imitation/v1", "games_recorded": self.games_recorded,
                "W": self.W.tolist() if self.W is not None else None,
                "samples": len(self.X)}

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f)

    @classmethod
    def load(cls, path: str) -> "ImitationPolicy":
        p = cls()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("W") is not None:
                    p.W = np.array(data["W"], dtype=np.float64)
                p.games_recorded = int(data.get("games_recorded", 0))
            except Exception:
                pass
        return p
