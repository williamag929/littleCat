"""
arcade.py - the cat's little arcade (roadmap 2.8 / 2.9), without pygame.

Two modes on the built-in Pong:
  * "cat"  ("Watch me play")  the cat plays. Its aim gets better with practice
           (games played) and, once it has watched you, it plays like you.
  * "you"  ("Teach me")       you play with the arrow keys; every decision you
           make is recorded and, at game over, the cat learns your style.

The session only produces events ("hit", "miss", "record", "game_over"...);
game.py turns them into speech, poses and memories.
"""

from __future__ import annotations

import random
from typing import List, Optional

try:
    from .minigames.pong import Pong
    from .screen_agent.policy import ImitationPolicy, PredictivePolicy
    from .screen_agent.state import Observation, StateTracker
except ImportError:  # running from src/
    from minigames.pong import Pong
    from screen_agent.policy import ImitationPolicy, PredictivePolicy
    from screen_agent.state import Observation, StateTracker

LIVES = 3
GAMES_TO_LEARN = 3        # recorded games before "plays like you" kicks in


def cat_aim_error(games_played: int) -> float:
    """Aiming mistake (fraction of paddle width): sloppy kitten -> decent player."""
    return max(0.18, 0.75 - 0.07 * games_played)


class ArcadeSession:
    def __init__(self, mode: str, games_played: int = 0, imitation: Optional[ImitationPolicy] = None,
                 best_ever: int = 0, rng: Optional[random.Random] = None, seed: Optional[int] = None):
        assert mode in ("cat", "you")
        self.mode = mode
        self.rng = rng or random.Random(seed)
        self.pong = Pong(seed=self.rng.randrange(1 << 30))
        self.tracker = StateTracker()
        self.imitation = imitation
        self.best_ever = best_ever
        self.over = False
        self.time = 0.0
        self.new_record = False
        self.style = "own"
        self.policy = None
        if mode == "cat":
            if imitation is not None and imitation.trained and imitation.games_recorded >= GAMES_TO_LEARN:
                self.policy, self.style = imitation, "yours"
            else:
                self.policy = PredictivePolicy(error=cat_aim_error(games_played), rng=self.rng)
        self.last_action = 0

    @property
    def lives(self) -> int:
        return max(0, LIVES - self.pong.misses)

    def _tracked(self):
        st = self.pong.state()
        ball = None if st["serving"] else (st["ball_x"], st["ball_y"])
        obs = Observation(ball, st["paddle_x"], st["width"], st["height"], st["paddle_y"],
                          st["paddle_w"], st["ball"])
        return obs

    def step(self, dt: float, player_action: int = 0) -> List[str]:
        if self.over:
            return []
        self.time += dt
        s = self.tracker.update(self._tracked(), dt)
        if self.mode == "cat":
            action = self.policy.act(s) if s is not None else 0
        else:
            action = player_action
            if s is not None and self.imitation is not None:
                self.imitation.record(s, action)
        self.last_action = action
        events = [e for e in self.pong.step(dt, action) if e in ("hit", "miss")]
        if "hit" in events and self.pong.rally > self.best_ever and self.pong.rally >= 3 and not self.new_record:
            self.new_record = True
            events.append("record")
        if self.pong.misses >= LIVES:
            self.over = True
            events.append("game_over")
            if self.mode == "you" and self.imitation is not None:
                self.imitation.games_recorded += 1
                self.imitation.train()
                events.append("learned")
        return events

    def summary(self) -> dict:
        p = self.pong
        return {"mode": self.mode, "hits": p.hits, "misses": p.misses, "best_rally": p.best_rally,
                "hit_rate": round(p.hit_rate(), 2), "style": self.style,
                "seconds": round(self.time, 1), "new_record": self.new_record}

    def reward(self) -> float:
        """How the game felt (-1..1): rallies feel great, losing quickly feels meh (never awful)."""
        return max(-0.3, min(1.0, (self.pong.hits - 2) / 8.0))
