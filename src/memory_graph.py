"""
Memory Graph - associative, JSON-native memory for LittleCat.

Replaces the flat "last 20 events" list with a small knowledge graph:

* nodes    -> concepts the cat knows about (actions, stimuli/toys, who acted,
              context, internal-state tags such as "hunger:high").
* edges    -> learned associations between concepts, each with a strength
              (how well it is remembered) and a valence (good/bad, -1..1).
* episodes -> concrete events ("at age 12.3 the player fed me while I was
              hungry and it felt great"), linked to the nodes they touched and
              to the previous episode (temporal chain).

Everything is plain dicts/lists so `to_dict()` is directly JSON serialisable
and the file is easy to inspect, diff, query or feed to other tools.

Learning rules (cheap, game-friendly):
* Hebbian reinforcement: strength += lr * (1 - strength) each co-activation.
* Valence is an exponential moving average of the rewards seen on that edge.
* Forgetting: strength decays exponentially with in-game age (half-life).
* Consolidation: when the episode buffer is full, the least *salient*
  episodes are forgotten first (salience = |reward| + novelty + recency),
  so emotional / first-time memories survive longer than routine ones.
"""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

SCHEMA = "littlecat.memory/v1"

# Relations used in the graph (kept explicit so the JSON is self-describing)
REL_FOLLOWED_BY = "followed_by"    # action -> action (habits / sequences)
REL_REWARDED_BY = "rewarded_by"    # action -> source (who made it feel good/bad)
REL_IN_STATE = "in_state"          # state tag -> action (what helps when X)
REL_IN_CONTEXT = "in_context"      # context -> action
REL_INVOLVES = "involves"          # action -> stimulus (toy, food, mini-game)

# Words in free-text responses that become stimulus nodes
STIMULUS_PATTERNS = {
    "ball": r"\bball\b",
    "fish": r"\bfish\b",
    "mouse": r"\bmouse\b",
    "bird": r"\bbird\b",
    "food": r"\b(fed|food|meal|eat)\b",
    "mini_game": r"mini-?game",
    "brush": r"\bgroom",
    "voice": r"\b(talk|chirp|voice)\b",
}


def _bin_label(value: float) -> str:
    if value >= 70:
        return "high"
    if value <= 30:
        return "low"
    return "mid"


def state_tags(happiness: float, hunger: float, energy: float, trust: float) -> List[str]:
    """Turn the 0-100 emotional state into a few discrete, readable tags."""
    return [
        f"happiness:{_bin_label(happiness)}",
        f"hunger:{_bin_label(hunger)}",
        f"energy:{_bin_label(energy)}",
        f"trust:{_bin_label(trust)}",
    ]


def extract_stimuli(text: str) -> List[str]:
    text = (text or "").lower()
    return [name for name, pattern in STIMULUS_PATTERNS.items() if re.search(pattern, text)]


