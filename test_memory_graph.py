"""
Tests for the JSON memory graph and the utility-AI autonomy layer.
Run: python test_memory_graph.py   (or: pytest test_memory_graph.py)
"""

import json
import os
import sys
import tempfile
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import autonomy  # noqa: E402
from cat_brain import CatBrain  # noqa: E402
from memory_graph import MemoryGraph  # noqa: E402

HUNGRY = {"happiness": 60, "hunger": 90, "energy": 60, "trust": 60}


def test_record_builds_nodes_edges_and_chain():
    g = MemoryGraph()
    g.record("eat", "You fed the cat!", 1.0, age=1.0, source="player", state=HUNGRY)
    ep2 = g.record("play", "Played with Ball", 0.5, age=1.1, source="player", context="human_nearby", state=HUNGRY)
    assert "action:eat" in g.nodes and "stimulus:ball" in g.nodes and "stimulus:food" in g.nodes
    assert "state:hunger:high|in_state|action:eat" in g.edges
    assert g.habit_after("eat")[0][0] == "play"
    assert ep2["prev"] == "ep_000001"
    assert "context:human_nearby" in ep2["links"]


def test_expectation_learns_good_and_bad():
    g = MemoryGraph()
    for i in range(5):
        g.record("eat", "fed", 1.0, age=i * 0.01, state=HUNGRY)
        g.record("hide", "hid", -0.8, age=i * 0.01, state=HUNGRY)
    tags = ["hunger:high"]
    assert g.expectation("eat", tags) > 0.5
    assert g.expectation("hide", tags) < -0.4
    assert g.expectation("train", tags) == 0.0


def test_decay_forgets_and_prunes():
    g = MemoryGraph(half_life_days=1.0)
    g.record("groom", "brush", 0.5, age=0.0)
    before = len(g.edges)
    g.decay(30.0)  # 30 half-lives later
    assert len(g.edges) < before


def test_consolidation_keeps_salient_memories():
    g = MemoryGraph(max_episodes=20)
    g.record("purr", "First time trusting you", 1.0, age=0.0)  # novel + strong
    for i in range(40):
        g.record("rest", "Cat is resting", 0.1, age=0.1 + i * 0.001)
    assert len(g.episodes) == 20
    assert any(ep["action"] == "purr" for ep in g.episodes)


def test_json_roundtrip():
    g = MemoryGraph()
    g.record("eat", "fed", 1.0, age=1.0, state=HUNGRY)
    data = json.loads(json.dumps(g.to_dict()))
    g2 = MemoryGraph.from_dict(data)
    assert g2.to_dict() == g.to_dict()


def test_brain_save_load_and_legacy_migration():
    # Self-contained legacy save (old format: flat memories, no memory_graph key)
    legacy = {"name": "Old", "age": 3.0, "memories": [
        {"timestamp": "2026-02-06T16:52:15", "action": a, "response": r, "reward": w, "age": 2.0 + i * 0.1}
        for i, (a, r, w) in enumerate([("eat", "You fed the cat!", 1.0), ("play", "Played with Ball", 0.5),
                                       ("sleep", "Cat yawns and sleeps", 0.5)] * 4)]}
    with tempfile.TemporaryDirectory() as tmp:
        legacy_path = os.path.join(tmp, "legacy.json")
        with open(legacy_path, "w") as fh:
            json.dump(legacy, fh)
        cat = CatBrain("Old")
        cat.load_brain(legacy_path)  # old format -> graph rebuilt from flat memories
        assert len(cat.memory_graph.episodes) == 12
        assert "stimulus:ball" in cat.memory_graph.nodes
        cat.learn_from_interaction("eat", "You fed the cat!", 1.0, source="player")
        path = os.path.join(tmp, "cat.json")
        cat.save_brain(path)
        clone = CatBrain("Whiskers")
        clone.load_brain(path)
    assert clone.memory_graph.to_dict() == cat.memory_graph.to_dict()


def test_self_reward_is_damped():
    a, b = CatBrain("A"), CatBrain("A")
    for _ in range(10):
        a.learn_from_interaction("play", "x", 1.0, source="player")
        b.learn_from_interaction("play", "x", 1.0, source="self")
    assert a.behavior_weights["play"] > b.behavior_weights["play"]


def test_utility_prefers_urgent_needs():
    scores = autonomy.score_actions(HUNGRY, {"playful": 0.5, "calm": 0.5, "curious": 0.5, "social": 0.5}, hour=12)
    assert max(scores, key=scores.get) == "eat"
    tired = {"happiness": 60, "hunger": 20, "energy": 5, "trust": 60}
    scores = autonomy.score_actions(tired, {"playful": 0.5, "calm": 0.5, "curious": 0.5, "social": 0.5}, hour=14)
    assert max(scores, key=scores.get) in ("sleep", "rest")


def test_boredom_reduces_repetition():
    needs = {"happiness": 50, "hunger": 20, "energy": 80, "trust": 70}
    p = {"playful": 0.9, "calm": 0.3, "curious": 0.5, "social": 0.5}
    fresh = autonomy.score_actions(needs, p, hour=19)["play"]
    bored = autonomy.score_actions(needs, p, hour=19, recent=["play"] * 4)["play"]
    assert bored < fresh * 0.5


def test_decisions_are_varied_not_stuck():
    cat = CatBrain("Variety")
    cat.hunger, cat.energy, cat.happiness, cat.trust = 20, 80, 60, 70
    picks = Counter(cat.decide_action("human_nearby")[0] for _ in range(300))
    assert len(picks) >= 4, picks


if __name__ == "__main__":
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
