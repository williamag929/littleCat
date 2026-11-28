"""
agent.py - the screen agent loop: capture -> perceive -> track -> decide -> press.

    agent = ScreenAgent(load_profile("littlecat_pong"))
    agent.run(seconds=60)

It only ever runs because you started it (menu or command line), stops with
Ctrl+Alt+P, when the game window closes, or after `seconds`.
"""

from __future__ import annotations

import json
import os
import time
from typing import Callable, Optional

from .actuator import KeyActuator
from .perception import Detector
from .policy import ChaseBallPolicy, ImitationPolicy, PredictivePolicy
from .state import StateTracker

PROFILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")

DEFAULT_PROFILE = {
    "name": "custom", "window_title": "", "region": None, "keys": ["left", "right"],
    "bottom_band": 0.18, "tolerance": 40, "downsample": "auto", "ball_color": None,
    "paddle_color": None, "policy": "predict", "error": 0.0,
}


def list_profiles():
    if not os.path.isdir(PROFILES_DIR):
        return []
    return sorted(f[:-5] for f in os.listdir(PROFILES_DIR) if f.endswith(".json"))


def load_profile(name_or_path: str) -> dict:
    path = name_or_path if os.path.exists(name_or_path) else os.path.join(PROFILES_DIR, f"{name_or_path}.json")
    with open(path, "r", encoding="utf-8-sig") as f:   # -sig: profiles edited in Notepad may have a BOM
        data = json.load(f)
    return {**DEFAULT_PROFILE, **data}


def profile_from_poc(calibration: dict) -> dict:
    """The old screen_agent_poc calibration (data/screen_agent.json) as a profile."""
    r = calibration["region"]
    bgr = lambda c: [c["r"], c["g"], c["b"]]  # noqa: E731 - POC stored BGR
    cfg = calibration.get("config", {})
    keys = cfg.get("move_key", ["left", "right"])
    return {**DEFAULT_PROFILE, "name": "poc calibration",
            "region": [r["left"], r["top"], r["width"], r["height"]],
            "ball_color": bgr(calibration["ball_color"]), "paddle_color": bgr(calibration["paddle_color"]),
            "tolerance": cfg.get("tolerance", 30), "keys": list(keys), "downsample": 1}


def make_policy(profile: dict, imitation_path: Optional[str] = None):
    kind = profile.get("policy", "predict")
    if kind == "chase":
        return ChaseBallPolicy()
    if kind == "imitation" and imitation_path:
        p = ImitationPolicy.load(imitation_path)
        if p.trained:
            return p
    return PredictivePolicy(error=float(profile.get("error", 0.0)))


class ScreenAgent:
    def __init__(self, profile: dict, policy=None, log: Callable[[str], None] = print):
        self.profile = profile
        self.policy = policy or make_policy(profile)
        self.log = log
        self.detector = Detector(bottom_band=profile["bottom_band"], tolerance=profile["tolerance"],
                                 downsample=profile["downsample"], ball_color=profile["ball_color"],
                                 paddle_color=profile["paddle_color"])
        self.tracker = StateTracker()
        self.hwnd = 0
        self.region = None

    def locate(self) -> bool:
        """Find the game: window title (follows the window) or a fixed region."""
        from desktop import client_rect, find_window  # windows-only helpers
        title = self.profile.get("window_title")
        if title:
            for _ in range(20):                 # the game may still be opening: wait up to ~5 s
                self.hwnd = find_window(title)
                if self.hwnd:
                    break
                time.sleep(0.25)
            if not self.hwnd:
                self.log(f"Game window '{title}' not found - open the game first.")
                return False
            l, t, r, b = client_rect(self.hwnd)
            self.region = (l, t, r - l, b - t)
        elif self.profile.get("region"):
            self.region = tuple(self.profile["region"])
        else:
            self.log("Profile needs 'window_title' or 'region'.")
            return False
        return True

    def run(self, seconds: float = 120.0, dry_run: bool = False, fps: float = 30.0,
            countdown: float = 3.0) -> dict:
        from .capture import ScreenCapture
        if not self.locate():
            return {"ok": False}
        act = KeyActuator(tuple(self.profile["keys"]), target_hwnd=self.hwnd)
        if countdown and not dry_run:
            self.log(f"Starting in {countdown:.0f}s - click the game window. Ctrl+Alt+P stops me.")
            time.sleep(countdown)
        start = last = time.perf_counter()
        frames = seen = 0
        with ScreenCapture(self.region) as cap:
            try:
                while time.perf_counter() - start < seconds:
                    now = time.perf_counter()
                    dt, last = now - last, now
                    frame = cap.grab()
                    if frame is None:
                        break
                    obs = self.detector.observe(frame)
                    s = self.tracker.update(obs, dt)
                    frames += 1
                    if s is not None and s.visible:
                        seen += 1
                    action = self.policy.act(s) if s is not None else 0
                    if dry_run:
                        if frames % 15 == 0:
                            self.log(f"ball={obs.ball} paddle_x={obs.paddle_x} action={action:+d}")
                    elif not act.apply(action):
                        self.log(f"Stopped: {act.stop_reason}")
                        break
                    if self.hwnd:
                        from desktop import window_rect
                        if window_rect(self.hwnd) is None:
                            self.log("Game window closed.")
                            break
                    time.sleep(max(0.0, 1.0 / fps - (time.perf_counter() - now)))
            finally:
                act.release_all()
        result = {"ok": True, "frames": frames, "ball_seen": round(seen / max(1, frames), 2),
                  "hits": self.tracker.hits, "misses": self.tracker.misses,
                  "fps": round(frames / max(1e-6, time.perf_counter() - start), 1)}
        self.log(f"Done: {result}")
        return result
