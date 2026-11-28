"""
desktop.py - What the cat can "see" of the real Windows desktop.

Everything here is read-only and privacy-safe:
  * windows: position/size of visible top-level windows (titles are only used
    to skip system windows, never stored)
  * cursor position
  * monitors and their work areas (screen minus taskbar)
  * idle time via GetLastInputInfo (WHEN you last used the PC, never WHAT you typed)

Every call fails soft: on non-Windows systems or if an API errors out the
functions return empty/neutral values, so the game keeps working without
desktop features.

Coordinates returned are screen coordinates. The pure helpers at the bottom
(`perch_spots`, `spot_at`, ...) take plain tuples so they can be unit tested
anywhere.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

Rect = Tuple[int, int, int, int]  # left, top, right, bottom

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32
    try:
        _dwmapi = ctypes.windll.dwmapi
    except OSError:  # pragma: no cover
        _dwmapi = None

    _user32.GetWindowLongW.restype = ctypes.c_long
    _user32.GetWindowTextLengthW.restype = ctypes.c_int
    _kernel32.GetTickCount.restype = wintypes.DWORD

    class _LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    class _MONITORINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

    _WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    _MONITORENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
                                          ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
DWMWA_CLOAKED = 14
GA_ROOTOWNER = 3

# Shell / system windows the cat should never sit on
_SKIP_CLASSES = {
    "Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd",
    "Windows.UI.Core.CoreWindow", "ApplicationFrameInputSinkWindow",
}

MIN_PERCH_WIDTH = 120     # px of uncovered title bar needed to sit on
MIN_WINDOW_SIZE = (200, 100)


@dataclass
class WindowInfo:
    hwnd: int
    rect: Rect   # screen coords
    z: int       # 0 = topmost of the listed windows


# --------------------------------------------------------------------------
# Windows API wrappers (fail soft)
# --------------------------------------------------------------------------

def available() -> bool:
    return IS_WINDOWS


def cursor_pos() -> Optional[Tuple[int, int]]:
    """Global cursor position in screen coords (works even off the overlay)."""
    if not IS_WINDOWS:
        return None
    try:
        pt = wintypes.POINT()
        if _user32.GetCursorPos(ctypes.byref(pt)):
            return pt.x, pt.y
    except Exception:
        pass
    return None


def left_button_down() -> bool:
    """Global left-button state (lets a drag end even if the release happens off the cat)."""
    if not IS_WINDOWS:
        return False
    try:
        return bool(_user32.GetAsyncKeyState(0x01) & 0x8000)
    except Exception:
        return False


def idle_seconds() -> float:
    """Seconds since the last keyboard/mouse input anywhere (0.0 if unknown)."""
    if not IS_WINDOWS:
        return 0.0
    try:
        info = _LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(_LASTINPUTINFO)
        if _user32.GetLastInputInfo(ctypes.byref(info)):
            ticks = _kernel32.GetTickCount()
            return max(0.0, ((ticks - info.dwTime) & 0xFFFFFFFF) / 1000.0)
    except Exception:
        pass
    return 0.0


def virtual_screen() -> Optional[Rect]:
    """Bounding box of all monitors (screen coords)."""
    if not IS_WINDOWS:
        return None
    try:
        x, y = _user32.GetSystemMetrics(76), _user32.GetSystemMetrics(77)
        w, h = _user32.GetSystemMetrics(78), _user32.GetSystemMetrics(79)
        if w > 0 and h > 0:
            return x, y, x + w, y + h
    except Exception:
        pass
    return None


def monitors() -> List[dict]:
    """[{'rect': Rect, 'work': Rect, 'primary': bool}, ...]. 'work' excludes the taskbar."""
    if not IS_WINDOWS:
        return []
    result: List[dict] = []
    try:
        def _cb(hmon, _hdc, _lprect, _data):
            info = _MONITORINFO()
            info.cbSize = ctypes.sizeof(_MONITORINFO)
            if _user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
                m, w = info.rcMonitor, info.rcWork
                result.append({"rect": (m.left, m.top, m.right, m.bottom),
                               "work": (w.left, w.top, w.right, w.bottom),
                               "primary": bool(info.dwFlags & 1)})
            return True
        _user32.EnumDisplayMonitors(None, None, _MONITORENUMPROC(_cb), 0)
    except Exception:
        return []
    return result


def window_rect(hwnd: int) -> Optional[Rect]:
    """Current rect of a window, or None if it is gone, hidden or minimized."""
    if not IS_WINDOWS or not hwnd:
        return None
    try:
        if not _user32.IsWindow(hwnd) or not _user32.IsWindowVisible(hwnd) or _user32.IsIconic(hwnd):
            return None
        r = wintypes.RECT()
        if _user32.GetWindowRect(hwnd, ctypes.byref(r)):
            return r.left, r.top, r.right, r.bottom
    except Exception:
        pass
    return None


def client_origin(hwnd: int) -> Tuple[int, int]:
    """Screen position of a window's client (0, 0) - used to map overlay <-> screen coords."""
    if not IS_WINDOWS or not hwnd:
        return 0, 0
    try:
        pt = wintypes.POINT(0, 0)
        if _user32.ClientToScreen(hwnd, ctypes.byref(pt)):
            return pt.x, pt.y
    except Exception:
        pass
    return 0, 0


