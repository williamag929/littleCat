"""
Tests for roadmap phase 3 (work companion): away/back, Focus, typing rhythm, time together.
The Windows input APIs are replaced by a fake provider and a fake clock.

    python test_companion.py
"""

import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import companion as companion_mod  # noqa: E402
from companion import Companion, format_together  # noqa: E402
from cat_brain import CatBrain  # noqa: E402

FPS = 30
DT = 1 / FPS


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class FakeInput:
    """Stands in for desktop: idle time, last-input tick and cursor."""

    def __init__(self, clock):
        self.clock = clock
        self.last_input = clock()
        self.tick = 0
        self.cursor = (500, 500)

    def press(self):                       # a key (or click): tick changes, cursor doesn't
        self.tick += 1
        self.last_input = self.clock()

    def move_mouse(self):
        self.tick += 1
        self.cursor = (self.cursor[0] + 7, self.cursor[1])
        self.last_input = self.clock()

    def idle_seconds(self):
        return max(0.0, self.clock() - self.last_input)

    def last_input_tick(self):
        return self.tick

    def cursor_pos(self):
        return self.cursor


def make(**kw):
    clock = FakeClock()
    inp = FakeInput(clock)
    return Companion(provider=inp, clock=clock, **kw), inp, clock


def run(comp, clock, seconds, each=None):
    events = []
    for i in range(int(seconds * FPS)):
        clock.t += DT
        if each:
            each(i)
        events += comp.update(DT)
    return events


# ---------------------------------------------------------------- away / back
def test_away_after_five_minutes_then_back_once():
    comp, inp, clock = make()
    events = run(comp, clock, 299)
    assert not comp.away and events == []
    events = run(comp, clock, 2)
    assert comp.away and events == [("away",)]
    assert comp.need_rate() < 0.5, "needs must slow down while away"
    events = run(comp, clock, 600)
    assert events == [], "no repeated away events"
    inp.press()
    events = run(comp, clock, 1)
    assert [e[0] for e in events] == ["back"]
    assert events[0][1] >= 900 - 2, f"away duration counted from last input: {events[0][1]}"
    inp.press()
    assert run(comp, clock, 5, each=lambda i: inp.press()) == [], "says welcome back only once"
    assert comp.need_rate() == 1.0


def test_presence_can_be_turned_off():
    comp, inp, clock = make(presence=False)
    assert run(comp, clock, 900) == [] and not comp.away


# ---------------------------------------------------------------- focus
def test_focus_ends_with_one_event_and_never_goes_away():
    comp, inp, clock = make()
    comp.start_focus(25)
    assert comp.in_focus and 24 * 60 < comp.focus_left() <= 25 * 60
    events = run(comp, clock, 25 * 60 - 1)        # deep reading: no input at all
    assert events == [] and comp.in_focus and not comp.away, "focus is not 'away'"
    events = run(comp, clock, 2)
    assert events == [("focus_done", 25)] and not comp.in_focus
    assert run(comp, clock, 60) == [] and not comp.away, "no 'away' right after a quiet Focus"
    assert run(comp, clock, 300) == [("away",)], "away again only after 5 more idle minutes"


def test_focus_can_be_cancelled():
    comp, inp, clock = make()
    comp.start_focus(25)
    run(comp, clock, 60)
    comp.cancel_focus()
    assert not comp.in_focus and comp.focus_left() == 0
    assert all(e[0] != "focus_done" for e in run(comp, clock, 30 * 60))


# ---------------------------------------------------------------- typing rhythm
def test_typing_rhythm_without_reading_keys():
    comp, inp, clock = make()
    run(comp, clock, 3, each=lambda i: inp.press() if i % 6 == 0 else None)   # 5 inputs/s
    assert comp.typing(), f"5 inputs/s with the cursor still is typing (rhythm {comp.rhythm():.2f})"
    beats = set()
    run(comp, clock, 1, each=lambda i: (inp.press() if i % 6 == 0 else None, beats.add(comp.beat)))
    assert beats == {0, 1}, "paws alternate with the input"
    run(comp, clock, 3)
    assert not comp.typing() and comp.rhythm() == 0, "stops when you stop"


def test_mouse_motion_is_not_typing():
    comp, inp, clock = make()
    run(comp, clock, 3, each=lambda i: inp.move_mouse())
    assert not comp.typing(), "moving the mouse is not typing"


def test_rhythm_can_be_turned_off():
    comp, inp, clock = make(rhythm=False)
    run(comp, clock, 3, each=lambda i: inp.press() if i % 3 == 0 else None)
    assert not comp.typing()


def test_companion_never_reads_keys_or_screen():
    with open(companion_mod.__file__, encoding="utf-8") as f:
        src = f.read()
    for banned in ("GetAsyncKeyState", "GetKeyState", "SetWindowsHookEx", "keyboard", "pynput",
                   "ImageGrab", "BitBlt", "ScreenCapture", "pygame.key"):
        assert banned not in src, f"companion.py must not use {banned}"


