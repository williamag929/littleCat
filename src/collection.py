"""
Collection and visitors (Phase 4): wardrobe, album and the occasional visiting cat.

Pure logic, no pygame - the game draws what this module decides.

    ACCESSORIES      8 pixel-art accessories, each unlocked by time together,
                     bond, focus sessions, arcade records or visitors met.
    album            a list of dicts saved inside the cat's brain file.
    VisitorSchedule  at most ONE visitor per day, persisted in a tiny JSON file.
    Visit            the visitor's little story: arrive -> sniff -> play -> leave.
                     It always leaves (hard time limit) and there is never more than one.
"""

import json
import os
import random
from datetime import date

# Coats: (fur, dark stripes, cream belly/paws, pink nose/ears)
COATS = {
    "ginger": ((247, 160, 72), (214, 112, 44), (255, 228, 190), (244, 150, 160)),
    "grey": ((156, 160, 170), (108, 112, 124), (226, 228, 234), (240, 160, 170)),
    "black": ((66, 62, 72), (40, 37, 45), (128, 124, 134), (230, 140, 150)),
    "cream": ((242, 214, 168), (214, 178, 128), (255, 244, 224), (244, 160, 165)),
    "brown": ((156, 104, 72), (108, 70, 46), (222, 192, 160), (236, 150, 150)),
    "white": ((246, 244, 240), (214, 208, 202), (255, 255, 255), (246, 166, 176)),
    "blue": ((124, 142, 178), (88, 102, 138), (212, 220, 236), (236, 160, 176)),
    "siamese": ((238, 224, 200), (112, 82, 62), (252, 244, 230), (230, 150, 150)),
}
DEFAULT_COAT = "ginger"

VISITOR_NAMES = ["Mochi", "Pumpkin", "Luna", "Biscuit", "Tofu", "Ziggy", "Nala", "Pepper",
                 "Olive", "Sushi", "Miso", "Cleo", "Pixel", "Nori", "Poppy", "Waffles"]

# key -> label, icon, slot, (requirement, amount), hint shown while locked
ACCESSORIES = {
    "bow": ("Pink bow", "🎀", "head", ("together_hours", 1), "1 h together"),
    "bell": ("Bell collar", "🔔", "neck", ("trust", 50), "bond 50"),
    "glasses": ("Glasses", "👓", "face", ("focus_sessions", 3), "3 focus sessions"),
    "flower": ("Flower", "🌸", "head", ("visitors", 1), "meet a visitor"),
    "scarf": ("Scarf", "🧣", "neck", ("together_hours", 5), "5 h together"),
    "party": ("Party hat", "🥳", "head", ("achievements", 4), "4 achievements"),
    "crown": ("Crown", "👑", "head", ("best_rally", 10), "pong rally of 10"),
    "tophat": ("Top hat", "🎩", "head", ("visitors", 3), "meet 3 visitors"),
}

ALBUM_MAX = 80


# ---------------------------------------------------------------- unlocks
def progress(cat, best_rally=0):
    """The numbers that unlock accessories."""
    return {
        "together_hours": getattr(cat, "time_together", 0.0) / 3600.0,
        "trust": getattr(cat, "trust", 0),
        "focus_sessions": getattr(cat, "focus_sessions", 0),
        "visitors": len({e.get("name") for e in getattr(cat, "album", []) if e.get("kind") == "visitor"}),
        "achievements": len(getattr(cat, "achievements", ())),
        "best_rally": best_rally,
    }


def unlocked(cat, best_rally=0):
    """Accessory keys the cat has earned (in catalog order)."""
    p = progress(cat, best_rally)
    return [k for k, (_, _, _, (req, amount), _) in ACCESSORIES.items() if p.get(req, 0) >= amount]


def new_unlocks(cat, best_rally=0):
    """Keys earned since last time; remembers them in cat.unlocked (once each)."""
    have = set(getattr(cat, "unlocked", []))
    fresh = [k for k in unlocked(cat, best_rally) if k not in have]
    if fresh:
        cat.unlocked = list(getattr(cat, "unlocked", [])) + fresh
    return fresh


def equip(cat, key):
    """Wear an accessory (only if unlocked) or None to take it off. Returns True if it changed."""
    if key is not None and key not in getattr(cat, "unlocked", []):
        return False
    changed = getattr(cat, "accessory", None) != key
    cat.accessory = key
    return changed


# ---------------------------------------------------------------- album
def add_album(cat, kind, title, detail="", today=None, **extra):
    """Add an album entry. Records replace older records; the album keeps ALBUM_MAX entries."""
    album = getattr(cat, "album", None)
    if album is None:
        album = cat.album = []
    if kind == "record":
        album[:] = [e for e in album if e.get("kind") != "record" or e.get("title") != title]
    entry = {"kind": kind, "title": title, "detail": detail,
             "day": (today or date.today()).isoformat()}
    entry.update(extra)
    album.append(entry)
    del album[:-ALBUM_MAX]
    return entry