class MemoryGraph:
    """Associative memory stored as a JSON-friendly graph."""

    def __init__(self, max_episodes: int = 200, learning_rate: float = 0.15,
                 valence_rate: float = 0.25, half_life_days: float = 30.0,
                 prune_below: float = 0.02):
        self.max_episodes = max_episodes
        self.learning_rate = learning_rate
        self.valence_rate = valence_rate
        self.half_life_days = half_life_days
        self.prune_below = prune_below

        self.nodes: Dict[str, dict] = {}
        self.edges: Dict[str, dict] = {}
        self.episodes: List[dict] = []
        self._next_episode = 1
        self._last_decay_age = 0.0

    # ------------------------------------------------------------------ write
    def record(self, action: str, response: str, reward: float, *, age: float,
               source: str = "player", context: Optional[str] = None,
               state: Optional[Dict[str, float]] = None,
               timestamp: Optional[str] = None) -> dict:
        """Store one experience and update every association it touches."""
        self.decay(age)
        reward = max(-1.0, min(1.0, float(reward)))
        state = state or {}
        tags = state_tags(state.get("happiness", 50), state.get("hunger", 30),
                          state.get("energy", 70), state.get("trust", 30)) if state else []
        stimuli = extract_stimuli(response)

        action_id = self._touch_node("action", action, reward, age)
        source_id = self._touch_node("source", source, reward, age)
        linked = [action_id, source_id]

        self._reinforce(action_id, REL_REWARDED_BY, source_id, reward, age)
        for tag in tags:
            tag_id = self._touch_node("state", tag, reward, age)
            self._reinforce(tag_id, REL_IN_STATE, action_id, reward, age)
            linked.append(tag_id)
        if context:
            ctx_id = self._touch_node("context", context, reward, age)
            self._reinforce(ctx_id, REL_IN_CONTEXT, action_id, reward, age)
            linked.append(ctx_id)
        for stim in stimuli:
            stim_id = self._touch_node("stimulus", stim, reward, age)
            self._reinforce(action_id, REL_INVOLVES, stim_id, reward, age)
            linked.append(stim_id)

        prev = self.episodes[-1] if self.episodes else None
        if prev is not None:
            prev_action_id = f"action:{prev['action']}"
            if prev_action_id in self.nodes:
                self._reinforce(prev_action_id, REL_FOLLOWED_BY, action_id, reward, age)

        novelty = 1.0 / (1.0 + self.nodes[action_id]["count"] - 1)
        episode = {
            "id": f"ep_{self._next_episode:06d}",
            "t": timestamp or datetime.now().isoformat(timespec="seconds"),
            "age": round(age, 3),
            "action": action,
            "source": source,
            "context": context,
            "response": response,
            "reward": round(reward, 3),
            "state": {k: round(v, 1) for k, v in state.items()},
            "tags": tags + [f"stimulus:{s}" for s in stimuli],
            "links": linked,
            "prev": prev["id"] if prev else None,
            "salience": round(abs(reward) + novelty, 3),
        }
        self._next_episode += 1
        self.episodes.append(episode)
        self._consolidate(age)
        return episode

    def decay(self, age: float) -> None:
        """Forget a little: exponential decay of edge strength over in-game days."""
        elapsed = age - self._last_decay_age
        if elapsed <= 0.25:  # decay at most every ~6 in-game hours
            return
        factor = 0.5 ** (elapsed / self.half_life_days)
        dead = []
        for edge_id, edge in self.edges.items():
            edge["strength"] *= factor
            if edge["strength"] < self.prune_below:
                dead.append(edge_id)
        for edge_id in dead:
            del self.edges[edge_id]
        self._last_decay_age = age

    # ------------------------------------------------------------------ read
    def neighbors(self, node_id: str, rel: Optional[str] = None,
                  direction: str = "out") -> List[dict]:
        """Edges leaving (or entering) a node, strongest first."""
        key = "from" if direction == "out" else "to"
        found = [e for e in self.edges.values()
                 if e[key] == node_id and (rel is None or e["rel"] == rel)]
        return sorted(found, key=lambda e: e["strength"], reverse=True)

    def expectation(self, action: str, tags: Iterable[str] = (), context: Optional[str] = None) -> float:
        """Expected feeling (-1..1) of doing `action` given current tags/context.

        Strength-weighted average of the valences of every remembered
        association pointing at this action. 0.0 means "no idea yet".
        """
        target = f"action:{action}"
        sources = [f"state:{t}" for t in tags]
        if context:
            sources.append(f"context:{context}")
        num = den = 0.0
        for src in sources:
            for rel in (REL_IN_STATE, REL_IN_CONTEXT):
                edge = self.edges.get(self._edge_id(src, rel, target))
                if edge:
                    num += edge["valence"] * edge["strength"]
                    den += edge["strength"]
        return num / den if den else 0.0

    def habit_after(self, action: str, top: int = 3) -> List[Tuple[str, float]]:
        """What the cat tends to do after `action` (sequence memory)."""
        return [(e["to"].split(":", 1)[1], round(e["strength"], 3))
                for e in self.neighbors(f"action:{action}", REL_FOLLOWED_BY)[:top]]

    def favorites(self, node_type: str = "stimulus", top: int = 3) -> List[Tuple[str, float]]:
        """Best-liked nodes of a type (by valence * familiarity)."""
        items = [n for n in self.nodes.values() if n["type"] == node_type]
        items.sort(key=lambda n: n["valence"] * math.log1p(n["count"]), reverse=True)
        return [(n["label"], round(n["valence"], 3)) for n in items[:top]]

    def recent_actions(self, n: int = 5) -> List[str]:
        return [ep["action"] for ep in self.episodes[-n:]]

    def recall(self, tag_or_node: str, limit: int = 5) -> List[dict]:
        """Most salient episodes that mention a node id or tag."""
        hits = [ep for ep in self.episodes
                if tag_or_node in ep["links"] or tag_or_node in ep["tags"] or ep["action"] == tag_or_node]
        hits.sort(key=lambda ep: ep["salience"], reverse=True)
        return hits[:limit]

    def summary(self) -> dict:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "episodes": len(self.episodes),
            "favorite_stimuli": self.favorites("stimulus"),
            "favorite_actions": self.favorites("action"),
        }

    # ----------------------------------------------------------- (de)serialize
    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "params": {
                "max_episodes": self.max_episodes,
                "learning_rate": self.learning_rate,
                "valence_rate": self.valence_rate,
                "half_life_days": self.half_life_days,
                "prune_below": self.prune_below,
            },
            "last_decay_age": round(self._last_decay_age, 3),
            "next_episode": self._next_episode,
            "nodes": sorted(self.nodes.values(), key=lambda n: n["id"]),
            "edges": sorted(self.edges.values(), key=lambda e: e["id"]),
            "episodes": self.episodes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryGraph":
        params = data.get("params", {})
        graph = cls(**{k: v for k, v in params.items()
                       if k in ("max_episodes", "learning_rate", "valence_rate",
                                "half_life_days", "prune_below")})
        graph.nodes = {n["id"]: dict(n) for n in data.get("nodes", [])}
        graph.edges = {e["id"]: dict(e) for e in data.get("edges", [])}
        graph.episodes = list(data.get("episodes", []))
        graph._next_episode = data.get("next_episode", len(graph.episodes) + 1)
        graph._last_decay_age = data.get("last_decay_age", 0.0)
        return graph

    @classmethod
    def from_legacy(cls, memories: Iterable[dict]) -> "MemoryGraph":
        """Build a graph from the old flat `memories` list (no state/source info)."""
        graph = cls()
        for mem in memories:
            response = mem.get("response", "")
            source = "self" if response.lower().startswith("cat ") else "player"
            graph.record(mem.get("action", "unknown"), response, mem.get("reward", 0.0),
                         age=mem.get("age", 0.0), source=source,
                         timestamp=mem.get("timestamp"))
        return graph

    # --------------------------------------------------------------- internal
    @staticmethod
    def _edge_id(src: str, rel: str, dst: str) -> str:
        return f"{src}|{rel}|{dst}"

    def _touch_node(self, node_type: str, label: str, reward: float, age: float) -> str:
        node_id = f"{node_type}:{label}"
        node = self.nodes.get(node_id)
        if node is None:
            node = {"id": node_id, "type": node_type, "label": label,
                    "count": 0, "valence": 0.0, "first_age": round(age, 3), "last_age": round(age, 3)}
            self.nodes[node_id] = node
        node["count"] += 1
        node["valence"] = round(node["valence"] + self.valence_rate * (reward - node["valence"]), 4)
        node["last_age"] = round(age, 3)
        return node_id

    def _reinforce(self, src: str, rel: str, dst: str, reward: float, age: float) -> None:
        edge_id = self._edge_id(src, rel, dst)
        edge = self.edges.get(edge_id)
        if edge is None:
            edge = {"id": edge_id, "from": src, "rel": rel, "to": dst,
                    "strength": 0.0, "valence": 0.0, "count": 0}
            self.edges[edge_id] = edge
        edge["count"] += 1
        edge["strength"] = round(edge["strength"] + self.learning_rate * (1.0 - edge["strength"]), 4)
        edge["valence"] = round(edge["valence"] + self.valence_rate * (reward - edge["valence"]), 4)
        edge["last_age"] = round(age, 3)

    def _consolidate(self, age: float) -> None:
        """Keep the episode buffer bounded, forgetting the least salient first."""
        overflow = len(self.episodes) - self.max_episodes
        if overflow <= 0:
            return
        protected = 10  # never forget the most recent few
        candidates = self.episodes[:-protected]

        def score(ep):
            recency = 1.0 / (1.0 + max(0.0, age - ep.get("age", 0.0)))
            return ep.get("salience", 0.0) + recency

        drop = {ep["id"] for ep in sorted(candidates, key=score)[:overflow]}
        self.episodes = [ep for ep in self.episodes if ep["id"] not in drop]
