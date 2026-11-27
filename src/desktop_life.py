"""
desktop_life.py - The cat lives on your real desktop (roadmap phase 1).

* perch:  climbs onto the title bar of a window, rides along when you move it,
          tumbles down (gently) when the window closes or gets covered
* throw:  drag and fling the cat; it flies with gravity, bounces off the screen
          edges and lands on the taskbar or on a window it falls onto
* chase:  a fast cursor nearby is prey (oneko style); it gives up when tired,
          and never sits on top of the cursor
* gifts:  once or twice a day a happy cat leaves a little gift with a memory

No pygame in here: positions are overlay pixels (the cat's sprite centre), the
OS access goes through a `provider` (the `desktop` module, or a fake in tests),
and the game reads `events` to make the cat talk.
"""

from __future__ import annotations

import json
import math
import os
import random
import time
from datetime import date
from typing import List, Optional, Tuple

try:
    from . import desktop as _desktop
    from . import autonomy
except ImportError:  # run as a script from src/
    import desktop as _desktop
    import autonomy

FEET = 44            # px from sprite centre to the paws (32px sprite x3)
GRAVITY = 2200.0     # px/s^2
THROW_MIN_SPEED = 650.0
THROW_MAX_SPEED = 2600.0
HOP_TIME = 0.5
CHASE_KEEP_AWAY = 78     # stop this far from the cursor (sprite half-width + margin)
CHASE_MAX_TIME = 6.0
CHASE_COOLDOWN = 120.0   # a playful moment, not a distraction while you work
PERCH_COOLDOWN = 90.0
PERCH_CHECK_EVERY = 8.0
APPROACH_TIMEOUT = 10.0
GIFT_LIFETIME = 180.0
GIFT_MIN_GAP = 90 * 60
GIFT_KINDS = ("feather", "flower", "paperfish")


