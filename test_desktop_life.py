"""
Tests for roadmap phase 1 (cat living on the desktop).
Runs anywhere: the Windows desktop is replaced by a fake provider.

    python test_desktop_life.py
"""

import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import autonomy  # noqa: E402
import desktop  # noqa: E402
from desktop import WindowInfo, perch_spots, spot_at  # noqa: E402
from desktop_life import DesktopLife, FEET  # noqa: E402

FPS = 30
DT = 1 / FPS
SCREEN = (1600, 900)
MONITOR = [{"rect": (0, 0, 1600, 900), "work": (0, 0, 1600, 860), "primary": True}]


class FakeDesktop:
    """Stands in for the `desktop` module."""

    def __init__(self, windows=None):
        self.windows = windows or []
        self.cursor = (800, 450)

    def client_origin(self, hwnd):
        return 0, 0

    def monitors(self):
        return MONITOR

    def list_windows(self, exclude=()):
        return [w for w in self.windows if w.hwnd not in exclude]

    def window_rect(self, hwnd):
        for w in self.windows:
            if w.hwnd == hwnd:
                return w.rect
        return None

    def cursor_pos(self):
        return self.cursor

    def move(self, hwnd, dx, dy):
        for w in self.windows:
            if w.hwnd == hwnd:
                l, t, r, b = w.rect
                w.rect = (l + dx, t + dy, r + dx, b + dy)

    def close(self, hwnd):
        self.windows = [w for w in self.windows if w.hwnd != hwnd]


class FakeClock:
    def __init__(self):
        self.t = 1_000_000.0

    def __call__(self):
        return self.t


class FakeCat:
    def __init__(self, **kw):
        self.hunger, self.energy, self.happiness, self.trust = 20, 90, 80, 60
        self.personality = {"playful": 0.9, "curious": 0.9, "calm": 0.5, "social": 0.5}
        self.memory_graph = None
        self.__dict__.update(kw)


def make_life(windows=None, **kw):
    fake = FakeDesktop(windows)
    clock = FakeClock()
    life = DesktopLife(SCREEN, provider=fake, overlay_hwnd=999, rng=random.Random(1), clock=clock, **kw)
    return life, fake, clock


def run(life, x, y, seconds):
    for _ in range(int(seconds * FPS)):
        x, y, _owns = life.update(DT, x, y)
    return x, y


# ---------------------------------------------------------------- pure helpers
def test_perch_spots_occlusion():
    top = WindowInfo(1, (500, 300, 900, 700), 0)       # in front
    back = WindowInfo(2, (200, 400, 1200, 800), 1)     # behind; its edge is partly covered
    spots = perch_spots([top, back], bounds=(0, 0, 1600, 900))
    assert {"hwnd": 1, "x1": 500, "x2": 900, "y": 300} in spots
    back_spots = sorted((s["x1"], s["x2"]) for s in spots if s["hwnd"] == 2)
    assert back_spots == [(200, 500), (900, 1200)], back_spots


def test_perch_spots_skip_maximized_and_narrow():
    maxed = WindowInfo(1, (-7, -7, 1607, 893), 0)
    assert perch_spots([maxed], bounds=(0, 0, 1600, 900)) == []
    narrow = WindowInfo(2, (100, 300, 180, 600), 0)
    assert perch_spots([narrow], bounds=(0, 0, 1600, 900)) == []


def test_spot_at_finds_first_edge_below():
    spots = [{"hwnd": 1, "x1": 100, "x2": 400, "y": 300}, {"hwnd": 2, "x1": 100, "x2": 400, "y": 500}]
    assert spot_at(spots, 250, 200, 600)["hwnd"] == 1
    assert spot_at(spots, 250, 350, 600)["hwnd"] == 2
    assert spot_at(spots, 50, 200, 600) is None