# ---------------------------------------------------------------- together
def test_together_counts_only_while_present():
    comp, inp, clock = make()
    run(comp, clock, 120, each=lambda i: inp.press() if i % 30 == 0 else None)
    gained = comp.take_together()
    assert 119 <= gained <= 121, gained
    assert comp.take_together() == 0
    run(comp, clock, 900)                      # walk away: 5 min still counts, then it stops
    gained = comp.take_together()
    assert 290 <= gained <= 310, f"only the time before going away counts: {gained}"


def test_together_survives_save_and_load():
    cat = CatBrain("Tester")
    cat.time_together = 3 * 3600 + 20 * 60
    cat.focus_sessions = 4
    path = os.path.join(tempfile.mkdtemp(), "cat.json")
    cat.save_brain(path)
    other = CatBrain("Tester")
    other.load_brain(path)
    assert other.time_together == cat.time_together and other.focus_sessions == 4
    assert other.get_status()["time_together"] == 12000
    assert format_together(other.time_together) == "3 h 20 min"
    assert format_together(12 * 60 + 5) == "12 min"


def test_old_saves_load_with_zero_together():
    cat = CatBrain("Old")
    path = os.path.join(tempfile.mkdtemp(), "cat.json")
    cat.save_brain(path)
    import json
    with open(path) as f:
        data = json.load(f)
    data.pop("time_together")
    data.pop("focus_sessions")
    with open(path, "w") as f:
        json.dump(data, f)
    other = CatBrain("Old")
    other.load_brain(path)
    assert other.time_together == 0 and other.focus_sessions == 0


# ---------------------------------------------------------------- whole game, headless
def _headless_game():
    """A real LittleCatGame on the dummy video driver, saving into a temp folder."""
    import game
    tmp = tempfile.mkdtemp()
    game.DATA_DIR = tmp
    game.CATS_DIR = os.path.join(tmp, "cats")
    game.EXPORT_DIR = os.path.join(tmp, "exports")
    game.PROFILES_INDEX = os.path.join(tmp, "profiles.json")
    game.FOCUS_MINUTES = 1
    g = game.LittleCatGame()
    g.life = None                                   # no real windows in a test
    clock = FakeClock()
    inp = FakeInput(clock)
    g.companion = Companion(provider=inp, clock=clock)
    g.display.play_areas = [(150, 250, 1300, 700)]
    return game, g, inp, clock


def _step(g, clock, inp=None, typing=False):
    clock.t += DT
    if typing and int(clock.t * FPS) % 6 == 0:
        inp.press()
    g.update()


def test_game_focus_is_silent_then_celebrates():
    game, g, inp, clock = _headless_game()
    g.cat.hunger, g.cat.energy = 90, 15            # would normally beg for food and sleep
    g.start_focus()
    start_line = g.speech and g.speech["text"]
    lines = set()
    for _ in range(60 * FPS - 10):
        _step(g, clock, inp, typing=True)
        if g.speech and g.speech["text"] != start_line:
            lines.add(g.speech["text"])
    assert lines == set(), f"zero messages during Focus, got {lines}"
    assert g.current_action == "focus", g.current_action
    trust = g.cat.trust
    after = []
    for _ in range(20 * FPS):
        _step(g, clock)
        if g.speech and (not after or after[-1] != g.speech["text"]):
            after.append(g.speech["text"])
    assert not g.companion.in_focus and g.cat.focus_sessions == 1
    assert g.cat.trust > trust, "a finished Focus strengthens the bond"
    assert len(after) >= 2, f"it congratulates you, then suggests a break: {after}"


def test_game_never_welcomes_you_back_starving():
    game, g, inp, clock = _headless_game()
    g.cat.hunger = 20
    while not g.companion.away:                    # the first 5 idle minutes are normal time
        _step(g, clock)
    at_away = g.cat.hunger
    for _ in range(20 * 60 * FPS):                 # then 20 real minutes away
        _step(g, clock)
    assert g.companion.away and g.current_action == "sleep"
    assert g.cat.hunger <= max(at_away, 65), f"hunger {at_away:.1f} -> {g.cat.hunger:.1f} while away"
    g.speech = None
    inp.press()
    _step(g, clock)
    assert g.speech and g.speech["priority"] == 4, "says welcome back"
    assert not g.companion.away


def test_game_taps_paws_while_you_type():
    game, g, inp, clock = _headless_game()
    g.cat.energy = 80
    g.cat.personality["playful"] = 0.8
    poses = set()
    for _ in range(4 * FPS):
        _step(g, clock, inp, typing=True)
        poses.add(g.current_action)
    assert "tap" in poses, poses
    assert g.cat.time_together > 3


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
