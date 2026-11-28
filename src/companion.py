"""
Work companion (Phase 3): the cat notices *that* you are working, never *what*.

Everything here comes from two numbers Windows gives any program:
  - when the last input happened (GetLastInputInfo), and
  - where the cursor is.
No key is read, no screen is captured, nothing is logged.

    away / back   no input for AWAY_AFTER seconds -> the cat naps and its needs
                  slow down; the first input after that -> one "welcome back".
    focus         a pomodoro: the cat curls up and stays silent, then cheers.
    rhythm        how often the input timestamp changes while the cursor stays
                  still ~ typing intensity (Bongo-Cat paws, no keylogger).
    together      seconds you and the cat spent with the human present.
"""

import time
from collections import deque

import desktop

AWAY_AFTER = 300.0        # 5 min without input -> away
BACK_IDLE = 2.0           # input in the last 2 s after being away -> back
AWAY_NEED_RATE = 0.2      # needs move 5x slower while you are away
FOCUS_MINUTES = 25
RHYTHM_WINDOW = 2.0       # seconds of history for the typing rhythm
TYPING_RATE = 2.5         # input changes per second (cursor still) that count as typing
RHYTHM_FULL = 8.0         # changes per second that count as full speed


class Companion:
    def __init__(self, provider=desktop, clock=time.monotonic, away_after=AWAY_AFTER,
                 presence=True, rhythm=True):
        self.provider = provider
        self.clock = clock
        self.away_after = away_after
        self.presence_enabled = presence
        self.rhythm_enabled = rhythm
        self.away = False
        self.away_started = None
        self.focus_end = None
        self.focus_minutes = 0
        self._present_mark = float("-inf")   # last moment we know you were there besides input
        self.together_seconds = 0.0     # gained since the last take_together()
        self._last_tick = None
        self._last_cursor = None
        self._samples = deque()          # times when input happened with the cursor still
        self.beat = 0                    # flips on every detected keystroke-ish input

    # ---- focus (pomodoro) ----
    @property
    def in_focus(self):
        return self.focus_end is not None

    def start_focus(self, minutes=FOCUS_MINUTES):
        self.focus_minutes = minutes
        self.focus_end = self.clock() + minutes * 60

    def cancel_focus(self):
        self.focus_end = None
        self._present_mark = self.clock()

    def focus_left(self):
        """Seconds left in the focus session (0 if none)."""
        return max(0.0, self.focus_end - self.clock()) if self.focus_end else 0.0

    # ---- rhythm ----
    def rhythm(self):
        """0..1 typing intensity over the last RHYTHM_WINDOW seconds."""
        rate = len(self._samples) / RHYTHM_WINDOW
        return min(1.0, rate / RHYTHM_FULL)

    def typing(self):
        return self.rhythm_enabled and not self.away and len(self._samples) / RHYTHM_WINDOW >= TYPING_RATE

    def need_rate(self):
        """Multiplier for how fast hunger/energy/happiness drift."""
        return AWAY_NEED_RATE if self.away else 1.0

    def take_together(self):
        """Return and reset the together time gained since the last call."""
        gained, self.together_seconds = self.together_seconds, 0.0
        return gained

    # ---- main tick ----
    def update(self, dt):
        """Advance one frame. Returns a list of events:
        ("away",), ("back", seconds_away), ("focus_done", minutes)."""
        events = []
        now = self.clock()

        if self.presence_enabled:
            # A focus session counts as presence (you may have been reading): idle restarts at its end
            idle = min(self.provider.idle_seconds(), now - self._present_mark)
            if not self.away and idle >= self.away_after and not self.in_focus:
                self.away = True
                self.away_started = now - idle
                self._samples.clear()
                events.append(("away",))
            elif self.away and idle < BACK_IDLE:
                self.away = False
                events.append(("back", max(0.0, now - (self.away_started or now))))
                self.away_started = None

        if self.rhythm_enabled:
            self._sample_rhythm(now)

        if self.focus_end is not None and now >= self.focus_end:
            events.append(("focus_done", self.focus_minutes))
            self.focus_end = None
            self._present_mark = now

        if not self.away:
            self.together_seconds += dt
        return events

    def _sample_rhythm(self, now):
        tick = self.provider.last_input_tick()
        cursor = self.provider.cursor_pos()
        if tick is not None and self._last_tick is not None and tick != self._last_tick:
            if cursor == self._last_cursor:   # input without mouse motion ~ keys / clicks
                self._samples.append(now)
                self.beat ^= 1
        self._last_tick, self._last_cursor = tick, cursor
        while self._samples and now - self._samples[0] > RHYTHM_WINDOW:
            self._samples.popleft()


def format_together(seconds):
    """'3 h 20 min' / '12 min' for the Stats card."""
    minutes = int(seconds // 60)
    h, m = divmod(minutes, 60)
    return f"{h} h {m:02d} min" if h else f"{m} min"
