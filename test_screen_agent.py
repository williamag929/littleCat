"""
Tests for roadmap phase 2 (screen agent + the cat's arcade). Headless, no keys sent.

    python test_screen_agent.py
"""

import json
import os
import random
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from arcade import ArcadeSession, cat_aim_error  # noqa: E402
from minigames.pong import Pong  # noqa: E402
from screen_agent.actuator import KeyActuator  # noqa: E402
from screen_agent.agent import list_profiles, load_profile, profile_from_poc  # noqa: E402
from screen_agent.bench import run  # noqa: E402
from screen_agent.perception import Detector  # noqa: E402
from screen_agent.policy import (ChaseBallPolicy, ImitationPolicy, PredictivePolicy, fold,  # noqa: E402
                                 predict_landing_x)
from screen_agent.state import TrackedState  # noqa: E402


# ---------------------------------------------------------------- prediction
def test_fold_reflects_like_walls():
    assert fold(50, 0, 100) == 50
    assert fold(130, 0, 100) == 70          # bounced off the right wall
    assert fold(-20, 0, 100) == 20          # bounced off the left wall
    assert fold(250, 0, 100) == 50          # two bounces


def test_prediction_matches_the_real_ball():
    errors = []
    for seed in range(30):
        g = Pong(seed=seed)
        g.serve_delay = 0
        s = TrackedState(g.ball_x, g.ball_y, g.vx, g.vy, g.paddle_x, 320, 240, 222, 48, 6)
        guess = predict_landing_x(s)
        while True:   # step until the ball reaches the paddle line (hit or miss)
            events = g.step(1 / 240, 0)
            if g.ball_y >= 222 - 3 or "hit" in events:
                break
        errors.append(abs(guess - g.ball_x))
    assert max(errors) < 3.0, max(errors)


# ---------------------------------------------------------------- benchmark
def test_benchmark_is_fast_and_prediction_beats_chasing():
    t0 = time.perf_counter()
    chase = run(ChaseBallPolicy(), attempts=1000)
    predict = run(PredictivePolicy(), attempts=1000)
    elapsed = time.perf_counter() - t0
    assert elapsed < 10, f"2x1000 attempts took {elapsed:.1f}s"
    assert predict["hit_rate"] >= 0.90, predict
    assert predict["hit_rate"] > chase["hit_rate"], (predict, chase)
    assert predict["best_rally"] > chase["best_rally"], (predict, chase)


def test_tracker_counts_hits_and_misses():
    r = run(PredictivePolicy(error=0.6, rng=random.Random(1)), attempts=150)
    assert abs(r["tracker_hits"] - r["hits"]) <= 3, r
    assert abs(r["tracker_misses"] - r["misses"]) <= 3, r


