"""
perception.py - find the ball and the paddle in a frame (numpy only, no OpenCV).

No calibration needed:
  * background  = the most common colour of the frame
  * foreground  = pixels clearly different from the background
  * static      = foreground that has stayed put for a while (walls, score...)
  * paddle      = the widest horizontal run of foreground in the bottom band
  * ball        = the small blob of NON-static foreground above that band

Optional colours from a profile (`ball_color`, `paddle_color`) make it even
more robust when a game has a busy background.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from .state import Observation


def _mode_color(frame: np.ndarray) -> np.ndarray:
    """Most common colour (quantised) - the background of most paddle games."""
    q = (frame[::4, ::4] // 16).reshape(-1, 3).astype(np.int32)
    keys = q[:, 0] * 256 + q[:, 1] * 16 + q[:, 2]
    k = np.bincount(keys).argmax()
    return np.array([(k // 256) * 16 + 8, ((k // 16) % 16) * 16 + 8, (k % 16) * 16 + 8], dtype=np.int32)


def _color_mask(frame: np.ndarray, color, tol: int) -> np.ndarray:
    diff = np.abs(frame.astype(np.int16) - np.array(color, dtype=np.int16)).max(axis=2)
    return diff <= tol


def _longest_run(cols: np.ndarray) -> Optional[Tuple[int, int]]:
    """Longest run of True in a 1-D bool array -> (start, end_exclusive)."""
    if not cols.any():
        return None
    padded = np.concatenate(([0], cols.astype(np.int8), [0]))
    edges = np.flatnonzero(np.diff(padded))
    starts, ends = edges[::2], edges[1::2]
    i = int(np.argmax(ends - starts))
    return int(starts[i]), int(ends[i])


class Detector:
    def __init__(self, bottom_band: float = 0.18, tolerance: int = 40, downsample: int = 1,
                 ball_color=None, paddle_color=None, static_frames: int = 20,
                 min_paddle: int = 12):
        self.bottom_band = bottom_band
        self.tol = tolerance
        self.auto_ds = downsample in (None, "auto", 0)
        self.ds = 1 if self.auto_ds else max(1, int(downsample))
        self.ball_size = 6.0
        self.ball_color = ball_color
        self.paddle_color = paddle_color
        self.static_frames = static_frames
        self.min_paddle = min_paddle
        self.still = None          # per-pixel count of consecutive foreground frames
        self.bg = None
        self.frames = 0
        self.paddle_y: Optional[float] = None
        self.last_ball = None
        self._paddle_bottom = 0

    def observe(self, frame: np.ndarray) -> Observation:
        """frame: HxWx3 uint8 RGB of the game area."""
        if self.auto_ds:   # big capture (scaled display): work at ~320 px wide, plenty for a ball
            self.ds = max(1, int(round(frame.shape[1] / 320)))
            self.auto_ds = False
        f = frame[::self.ds, ::self.ds]
        h, w = f.shape[:2]
        if self.bg is None or self.frames % 30 == 0:
            self.bg = _mode_color(f)
        self.frames += 1
        fg = np.abs(f.astype(np.int16) - self.bg.astype(np.int16)).max(axis=2) > self.tol

        if self.still is None or self.still.shape != fg.shape:
            self.still = np.zeros(fg.shape, dtype=np.int16)
        self.still = np.where(fg, np.minimum(self.still + 1, 1000), 0)

        band_top = int(h * (1 - self.bottom_band))
        paddle_x, paddle_y, paddle_w = self._paddle(f, fg, band_top)
        if paddle_y is not None:
            self.paddle_y = paddle_y
        # Look for the ball everywhere except on the paddle itself (a moving paddle is not static,
        # and the ball is right next to it at the very moment that matters)
        hide = None
        if paddle_x is not None:
            top = int(paddle_y / self.ds)
            half = int(paddle_w / 2) + 1
            px = int(paddle_x)
            hide = (max(0, top - 1), self._paddle_bottom + 2, max(0, px - half - 1), px + half + 2)
        ball = self._ball(f, fg, h, hide)

        s = self.ds
        return Observation(
            ball=(ball[0] * s, ball[1] * s) if ball else None,
            paddle_x=paddle_x * s if paddle_x is not None else None,
            width=w * s, height=h * s,
            paddle_y=(self.paddle_y if self.paddle_y is not None else band_top * s),
            paddle_w=(paddle_w or 48 / s) * s,
            ball_size=self.ball_size,
        )

    def _paddle(self, f, fg, band_top):
        band = _color_mask(f[band_top:], self.paddle_color, self.tol) if self.paddle_color else fg[band_top:]
        # ignore full-width rows (a floor/border line is not the paddle)
        rows = band.sum(axis=1)
        rows_ok = rows < band.shape[1] * 0.8
        band = band & rows_ok[:, None]
        counts = band.sum(axis=1)
        if not counts.any():
            return None, None, None
        ry = int(np.argmax(counts))              # the paddle is the "heaviest" row of the band
        run = _longest_run(band[ry])
        if not run or run[1] - run[0] < self.min_paddle // self.ds:
            return None, None, None
        x0, x1 = run
        top = bottom = ry
        while top > 0 and band[top - 1, x0:x1].mean() > 0.6:   # walk up to the paddle's top edge
            top -= 1
        while bottom + 1 < band.shape[0] and band[bottom + 1, x0:x1].mean() > 0.6:
            bottom += 1
        self._paddle_bottom = band_top + bottom
        return (x0 + x1 - 1) / 2.0, float((band_top + top) * self.ds), float(x1 - x0)

    def _ball(self, f, fg, limit_y, hide=None):
        limit_y = max(1, limit_y)
        if self.ball_color:
            m = _color_mask(f[:limit_y], self.ball_color, self.tol)
        else:
            if self.frames <= self.static_frames:
                return None   # warming up: can't tell walls/score (static) from the ball yet
            m = fg[:limit_y] & (self.still[:limit_y] < self.static_frames)
            if hide is not None:
                y0, y1, x0, x1 = hide
                m[y0:y1, x0:x1] = False
        ys, xs = np.nonzero(m)
        if len(xs) < 2:
            self.last_ball = None
            return None
        # Group pixels into coarse cells; several blobs can move at once (e.g. a score
        # digit just changed), so prefer the one next to where the ball was, else the
        # most compact one.
        cell = 12 // self.ds or 1
        keys = (ys // cell) * 10000 + (xs // cell)
        uniq, counts = np.unique(keys, return_counts=True)
        cands = [(int(k), int(c)) for k, c in zip(uniq, counts) if c >= 2]
        if not cands:
            self.last_ball = None
            return None
        prev = getattr(self, "last_ball", None)
        if prev is not None:
            px, py = prev
            k = min(cands, key=lambda kc: abs((kc[0] % 10000 + 0.5) * cell - px) + abs((kc[0] // 10000 + 0.5) * cell - py))[0]
        else:
            k = max(cands, key=lambda kc: kc[1])[0]
        cx, cy = (k % 10000 + 0.5) * cell, (k // 10000 + 0.5) * cell
        near = (np.abs(xs - cx) <= cell) & (np.abs(ys - cy) <= cell)
        bx, by = float(xs[near].mean()), float(ys[near].mean())
        self.last_ball = (bx, by)
        size = (max(np.ptp(xs[near]), np.ptp(ys[near])) + 1) * self.ds
        self.ball_size = 0.8 * self.ball_size + 0.2 * float(size)   # smoothed
        return bx, by