def test_desktop_module_fails_soft():
    # Real OS calls must never raise (on any platform)
    desktop.cursor_pos(); desktop.idle_seconds(); desktop.monitors(); desktop.virtual_screen()
    desktop.list_windows(); desktop.window_rect(0); desktop.left_button_down()


# ---------------------------------------------------------------- throw physics
def throw(life, clock, start, velocity):
    x, y = start
    life.grab()
    for _ in range(4):
        life.track_drag(x, y)
        clock.t += 0.02
        x += velocity[0] * 0.02
        y += velocity[1] * 0.02
    life.track_drag(x, y)
    return life.release(x, y), x, y


def test_throw_flies_and_lands_on_taskbar():
    life, _fake, clock = make_life()
    result, x, y = throw(life, clock, (400, 400), (1500, -900))
    assert result == "thrown" and life.mode == "airborne"
    x, y = run(life, x, y, 4)
    assert life.mode == "free"
    assert abs(y - (860 - FEET)) < 1, y          # standing on the taskbar
    assert 40 <= x <= SCREEN[0] - 40              # never leaves the screen
    events = life.pop_events()
    assert events[0] == "thrown" and "landed" in events


def test_throw_bounces_off_screen_edge():
    life, _fake, clock = make_life()
    _r, x, y = throw(life, clock, (1400, 300), (2500, 0))
    run(life, x, y, 3)
    assert "bonk" in life.pop_events()


def test_gentle_release_stays_put():
    life, _fake, clock = make_life()
    life.grab()
    life.track_drag(500, 400); clock.t += 0.1; life.track_drag(503, 401)
    assert life.release(503, 401) == "set_down"
    assert life.mode == "free"


def test_falls_onto_a_window():
    win = WindowInfo(7, (300, 600, 900, 850), 0)
    life, _fake, clock = make_life([win])
    _r, x, y = throw(life, clock, (600, 200), (0, -800))
    x, y = run(life, x, y, 3)
    assert life.mode == "perched" and life.perch["hwnd"] == 7
    assert abs(y - (600 - FEET)) < 1


def test_place_cat_on_window_by_hand():
    win = WindowInfo(7, (300, 500, 900, 850), 0)
    life, _fake, clock = make_life([win])
    life.grab()
    life.track_drag(600, 500 - FEET); clock.t += 0.2; life.track_drag(601, 500 - FEET)
    assert life.release(601, 500 - FEET) == "perched"


# ---------------------------------------------------------------- perching
def perched_life():
    win = WindowInfo(7, (300, 500, 900, 850), 0)
    life, fake, clock = make_life([win])
    assert life.start_perch(600, 700)
    x, y = 600, 700
    for _ in range(15 * FPS):                     # walk to the approach point, then hop
        if life.mode == "approach":
            tx, ty = life.approach_point()
            dx, dy = tx - x, ty - y
            d = max(1e-6, (dx * dx + dy * dy) ** 0.5)
            step = min(d, 3.0)
            x, y = x + dx / d * step, y + dy / d * step
        x, y, _ = life.update(DT, x, y)
        if life.mode == "perched":
            break
    return life, fake, x, y


def test_walks_and_hops_onto_window():
    life, _fake, x, y = perched_life()
    assert life.mode == "perched"
    assert abs(y - (500 - FEET)) < 1


def test_rides_the_window_when_it_moves():
    life, fake, x, y = perched_life()
    fake.move(7, 120, -80)
    x2, y2, _ = life.update(DT, x, y)
    assert abs(x2 - (x + 120)) < 1 and abs(y2 - (y - 80)) < 1


def test_falls_when_window_closes():
    life, fake, x, y = perched_life()
    fake.close(7)
    life.update(DT, x, y)
    assert life.mode == "airborne"
    assert "perch_fall" in life.pop_events()


def test_falls_when_window_gets_covered():
    life, fake, x, y = perched_life()
    fake.windows.insert(0, WindowInfo(8, (200, 200, 1000, 800), 0))   # new window in front
    life.refresh_timer = 0
    life.update(DT, x, y)
    assert life.mode == "airborne"


