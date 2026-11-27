"""
Autonomy - Utility AI for LittleCat (needs-driven, as in The Sims / Creatures).

Each candidate action gets a score from response curves over the cat's needs,
multiplied by personality, circadian rhythm, memory (what it learned feels
good in this situation) and a boredom penalty for repeating itself. The best
scored action wins (with softmax-style noise so the cat stays unpredictable),
and the module also returns a human-readable *reason* that the UI can show in
the thought bubble ("so hungry...", "wanna play!").

Pure functions, no pygame: easy to unit-test and to tune.
"""

from __future__ import annotations

import math
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------- curves
def rising(x: float, midpoint: float = 50.0, steepness: float = 0.12) -> float:
    """Logistic 0..1 that rises with x (0-100)."""
    return 1.0 / (1.0 + math.exp(-steepness * (x - midpoint)))


def falling(x: float, midpoint: float = 50.0, steepness: float = 0.12) -> float:
    return 1.0 - rising(x, midpoint, steepness)


def circadian_activity(hour: float) -> float:
    """Cats are crepuscular: active at dawn (~6h) and dusk (~19h), sleepy midday/night.

    Returns 0..1 activity level for a local hour (0-24).
    """
    dawn = math.exp(-((hour - 6.5) ** 2) / 4.0)
    dusk = math.exp(-((hour - 19.0) ** 2) / 5.0)
    return max(0.15, min(1.0, dawn + dusk))


# ---------------------------------------------------------------- reasons
REASONS = {
    "eat": "so hungry...",
    "sleep": "sleepy...",
    "rest": "need a break",
    "play": "wanna play!",
    "purr": "pet me?",
    "talk": "mrrp? hey you",
    "groom": "fur check",
    "scratch": "sharpening claws",
    "hide": "don't feel safe",
    "train": "teach me a trick!",
    "perch": "up there looks comfy",
    "chase_cursor": "what's that?!",
}


def score_actions(needs: Dict[str, float], personality: Dict[str, float], *,
                  learned_weights: Optional[Dict[str, float]] = None,
                  memory=None, tags: Tuple[str, ...] = (), context: Optional[str] = None,
                  hour: Optional[float] = None, recent: Optional[List[str]] = None
                  ) -> Dict[str, float]:
    """Return {action: utility >= 0} for every action the cat can choose."""
    h = needs.get("happiness", 50)
    hunger = needs.get("hunger", 30)
    energy = needs.get("energy", 70)
    trust = needs.get("trust", 30)
    playful = personality.get("playful", 0.5)
    calm = personality.get("calm", 0.5)
    curious = personality.get("curious", 0.5)
    social = personality.get("social", 0.5)
    if hour is None:
        now = datetime.now()
        hour = now.hour + now.minute / 60.0
    activity = circadian_activity(hour)
    human_near = context == "human_nearby"

    tired = falling(energy, 35, 0.15)
    bored = falling(h, 55, 0.08)
    lonely = falling(trust, 70, 0.05) * (0.5 + social)

    base = {
        "eat": rising(hunger, 60, 0.15),
        "sleep": tired * (1.3 - activity) * (0.8 + calm * 0.4),
        "rest": 0.5 * tired + 0.25 * (1.0 - activity),
        "play": rising(energy, 45, 0.1) * falling(hunger, 75, 0.15) * activity * (0.6 + playful) * (0.6 + bored),
        "purr": (0.4 + lonely) * rising(trust, 45, 0.1) * (1.0 if human_near else 0.4),
        "talk": (0.3 + lonely + 0.4 * rising(hunger, 70, 0.15)) * (0.5 + social) * (1.0 if human_near else 0.5),
        "groom": 0.25 + 0.2 * calm + 0.15 * (1.0 - activity),
        "scratch": 0.2 + 0.25 * curious * activity,
        "hide": falling(trust, 30, 0.15) * (1.2 - social),
        "train": rising(energy, 40, 0.1) * rising(trust, 50, 0.1) * (0.4 + curious) * (1.0 if human_near else 0.3),
    }

    recent = recent or []
    scores = {}
    for action, utility in base.items():
        # Learned preference (0..1 weights) nudges but does not dominate needs
        if learned_weights and action in learned_weights:
            utility *= 0.75 + 0.5 * float(learned_weights[action])
        # Associative memory: "last time I did this in this situation it felt..."
        if memory is not None:
            utility *= 1.0 + 0.4 * memory.expectation(action, tags, context)
        # Boredom: repeating the same thing gets less attractive (not for urgent needs)
        repeats = recent.count(action)
        if repeats and action not in ("eat", "sleep"):
            utility *= 0.75 ** repeats
        scores[action] = max(0.0, utility)
    return scores


def score_desktop(needs: Dict[str, float], personality: Dict[str, float], *,
                  hour: Optional[float] = None, memory=None,
                  tags: Tuple[str, ...] = (), context: Optional[str] = None,
                  cursor_speed: float = 0.0, cursor_dist: float = 9999.0,
                  perch_available: bool = False) -> Dict[str, float]:
    """Utilities (0..~1) for the desktop behaviours: climbing on a window and chasing the cursor.

    They are evaluated by desktop_life alongside the classic actions, with the same
    ingredients: needs, personality, time of day and what the cat remembers enjoying.
    """
    hunger = needs.get("hunger", 30)
    energy = needs.get("energy", 70)
    playful = personality.get("playful", 0.5)
    curious = personality.get("curious", 0.5)
    calm = personality.get("calm", 0.5)
    if hour is None:
        now = datetime.now()
        hour = now.hour + now.minute / 60.0
    activity = circadian_activity(hour)
    ok_body = rising(energy, 30, 0.12) * falling(hunger, 80, 0.15)

    # Cats love high places: curious and calm cats climb up to watch the world
    perch = (0.35 + 0.4 * curious + 0.25 * calm) * ok_body * (0.5 + 0.5 * activity) if perch_available else 0.0
    # A fast cursor close by is prey: playful, energetic cats can't resist
    moving = rising(cursor_speed, 450, 0.012)
    near = falling(cursor_dist, 420, 0.015)
    chase = moving * near * rising(energy, 45, 0.1) * (0.4 + playful) * (0.5 + 0.5 * activity)

    scores = {"perch": perch, "chase_cursor": chase}
    if memory is not None:
        for action in scores:
            scores[action] *= 1.0 + 0.4 * memory.expectation(action, tags, context)
    return {a: max(0.0, s) for a, s in scores.items()}


def choose(scores: Dict[str, float], temperature: float = 0.15,
           rng: Optional[random.Random] = None) -> Tuple[str, float, str]:
    """Softmax pick. Returns (action, confidence 0..1, reason)."""
    rng = rng or random
    actions = list(scores)
    best = max(scores.values()) if scores else 0.0
    exps = [math.exp((scores[a] - best) / max(1e-6, temperature)) for a in actions]
    total = sum(exps)
    r = rng.random() * total
    acc = 0.0
    picked = actions[-1]
    for a, e in zip(actions, exps):
        acc += e
        if r <= acc:
            picked = a
            break
    confidence = min(1.0, scores[picked] / best) * min(1.0, best) if best > 0 else 0.0
    return picked, confidence, REASONS.get(picked, picked)
