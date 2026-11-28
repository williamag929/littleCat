"""
Tests for roadmap phase 4 (collection and visitors): wardrobe, album, visitors, adoption.

    python test_collection.py
"""

import json
import os
import random
import sys
import tempfile
from datetime import date, timedelta

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import collection  # noqa: E402
from collection import ACCESSORIES, COATS, Visit, VisitorSchedule  # noqa: E402
from cat_brain import CatBrain  # noqa: E402

FPS = 30
DT = 1 / FPS


# ---------------------------------------------------------------- wardrobe
def test_eight_accessories_with_reachable_unlocks():
    assert len(ACCESSORIES) == 8
    slots = {a[2] for a in ACCESSORIES.values()}
    assert slots == {"head", "face", "neck"}
    cat = CatBrain("Fresh")
    cat.trust = 30
    assert collection.unlocked(cat) == [], "a brand new cat has nothing yet"


def test_unlocks_follow_progress_and_announce_once():
    cat = CatBrain("Tester")
    cat.trust = 30
    cat.time_together = 3600
    assert collection.new_unlocks(cat) == ["bow"]
    assert collection.new_unlocks(cat) == [], "each unlock is announced once"
    cat.trust = 55
    cat.focus_sessions = 3
    assert set(collection.new_unlocks(cat)) == {"bell", "glasses"}
    assert set(collection.new_unlocks(cat, best_rally=12)) == {"crown"}
    collection.add_album(cat, "visitor", "Mochi visited", name="Mochi", coat="grey")
    assert collection.new_unlocks(cat) == ["flower"]
    for n in ("Luna", "Tofu"):
        collection.add_album(cat, "visitor", f"{n} visited", name=n, coat="black")
    assert "tophat" in collection.new_unlocks(cat)


def test_only_unlocked_items_can_be_worn():
    cat = CatBrain("Tester")
    assert not collection.equip(cat, "crown") and cat.accessory is None
    cat.unlocked = ["crown"]
    assert collection.equip(cat, "crown") and cat.accessory == "crown"
    assert not collection.equip(cat, "crown"), "no change"
    assert collection.equip(cat, None) and cat.accessory is None


def test_wardrobe_and_album_survive_save_and_load():
    cat = CatBrain("Tester")
    cat.coat = "siamese"
    cat.unlocked = ["bow", "scarf"]
    cat.accessory = "scarf"
    collection.add_album(cat, "gift", "a feather gift", "our pong games 🕹️")
    path = os.path.join(tempfile.mkdtemp(), "cat.json")
    cat.save_brain(path)
    other = CatBrain("Tester")
    other.load_brain(path)
    assert (other.coat, other.accessory, other.unlocked) == ("siamese", "scarf", ["bow", "scarf"])
    assert other.album[0]["title"] == "a feather gift" and other.album[0]["detail"].endswith("🕹️")


# ---------------------------------------------------------------- album
def test_album_keeps_one_record_per_title_and_a_maximum():
    cat = CatBrain("Tester")
    collection.add_album(cat, "record", "Pong record", "rally of 5")
    collection.add_album(cat, "record", "Pong record", "rally of 9")
    records = [e for e in cat.album if e["kind"] == "record"]
    assert len(records) == 1 and records[0]["detail"] == "rally of 9"
    for i in range(200):
        collection.add_album(cat, "moment", f"m{i}")
    assert len(cat.album) == collection.ALBUM_MAX and cat.album[-1]["title"] == "m199"


def test_adoptable_visitors_each_once():
    cat = CatBrain("Home")
    collection.add_album(cat, "visitor", "Mochi visited", name="Mochi", coat="grey")
    collection.add_album(cat, "visitor", "Luna visited", name="Luna", coat="black")
    collection.add_album(cat, "visitor", "Mochi visited", name="Mochi", coat="grey")
    names = [e["name"] for e in collection.adoptable(cat)]
    assert names == ["Mochi", "Luna"], names
    assert [e["name"] for e in collection.adoptable(cat, taken_names=["Luna"])] == ["Mochi"]
    collection.mark_adopted(cat, "Mochi")
    assert [e["name"] for e in collection.adoptable(cat)] == ["Luna"]