def test_hopping_down_does_not_land_back_on_same_window():
    life, _fake, x, y = perched_life()
    life.leave_perch()
    x, y = run(life, x, y, 4)
    assert life.mode == "free", life.mode            # reached the taskbar
    assert abs(y - (860 - FEET)) < 1
    assert life.pop_events().count("landed") == 1


def test_walk_target_stays_on_title_bar():
    life, _fake, _x, _y = perched_life()
    tx, ty = life.constrain_target(5000, 100)
    assert tx == 900 - 20 and ty == 500 - FEET


# ---------------------------------------------------------------- cursor chase
def test_chase_keeps_distance_and_gives_up():
    life, fake, _clock = make_life()
    cat = FakeCat()
    life.chase_cooldown = 0     # skip the start-of-session grace period
    x, y = 700, 450
    started = False
    for i in range(10 * FPS):
        fake.cursor = (900 + 300 * ((i // 3) % 2), 450)   # cursor zipping left/right
        x, y, _ = life.update(DT, x, y)
        life.wants_desktop(cat, DT, x, y, can_start=True)
        if life.mode == "chase":
            started = True
            tx, ty = life.chase_target(x, y)
            assert abs(tx - fake.cursor[0]) >= 70     # never targets the cursor itself
            break
    assert started, "an energetic playful cat should chase a zipping cursor"
    for _ in range(3 * FPS):                          # cursor stops: the chase ends
        x, y, _ = life.update(DT, x, y)
    assert life.mode == "free"


def test_tired_cat_does_not_chase():
    life, fake, _clock = make_life()
    cat = FakeCat(energy=5)
    for i in range(10 * FPS):
        fake.cursor = (900 + 300 * ((i // 3) % 2), 450)
        life.update(DT, 700, 450)
        life.wants_desktop(cat, DT, 700, 450, can_start=True)
    assert life.mode != "chase"


def test_score_desktop_needs_shape():
    rested = autonomy.score_desktop({"energy": 90, "hunger": 20}, {"playful": 0.8, "curious": 0.8},
                                    hour=19, cursor_speed=1200, cursor_dist=100, perch_available=True)
    tired = autonomy.score_desktop({"energy": 10, "hunger": 20}, {"playful": 0.8, "curious": 0.8},
                                   hour=19, cursor_speed=1200, cursor_dist=100, perch_available=True)
    assert rested["chase_cursor"] > tired["chase_cursor"] * 3
    assert rested["perch"] > tired["perch"]
    none = autonomy.score_desktop({"energy": 90}, {}, hour=19, perch_available=False)
    assert none["perch"] == 0 and none["chase_cursor"] < 0.05


# ---------------------------------------------------------------- gifts
def test_gifts_limited_per_day():
    path = os.path.join(tempfile.mkdtemp(), "gifts.json")
    life, _fake, clock = make_life(gifts_path=path, settings={"gifts_per_day": 2})
    life.rng = random.Random(3)
    gifts = 0
    for _hour in range(24 * 6):                       # 24h in 10-minute steps
        clock.t += 600
        life.gift_check = 0
        for _ in range(30):
            if life.maybe_gift(1.0, 800, wellbeing=90, user_present=True):
                gifts += 1
                assert life.gift_hit(life.gift["x"], life.gift["y"])
                life.open_gift()
            life.gift_check = 0
    assert 1 <= gifts <= 2, gifts
    # the daily count survives a restart
    again, _f, c2 = make_life(gifts_path=path, settings={"gifts_per_day": 2})
    assert again.gift_log["count"] == life.gift_log["count"]


def test_unhappy_cat_gives_no_gifts():
    life, _fake, clock = make_life()
    clock.t += 99999
    for _ in range(500):
        life.gift_check = 0
        assert not life.maybe_gift(1.0, 800, wellbeing=30, user_present=True)


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ok   {name}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {name}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ERR  {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
