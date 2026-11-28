"""
bench.py - measure a policy on the built-in Pong, headless.

    python -m screen_agent.bench            (from src/)
    python src/screen_agent/bench.py

Two ways to see the game:
  * "state":  exact positions (tests the policy alone)
  * "pixels": rendered frames -> Detector (tests perception + policy, like on screen)
Both go through StateTracker, so velocity is always *estimated*, never given.
"""

from __future__ import annotations

import os
import random
import sys
import time

if __package__ in (None, ""):  # allow `python src/screen_agent/bench.py`
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "screen_agent"

from minigames.pong import Pong  # noqa: E402
from .perception import Detector  # noqa: E402
from .policy import ChaseBallPolicy, PredictivePolicy  # noqa: E402
from .state import Observation, StateTracker  # noqa: E402

FPS = 60


def run(policy, attempts: int = 300, mode: str = "state", seed: int = 1, recorder=None,
        frame_skip: int = 2, latency: int = 3) -> dict:
    """Play until hits+misses == attempts. Returns hit rate and stats.

    Defaults mimic a real screen agent: it sees every 2nd frame (30 fps capture)
    and its key presses land 3 frames (50 ms) late.
    """
    from collections import deque
    pending = deque([0] * latency)
    game = Pong(seed=seed)
    tracker = StateTracker()
    detector = Detector(downsample=1) if mode == "pixels" else None
    dt = 1 / FPS
    action = 0
    steps = 0
    t0 = time.perf_counter()
    while game.hits + game.misses < attempts and steps < attempts * 2000:
        if steps % frame_skip == 0:
            if detector:
                obs = detector.observe(game.render_array())
            else:
                st = game.state()
                ball = None if st["serving"] else (st["ball_x"], st["ball_y"])
                obs = Observation(ball, st["paddle_x"], st["width"], st["height"], st["paddle_y"],
                                  st["paddle_w"], st["ball"])
            s = tracker.update(obs, dt * frame_skip)
            if s is not None:
                action = policy.act(s)
                if recorder is not None:
                    recorder(s, action)
        pending.append(action)
        game.step(dt, pending.popleft())
        steps += 1
    return {"policy": getattr(policy, "name", type(policy).__name__), "mode": mode,
            "hit_rate": round(game.hit_rate(), 3), "hits": game.hits, "misses": game.misses,
            "best_rally": game.best_rally, "seconds": round(time.perf_counter() - t0, 2),
            "tracker_hits": tracker.hits, "tracker_misses": tracker.misses}


def main():
    for mode, n in (("state", 1000), ("pixels", 60)):
        for policy in (ChaseBallPolicy(), PredictivePolicy(), PredictivePolicy(error=0.6, rng=random.Random(2))):
            r = run(policy, attempts=n, mode=mode)
            label = r["policy"] + (" (error 0.6)" if getattr(policy, "error", 0) else "")
            print(f"{mode:6s} {label:22s} hit rate {r['hit_rate'] * 100:5.1f}%  "
                  f"({r['hits']}/{r['hits'] + r['misses']}, best rally {r['best_rally']}, {r['seconds']}s)")


if __name__ == "__main__":
    main()