# ---------------------------------------------------------------- visitors
def test_at_most_one_visitor_per_day_even_after_restart():
    path = os.path.join(tempfile.mkdtemp(), "visitors.json")
    day = [date(2026, 11, 27)]
    rng = random.Random(3)
    sched = VisitorSchedule(path, rng=rng, today=lambda: day[0])
    visits = 0
    for _ in range(int(6 * 3600 * FPS / 10)):            # 6 calm hours at 3 fps steps
        if sched.should_visit(DT * 10, calm=True):
            visits += 1
            sched.mark()
    assert visits == 1, f"{visits} visitors in one day"
    again = VisitorSchedule(path, rng=rng, today=lambda: day[0])   # restart the app
    again.uptime = 10_000
    assert not any(again.should_visit(1.0, True) for _ in range(20000)), "restart doesn't allow a 2nd visit"
    day[0] += timedelta(days=1)
    assert any(again.should_visit(1.0, True) for _ in range(40000)), "a new day allows a new visitor"


def test_no_visitor_unless_calm_or_during_warmup():
    sched = VisitorSchedule(None, rng=random.Random(1))
    assert not any(sched.should_visit(1.0, calm=True) for _ in range(100)), "never in the first 2 minutes"
    assert not any(sched.should_visit(1.0, calm=False) for _ in range(50000))


def test_visit_story_arrives_plays_and_always_leaves():
    v = Visit({"name": "Mochi", "coat": "grey"}, 1600, host_x=500, host_y=600, rng=random.Random(0))
    assert v.x < 0, "walks in from the nearest edge"
    events, host_poses = [], set()
    for _ in range(120 * FPS):
        host = v.update(DT, 500, 600)
        if host:
            host_poses.add(host[0])
        events += v.pop_events()
        if v.done:
            break
    assert events == ["arrived", "play", "leaving", "gone"], events
    assert v.done and (v.x < -60 or v.x > 1660), "gone off screen"
    assert host_poses == {"sit", "play"}
    assert v.age < 60, f"short visit: {v.age:.0f}s"


def test_visitor_never_stays():
    v = Visit({"name": "Luna", "coat": "black"}, 3000, host_x=2900, host_y=600)
    v.SNIFF, v.PLAY = 1e9, 1e9                      # even if it wanted to stay forever...
    for _ in range(int((Visit.MAX_LIFETIME + 40) * FPS)):
        v.update(DT, 2900, 600)
        if v.done:
            break
    assert v.done, f"still here in state {v.state}"


def test_visitor_looks_different_from_the_host():
    rng = random.Random(5)
    for _ in range(50):
        vis = collection.make_visitor(rng, home_coat="ginger", avoid_names=["Mochi"])
        assert vis["coat"] in COATS and vis["coat"] != "ginger" and vis["name"] != "Mochi"


# ---------------------------------------------------------------- whole game, headless
def _headless_game():
    import game
    tmp = tempfile.mkdtemp()
    game.DATA_DIR = tmp
    game.CATS_DIR = os.path.join(tmp, "cats")
    game.EXPORT_DIR = os.path.join(tmp, "exports")
    game.PROFILES_INDEX = os.path.join(tmp, "profiles.json")
    g = game.LittleCatGame()
    g.life = None
    g.companion = None
    g.visitors = VisitorSchedule(os.path.join(tmp, "visitors.json"))
    return game, g


def test_game_visit_adds_album_and_can_be_adopted():
    game, g = _headless_game()
    g.cat.energy = 80
    g.start_visit({"name": "Mochi", "coat": "grey", "playful": 0.8})
    assert g.visitors.visited_today()
    seen_visitor_drawn = False
    for _ in range(90 * FPS):
        g.update()
        seen_visitor_drawn |= g.visitor_visual() is not None
        if g.visit is None:
            break
    assert g.visit is None and seen_visitor_drawn
    assert any(e["kind"] == "visitor" and e["name"] == "Mochi" for e in g.cat.album)
    host = g.cat
    g.adopt_visitor(collection.adoptable(host)[0])
    assert g.cat.name == "Mochi" and g.cat.coat == "grey" and len(g.cats) == 2
    assert g.display.coat == "grey", "the adopted cat keeps its fur"
    assert collection.adoptable(host, taken_names=g.profile_names) == []
    g.next_cat()
    assert g.cat is host and g.display.coat == "ginger"


def test_game_unlock_announces_and_wear_shows_on_cat():
    game, g = _headless_game()
    g.cat.time_together = 3700
    g.check_unlocks()
    assert "bow" in g.cat.unlocked and g.speech and g.speech["priority"] == 4
    assert any(e["kind"] == "unlock" for e in g.cat.album)
    g.wear("bow")
    assert g.cat.accessory == "bow" and g.display.accessory == "bow"
    g.wear("crown")                                   # locked: ignored
    assert g.cat.accessory == "bow"
    g.display.render(g.cat.get_status(), "idle")      # draws without errors
    g.show_album()
    assert g.album_timer > 0 and g.album_lines()


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
            import traceback
            traceback.print_exc()
            print(f"  ERR  {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