# ---------------------------------------------------------------- perception
def test_detector_finds_ball_and_paddle_without_calibration():
    g = Pong(seed=3)
    det = Detector(downsample=1)
    seen = frames = 0
    worst = 0.0
    for i in range(900):
        g.step(1 / 60, 1 if (i // 40) % 2 else -1)
        if i % 2:
            continue
        obs = det.observe(g.render_array())
        if g.serve_delay > 0:
            continue
        frames += 1
        if obs.ball is not None:
            seen += 1
            worst = max(worst, abs(obs.ball[0] - g.ball_x) + abs(obs.ball[1] - g.ball_y))
        assert obs.paddle_x is not None and abs(obs.paddle_x - g.paddle_x) < 3
    assert seen / frames >= 0.95, seen / frames
    assert worst < 6, worst


def test_detector_handles_scaled_capture():
    """A 3x bigger capture (scaled display) still works: auto downsample + ball size estimate."""
    import numpy as np
    g = Pong(seed=5)
    det = Detector(downsample="auto")
    hits = 0
    for i in range(300):
        g.step(1 / 60, 0)
        big = np.repeat(np.repeat(g.render_array(), 3, axis=0), 3, axis=1)
        obs = det.observe(big)
        if obs.ball is not None and g.serve_delay <= 0:
            hits += abs(obs.ball[0] - g.ball_x * 3) < 12
    assert det.ds == 3
    assert hits > 200, hits
    assert 10 <= det.ball_size <= 26, det.ball_size


def test_pixels_end_to_end_plays_well():
    r = run(PredictivePolicy(), attempts=25, mode="pixels")
    assert r["hit_rate"] >= 0.85, r


# ---------------------------------------------------------------- actuator safety
class Keys:
    def __init__(self):
        self.log = []

    def __call__(self, key, down):
        self.log.append((key, down))


def test_actuator_holds_keys_without_blocking():
    keys = Keys()
    act = KeyActuator(("left", "right"), target_hwnd=0, send=keys, panic=lambda: False)
    t0 = time.perf_counter()
    for a in (1, 1, 1, 0, -1, -1, 1):
        assert act.apply(a)
    assert time.perf_counter() - t0 < 0.01          # no sleeping while a key is down
    assert keys.log == [("right", True), ("right", False), ("left", True), ("left", False), ("right", True)]


def test_actuator_releases_when_focus_is_lost():
    keys = Keys()
    focus = {"hwnd": 42}
    act = KeyActuator(("left", "right"), target_hwnd=42, foreground=lambda: focus["hwnd"], send=keys,
                      panic=lambda: False)
    act.apply(1)
    focus["hwnd"] = 7                                # you clicked another window
    act.apply(1)
    act.apply(-1)
    assert keys.log == [("right", True), ("right", False)], keys.log   # nothing typed elsewhere


def test_panic_hotkey_stops_everything():
    keys = Keys()
    panic = {"on": False}
    act = KeyActuator(("left", "right"), send=keys, panic=lambda: panic["on"])
    act.apply(-1)
    panic["on"] = True
    assert act.apply(-1) is False and act.stopped
    assert keys.log[-1] == ("left", False)
    panic["on"] = False
    assert act.apply(1) is False                     # stays stopped


# ---------------------------------------------------------------- imitation
def test_imitation_learns_a_teachers_style():
    teacher = PredictivePolicy(error=0.2, rng=random.Random(4))
    student = ImitationPolicy()
    run(teacher, attempts=60, recorder=student.record)
    acc = student.train()
    # The teacher's random aiming mistakes can't be predicted, so exact agreement is modest;
    # what matters is that the student plays like a decent player.
    assert acc > 0.5, acc                               # well above chance (1/3)
    mine = run(student, attempts=150, seed=9)
    stay = run(type("Stay", (), {"act": lambda self, s: 0})(), attempts=150, seed=9)
    assert mine["hit_rate"] > 0.8 and mine["hit_rate"] > stay["hit_rate"] + 0.5, (mine, stay)

    path = os.path.join(tempfile.mkdtemp(), "style.json")
    student.games_recorded = 3
    student.save(path)
    again = ImitationPolicy.load(path)
    assert again.trained and again.games_recorded == 3


# ---------------------------------------------------------------- the cat's arcade
def test_cat_gets_better_with_practice():
    assert cat_aim_error(0) > cat_aim_error(5) > cat_aim_error(50) >= 0.18


def test_watch_me_play_session_ends_after_three_lives():
    s = ArcadeSession("cat", games_played=0, seed=2)
    events = []
    for _ in range(60 * 60 * 10):
        events += s.step(1 / 60)
        if s.over:
            break
    assert s.over and "game_over" in events and s.lives == 0
    assert -0.3 <= s.reward() <= 1.0
    assert s.summary()["mode"] == "cat"


def test_teach_me_records_and_cat_then_plays_like_you():
    style = ImitationPolicy()
    teacher = PredictivePolicy(error=0.4, rng=random.Random(8))
    for game in range(3):
        s = ArcadeSession("you", imitation=style, seed=game)
        while not s.over:
            # the "human": a decent player looking at the true state
            p = s.pong
            human = teacher.act(TrackedState(p.ball_x, p.ball_y, p.vx, p.vy, p.paddle_x, 320, 240, 222, 48, 6,
                                             visible=p.serve_delay <= 0))
            evs = s.step(1 / 60, human)
            if s.pong.t > 600:
                break
        assert "learned" in evs
    assert style.games_recorded == 3 and style.trained
    s = ArcadeSession("cat", imitation=style, seed=11)
    assert s.style == "yours"


# ---------------------------------------------------------------- profiles
def test_profiles_load():
    names = list_profiles()
    assert "littlecat_pong" in names and "pong_generic" in names
    p = load_profile("littlecat_pong")
    assert p["window_title"] == "LittleCat Pong" and p["keys"] == ["left", "right"]


def test_old_poc_calibration_becomes_a_profile():
    poc = {"region": {"left": 10, "top": 20, "width": 300, "height": 200},
           "ball_color": {"b": 1, "g": 2, "r": 3}, "paddle_color": {"b": 4, "g": 5, "r": 6},
           "config": {"tolerance": 25, "move_key": ["a", "d"]}}
    p = profile_from_poc(json.loads(json.dumps(poc)))
    assert p["region"] == [10, 20, 300, 200]
    assert p["ball_color"] == [3, 2, 1] and p["keys"] == ["a", "d"]


def test_screen_capture_works_on_windows():
    if sys.platform != "win32":
        return
    from screen_agent.capture import ScreenCapture
    with ScreenCapture((0, 0, 64, 48)) as cap:
        frame = cap.grab()
    assert frame is not None and frame.shape == (48, 64, 3)


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        t0 = time.perf_counter()
        try:
            fn()
            print(f"  ok   {name} ({time.perf_counter() - t0:.1f}s)")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {name}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ERR  {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