class DesktopLife:
    def __init__(self, size: Tuple[int, int], provider=_desktop, overlay_hwnd: int = 0,
                 settings: Optional[dict] = None, gifts_path: Optional[str] = None,
                 rng: Optional[random.Random] = None, clock=time.time):
        self.w, self.h = size
        self.p = provider
        self.hwnd = overlay_hwnd
        self.rng = rng or random.Random()
        self.clock = clock
        s = settings or {}
        self.perch_enabled = s.get("perch", True)
        self.chase_enabled = s.get("chase", True)
        self.throw_enabled = s.get("throw", True)
        self.gifts_enabled = s.get("gifts", True)
        self.gifts_per_day = int(s.get("gifts_per_day", 2))
        self.gifts_path = gifts_path

        self.origin = self.p.client_origin(overlay_hwnd) if overlay_hwnd else (0, 0)
        self.mode = "free"          # free | approach | hop | perched | airborne | chase
        self.events: List[str] = []
        self.windows = []
        self.spots = []
        self.monitors = []
        self.refresh_timer = 0.0

        # physics / hop
        self.vx = self.vy = 0.0
        self.bonked = False
        self.ignore_hwnd = None
        self.hop_from = self.hop_to = (0.0, 0.0)
        self.hop_t = 0.0
        self.drag_trail: List[Tuple[float, float, float]] = []

        # perch
        self.perch = None           # {'hwnd','x1','x2','y'} in overlay coords
        self.perch_rect = None      # last screen rect of the perch window
        self.perch_moved = (0, 0)
        self.perch_timer = 0.0
        self.perch_cooldown = 20.0
        self.perch_check = 3.0
        self.approach_target = None
        self.approach_timer = 0.0

        # cursor
        self.cursor = None
        self.cursor_speed = 0.0
        self.cursor_still = 0.0
        self.chase_timer = 0.0
        self.chase_cooldown = 10.0

        # gifts
        self.gift = None            # {'kind','x','y','ttl'}
        self.gift_check = 60.0
        self.session_start = self.clock()
        self.gift_log = self._load_gifts()
        self.refresh(force=True)

    # ------------------------------------------------------------------ coords
    def to_local(self, x, y):
        return x - self.origin[0], y - self.origin[1]

    def floor_y(self, x) -> float:
        """Sprite-centre y when standing on the taskbar of the monitor under x."""
        sx = x + self.origin[0]
        floor = _desktop.floor_y_at(self.monitors, sx, self.h + self.origin[1])
        return floor - self.origin[1] - FEET

    # ----------------------------------------------------------------- sensing
    def refresh(self, force=False, dt=0.0):
        self.refresh_timer -= dt
        if not force and self.refresh_timer > 0:
            return
        self.refresh_timer = 0.5
        try:
            self.monitors = self.p.monitors()
            self.windows = self.p.list_windows(exclude=(self.hwnd,))
            vs = (self.origin[0], self.origin[1], self.origin[0] + self.w, self.origin[1] + self.h)
            self.spots = [{"hwnd": s["hwnd"], "x1": s["x1"] - self.origin[0], "x2": s["x2"] - self.origin[0],
                           "y": s["y"] - self.origin[1]}
                          for s in _desktop.perch_spots(self.windows, vs)]
        except Exception:
            self.windows, self.spots = [], []

    def sense_cursor(self, dt):
        pos = self.p.cursor_pos()
        if pos is None:
            self.cursor = None
            return
        local = self.to_local(*pos)
        if self.cursor is not None and dt > 0:
            moved = math.hypot(local[0] - self.cursor[0], local[1] - self.cursor[1])
            self.cursor_speed = 0.7 * self.cursor_speed + 0.3 * (moved / dt)
            self.cursor_still = self.cursor_still + dt if moved < 2 else 0.0
        self.cursor = local

    # ------------------------------------------------------------------- drag
    def grab(self):
        """The player picked the cat up: whatever it was doing on the desktop stops."""
        self.mode = "free"
        self.perch = None
        self.drag_trail.clear()

    def track_drag(self, x, y):
        now = self.clock()
        self.drag_trail.append((now, x, y))
        self.drag_trail = [p for p in self.drag_trail if now - p[0] <= 0.12]

    def release(self, x, y) -> str:
        """Let go of the cat. Returns 'thrown', 'perched' or 'set_down'."""
        vx = vy = 0.0
        if len(self.drag_trail) >= 2:
            t0, x0, y0 = self.drag_trail[0]
            t1, x1, y1 = self.drag_trail[-1]
            if t1 - t0 > 0.005:
                vx, vy = (x1 - x0) / (t1 - t0), (y1 - y0) / (t1 - t0)
        self.drag_trail.clear()
        speed = math.hypot(vx, vy)
        if self.throw_enabled and speed >= THROW_MIN_SPEED:
            k = min(1.0, THROW_MAX_SPEED / speed)
            self.launch(vx * k, vy * k)
            self.events.append("thrown")
            return "thrown"
        # Gently placed right on top of a window? Then it sits there.
        spot = _desktop.spot_at(self.spots, x, y + FEET - 30, y + FEET + 30, margin=10)
        if spot and self.perch_enabled:
            self._settle_on(spot, x)
            return "perched"
        return "set_down"

    def launch(self, vx, vy, ignore_hwnd=None):
        self.mode = "airborne"
        self.perch = None
        self.vx, self.vy = vx, vy
        self.bonked = False
        # don't land straight back on the window the cat just jumped off
        self.ignore_hwnd = ignore_hwnd

    def drop(self, reason="perch_fall"):
        """Start falling from where the cat is (window closed, covered...)."""
        self.launch(self.rng.uniform(-60, 60), -120)
        self.events.append(reason)
        self.perch_cooldown = PERCH_COOLDOWN

    # ------------------------------------------------------------------ perch
    def _settle_on(self, spot, x):
        self.perch = dict(spot)
        self.perch_rect = self.p.window_rect(spot["hwnd"])
        self.mode = "perched"
        self.perch_timer = self.rng.uniform(40, 120)
        self.events.append("perched")

    def start_perch(self, cat_x, cat_y) -> bool:
        """Choose the nearest exposed window edge and walk over to hop on it."""
        if not self.spots:
            return False
        def dist(s):
            px = min(max(cat_x, s["x1"] + 40), s["x2"] - 40)
            return math.hypot(px - cat_x, (s["y"] - FEET) - cat_y)
        spot = min(self.spots, key=dist)
        px = min(max(cat_x, spot["x1"] + 40), spot["x2"] - 40)
        self.perch = dict(spot)
        self.approach_target = (px, spot["y"] - FEET)
        self.approach_timer = APPROACH_TIMEOUT
        self.mode = "approach"
        return True

    def _perch_still_valid(self) -> bool:
        rect = self.p.window_rect(self.perch["hwnd"])
        if rect is None:
            return False
        if self.perch_rect and rect != self.perch_rect:
            dx, dy = rect[0] - self.perch_rect[0], rect[1] - self.perch_rect[1]
            self.perch["x1"] += dx; self.perch["x2"] += dx; self.perch["y"] += dy
            self.perch_moved = (dx, dy)
        self.perch_rect = rect
        return True

    def _exposed_here(self, x) -> bool:
        return any(s["hwnd"] == self.perch["hwnd"] and s["x1"] - 10 <= x <= s["x2"] + 10 for s in self.spots)

    # ------------------------------------------------------------------- gifts
    def _load_gifts(self):
        if self.gifts_path and os.path.exists(self.gifts_path):
            try:
                with open(self.gifts_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"day": "", "count": 0, "last": 0.0}

    def _save_gifts(self):
        if not self.gifts_path:
            return
        try:
            os.makedirs(os.path.dirname(self.gifts_path), exist_ok=True)
            with open(self.gifts_path, "w", encoding="utf-8") as f:
                json.dump(self.gift_log, f)
        except Exception:
            pass

    def gifts_left_today(self) -> int:
        today = date.today().isoformat()
        if self.gift_log.get("day") != today:
            self.gift_log = {"day": today, "count": 0, "last": self.gift_log.get("last", 0.0)}
        return max(0, self.gifts_per_day - self.gift_log["count"])

    def maybe_gift(self, dt, cat_x, wellbeing, user_present) -> bool:
        if not self.gifts_enabled or self.gift or self.mode != "free":
            return False
        self.gift_check -= dt
        if self.gift_check > 0:
            return False
        self.gift_check = 60.0
        now = self.clock()
        if (now - self.session_start < 300 or now - self.gift_log.get("last", 0.0) < GIFT_MIN_GAP
                or self.gifts_left_today() <= 0):
            return False
        # callables so the (slightly costly) checks only run once a minute
        wellbeing = wellbeing() if callable(wellbeing) else wellbeing
        user_present = user_present() if callable(user_present) else user_present
        if wellbeing < 60 or not user_present:
            return False
        if self.rng.random() > 0.08:
            return False
        side = -1 if cat_x > self.w / 2 else 1
        gx = cat_x + side * 70
        self.gift = {"kind": self.rng.choice(GIFT_KINDS), "x": gx, "y": self.floor_y(gx) + FEET - 24,
                     "ttl": GIFT_LIFETIME}
        self.gift_log["count"] += 1
        self.gift_log["last"] = now
        self._save_gifts()
        self.events.append("gift_drop")
        return True

    def gift_hit(self, x, y) -> bool:
        g = self.gift
        return bool(g) and abs(x - g["x"]) <= 28 and abs(y - g["y"]) <= 28

    def open_gift(self):
        self.gift = None

    # -------------------------------------------------------------------- tick
    def wants_desktop(self, cat, dt, cat_x, cat_y, can_start: bool):
        """Utility check: start a chase or a climb when it beats doing nothing."""
        self.chase_cooldown -= dt
        self.perch_cooldown -= dt
        if not can_start or self.mode != "free":
            return
        needs = {"hunger": cat.hunger, "energy": cat.energy, "happiness": cat.happiness, "trust": cat.trust}
        personality = getattr(cat, "personality", {}) or {}
        dist = math.hypot(self.cursor[0] - cat_x, self.cursor[1] - cat_y) if self.cursor else 9999.0
        self.perch_check -= dt
        check_perch = self.perch_check <= 0
        if check_perch:
            self.perch_check = PERCH_CHECK_EVERY
        scores = autonomy.score_desktop(
            needs, personality, memory=getattr(cat, "memory_graph", None), context="alone",
            cursor_speed=self.cursor_speed, cursor_dist=dist,
            perch_available=bool(self.spots) and self.perch_enabled and self.perch_cooldown <= 0)
        # Chase: checked every frame while the cursor zips around (prey moment)
        if self.chase_enabled and self.chase_cooldown <= 0 and self.cursor and self.rng.random() < scores["chase_cursor"] * 0.04:
            self.mode = "chase"
            self.chase_timer = CHASE_MAX_TIME
            self.events.append("chase_start")
            return
        if check_perch and self.rng.random() < scores["perch"] * 0.3:
            if self.start_perch(cat_x, cat_y):
                self.events.append("approach")

    def chase_target(self, cat_x, cat_y):
        cx, cy = self.cursor
        side = -1 if cat_x < cx else 1
        return cx + side * CHASE_KEEP_AWAY, cy

    def update(self, dt, cat_x, cat_y) -> Tuple[float, float, bool]:
        """
        Advance desktop behaviour. Returns (x, y, owns_position): when owns_position
        is True the game must not move the cat itself this frame (flying, hopping,
        riding a window).
        """
        self.refresh(dt=dt)
        self.sense_cursor(dt)
        if self.gift:
            self.gift["ttl"] -= dt
            if self.gift["ttl"] <= 0:
                self.gift = None

        if self.mode == "airborne":
            return self._fly(dt, cat_x, cat_y)

        if self.mode == "hop":
            self.hop_t += dt / HOP_TIME
            t = min(1.0, self.hop_t)
            (x0, y0), (x1, y1) = self.hop_from, self.hop_to
            arc = -4 * 60 * t * (1 - t)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + arc
            if t >= 1.0:
                spot = self.perch
                if spot and self.p.window_rect(spot["hwnd"]) is not None:
                    self._settle_on(spot, x1)
                else:
                    self.drop()
            return x, y, True

        if self.mode == "approach":
            self.approach_timer -= dt
            tx, ty = self.approach_target
            if self.approach_timer <= 0 or not self.perch or self.p.window_rect(self.perch["hwnd"]) is None:
                self.mode, self.perch = "free", None
                self.perch_cooldown = PERCH_COOLDOWN
                return cat_x, cat_y, False
            if math.hypot(cat_x - tx, cat_y - (ty + 90)) < 14:
                self.mode = "hop"
                self.hop_t = 0.0
                self.hop_from, self.hop_to = (cat_x, cat_y), (tx, ty)
                return cat_x, cat_y, True
            return cat_x, cat_y, False   # the game walks it towards approach_point()

        if self.mode == "perched":
            self.perch_moved = (0, 0)
            if not self._perch_still_valid():
                self.drop("perch_fall")
                return cat_x, cat_y, True
            dx, dy = self.perch_moved
            x = min(max(cat_x + dx, self.perch["x1"] + 20), self.perch["x2"] - 20)
            y = self.perch["y"] - FEET
            if self.refresh_timer >= 0.49 and not self._exposed_here(x):   # just refreshed: covered now?
                self.drop("perch_fall")
                return x, y, True
            self.perch_timer -= dt
            if y < FEET:   # window dragged to the very top of the screen
                self.drop("perch_fall")
            return x, y, False

        if self.mode == "chase":
            self.chase_timer -= dt
            if not self.cursor or self.chase_timer <= 0 or self.cursor_still > 1.5:
                self.mode = "free"
                self.chase_cooldown = CHASE_COOLDOWN
                self.events.append("chase_tired" if self.chase_timer <= 0 else "chase_end")
            else:
                tx, ty = self.chase_target(cat_x, cat_y)
                if math.hypot(tx - cat_x, ty - cat_y) < 18:
                    self.mode = "free"
                    self.chase_cooldown = CHASE_COOLDOWN
                    self.events.append("chase_caught")
            return cat_x, cat_y, False

        return cat_x, cat_y, False

    def approach_point(self):
        tx, ty = self.approach_target
        return tx, ty + 90   # just under the edge, then hop up

    def leave_perch(self):
        """Hop down on purpose (bored of the view, or hungry)."""
        if self.mode == "perched":
            self.launch(self.rng.choice((-1, 1)) * self.rng.uniform(80, 160), -380,
                        ignore_hwnd=self.perch["hwnd"] if self.perch else None)
            self.perch_cooldown = PERCH_COOLDOWN

    def _fly(self, dt, x, y):
        half = 40
        self.vy += GRAVITY * dt
        nx, ny = x + self.vx * dt, y + self.vy * dt
        if nx < half or nx > self.w - half:
            nx = min(max(nx, half), self.w - half)
            self.vx = -self.vx * 0.55
            if not self.bonked:
                self.bonked = True
                self.events.append("bonk")
        if ny < half:
            ny, self.vy = half, abs(self.vy) * 0.3
        if self.vy > 0:
            spots = [s for s in self.spots if s["hwnd"] != self.ignore_hwnd]
            spot = _desktop.spot_at(spots, nx, y + FEET, ny + FEET) if self.perch_enabled else None
            if spot:
                self._settle_on(spot, nx)
                self.events.append("landed")
                return nx, spot["y"] - FEET, True
            floor = self.floor_y(nx)
            if ny >= floor:
                self.mode = "free"
                self.vx = self.vy = 0.0
                self.events.append("landed")
                return nx, floor, True
        return nx, ny, True

    def constrain_target(self, tx, ty):
        """While perched, any walk target is projected onto the title bar."""
        if self.mode == "perched" and self.perch:
            return min(max(tx, self.perch["x1"] + 20), self.perch["x2"] - 20), self.perch["y"] - FEET
        return tx, ty

    def pop_events(self) -> List[str]:
        ev, self.events = self.events, []
        return ev