def foreground_window() -> int:
    if not IS_WINDOWS:
        return 0
    try:
        return int(_user32.GetForegroundWindow() or 0)
    except Exception:
        return 0


def window_title(hwnd: int) -> str:
    if not IS_WINDOWS or not hwnd:
        return ""
    try:
        n = _user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        _user32.GetWindowTextW(hwnd, buf, n + 1)
        return buf.value
    except Exception:
        return ""


def find_window(title_part: str) -> int:
    """First visible window whose title contains `title_part` (case-insensitive)."""
    needle = title_part.lower()
    for w in list_windows():
        if needle in window_title(w.hwnd).lower():
            return w.hwnd
    return 0


def client_rect(hwnd: int) -> Optional[Rect]:
    """A window's client area (inside borders/title bar) in screen coords."""
    if not IS_WINDOWS or not hwnd:
        return None
    try:
        r = wintypes.RECT()
        if not _user32.GetClientRect(hwnd, ctypes.byref(r)):
            return None
        x, y = client_origin(hwnd)
        return x, y, x + r.right, y + r.bottom
    except Exception:
        return None


def _is_cloaked(hwnd) -> bool:
    if _dwmapi is None:
        return False
    try:
        cloaked = wintypes.DWORD(0)
        res = _dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
        return res == 0 and cloaked.value != 0
    except Exception:
        return False


def _class_name(hwnd) -> str:
    buf = ctypes.create_unicode_buffer(256)
    _user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def list_windows(exclude=()) -> List[WindowInfo]:
    """Visible, normal application windows from top to bottom of the z-order."""
    if not IS_WINDOWS:
        return []
    exclude = {int(h) for h in exclude if h}
    found: List[WindowInfo] = []
    try:
        def _cb(hwnd, _data):
            try:
                h = int(hwnd)
                if h in exclude or not _user32.IsWindowVisible(hwnd) or _user32.IsIconic(hwnd):
                    return True
                if _user32.GetWindowTextLengthW(hwnd) == 0:
                    return True
                ex = _user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                if ex & (WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE):
                    return True
                if _class_name(hwnd) in _SKIP_CLASSES or _is_cloaked(hwnd):
                    return True
                r = wintypes.RECT()
                if not _user32.GetWindowRect(hwnd, ctypes.byref(r)):
                    return True
                if r.right - r.left < MIN_WINDOW_SIZE[0] or r.bottom - r.top < MIN_WINDOW_SIZE[1]:
                    return True
                found.append(WindowInfo(h, (r.left, r.top, r.right, r.bottom), len(found)))
            except Exception:
                pass
            return True
        _user32.EnumWindows(_WNDENUMPROC(_cb), 0)
    except Exception:
        return []
    return found


# --------------------------------------------------------------------------
# Pure helpers (no OS calls - unit tested)
# --------------------------------------------------------------------------

def _subtract(segments, a, b):
    """Remove the interval [a, b] from a list of [x1, x2] segments."""
    out = []
    for x1, x2 in segments:
        if b <= x1 or a >= x2:
            out.append((x1, x2))
            continue
        if a > x1:
            out.append((x1, a))
        if b < x2:
            out.append((b, x2))
    return out


def perch_spots(windows: List[WindowInfo], bounds: Optional[Rect] = None,
                min_width: int = MIN_PERCH_WIDTH, clearance: int = 60) -> List[dict]:
    """
    Uncovered stretches of window top edges where the cat can sit.

    `windows` must be ordered top -> bottom (as list_windows returns them).
    A stretch is uncovered if no higher window overlaps the edge or the
    `clearance` pixels above it (room for the cat's body).
    Returns [{'hwnd', 'x1', 'x2', 'y'}, ...] in screen coords.
    """
    spots = []
    for i, w in enumerate(windows):
        left, top, right, _bottom = w.rect
        if bounds:
            bl, bt, br, bb = bounds
            if top - clearance < bt or top > bb:
                continue
            left, right = max(left, bl), min(right, br)
        segs = [(left, right)] if right - left >= min_width else []
        for above in windows[:i]:
            al, at, ar, ab = above.rect
            if at <= top and ab >= top - clearance:   # covers the edge or the space above it
                segs = _subtract(segs, al, ar)
            if not segs:
                break
        for x1, x2 in segs:
            if x2 - x1 >= min_width:
                spots.append({"hwnd": w.hwnd, "x1": x1, "x2": x2, "y": top})
    return spots


def spot_at(spots: List[dict], x: float, y_from: float, y_to: float, margin: int = 20) -> Optional[dict]:
    """First perch whose edge lies between y_from and y_to (falling) under x."""
    best = None
    for s in spots:
        if s["x1"] + margin <= x <= s["x2"] - margin and y_from <= s["y"] <= y_to:
            if best is None or s["y"] < best["y"]:
                best = s
    return best


def floor_y_at(monitor_list: List[dict], x: float, default: float) -> float:
    """Top of the taskbar (bottom of the work area) of the monitor under x."""
    for m in monitor_list:
        left, _t, right, _b = m["rect"]
        if left <= x < right:
            return m["work"][3]
    return default