def adoptable(cat, taken_names=()):
    """Visitors from the album that could become your own cat (each once, newest first)."""
    seen, out = set(taken_names), []
    for e in reversed(getattr(cat, "album", [])):
        if e.get("kind") == "visitor" and not e.get("adopted") and e.get("name") not in seen:
            seen.add(e["name"])
            out.append(e)
    return out


def mark_adopted(cat, name):
    for e in getattr(cat, "album", []):
        if e.get("kind") == "visitor" and e.get("name") == name:
            e["adopted"] = True


# ---------------------------------------------------------------- visitors
class VisitorSchedule:
    """At most one visitor a day, remembered on disk so restarts don't cheat."""

    MEAN_WAIT = 90 * 60     # with everything calm, a visitor shows up after ~1.5 h on average
    WARMUP = 120            # never in the first two minutes after starting

    def __init__(self, path=None, rng=None, today=date.today):
        self.path = path
        self.rng = rng or random.Random()
        self.today = today
        self.uptime = 0.0
        self.last_day = None
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.last_day = json.load(f).get("last_day")
            except Exception:
                self.last_day = None

    def visited_today(self):
        return self.last_day == self.today().isoformat()

    def should_visit(self, dt, calm):
        """Call every frame; True at most once per day, only while things are calm."""
        self.uptime += dt
        if self.uptime < self.WARMUP or not calm or self.visited_today():
            return False
        return self.rng.random() < dt / self.MEAN_WAIT

    def mark(self):
        self.last_day = self.today().isoformat()
        if self.path:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump({"last_day": self.last_day}, f)
            except Exception:
                pass


def make_visitor(rng=None, home_coat=DEFAULT_COAT, avoid_names=()):
    rng = rng or random.Random()
    coats = [c for c in COATS if c != home_coat]
    names = [n for n in VISITOR_NAMES if n not in avoid_names] or VISITOR_NAMES
    return {"name": rng.choice(names), "coat": rng.choice(coats),
            "playful": round(rng.uniform(0.3, 1.0), 2)}


class Visit:
    """One visiting cat. Positions are in overlay pixels; y follows the host cat's floor."""

    SPEED = 130.0
    SNIFF = 3.0
    PLAY = 7.0
    MAX_LIFETIME = 75.0     # whatever happens, it goes home

    def __init__(self, visitor, width, host_x, host_y, rng=None):
        self.rng = rng or random.Random()
        self.visitor = visitor
        self.width = width
        self.side = -1 if host_x > width / 2 else 1          # walks in from the nearest screen edge
        self.x = -60.0 if self.side > 0 else width + 60.0
        self.y = host_y
        self.state = "arrive"
        self.timer = 0.0
        self.age = 0.0
        self.pose = "walk"
        self.facing_right = self.side > 0
        self.hop = 0.0
        self.events = []

    @property
    def done(self):
        return self.state == "gone"

    def _walk_to(self, tx, dt):
        dx = tx - self.x
        step = self.SPEED * dt
        self.facing_right = dx > 0
        if abs(dx) <= step:
            self.x = tx
            return True
        self.x += step if dx > 0 else -step
        return False

    def update(self, dt, host_x, host_y):
        """Advance; returns the host cat's pose and facing while the visit owns it (or None)."""
        self.age += dt
        self.timer += dt
        self.y = host_y
        if self.age > self.MAX_LIFETIME and self.state not in ("leave", "gone"):
            self._leave()
        meet_x = host_x - self.side * 70
        host = None
        if self.state == "arrive":
            self.pose = "walk"
            if self._walk_to(meet_x, dt):
                self.state, self.timer = "sniff", 0.0
                self.events.append("arrived")
            host = ("sit", self.x > host_x)
        elif self.state == "sniff":
            self.pose = "sit"
            self.facing_right = host_x > self.x
            host = ("sit", self.x > host_x)
            if self.timer >= self.SNIFF:
                self.state, self.timer = "play", 0.0
                self.events.append("play")
        elif self.state == "play":
            # little hops back and forth, both cats in the pounce pose
            self.pose = "play"
            wobble = 40 * (1 if int(self.timer / 1.2) % 2 == 0 else -1)
            self._walk_to(meet_x + wobble, dt)
            self.facing_right = host_x > self.x
            self.hop = abs(((self.timer * 2.5) % 2) - 1)
            host = ("play", self.x > host_x)
            if self.timer >= self.PLAY:
                self._leave()
        elif self.state == "leave":
            self.pose = "walk"
            self.hop = 0.0
            exit_x = -80.0 if self.side > 0 else self.width + 80.0
            if self._walk_to(exit_x, dt):
                self.state = "gone"
                self.events.append("gone")
        return host

    def _leave(self):
        self.state, self.timer = "leave", 0.0
        self.events.append("leaving")

    def pop_events(self):
        ev, self.events = self.events, []
        return ev
