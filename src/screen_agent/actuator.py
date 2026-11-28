"""
actuator.py - turn left/stay/right into keys held down, SAFELY.

* Non-blocking: a key is pressed when the action starts and released when it
  changes (no sleep while a key is down, so the agent keeps watching).
* Focus guard: keys are only sent while the game window is in front. The
  moment you switch to another window every key is released.
* Panic hotkey: Ctrl+Alt+P stops the agent from anywhere.
* Keys go out with SendInput scan codes (works with most games, no pyautogui).
"""

from __future__ import annotations

import sys
from typing import Callable, Dict, Optional, Tuple

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.windll.user32
    ULONG_PTR = ctypes.c_size_t

    class _KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]

    class _MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT)]

    class _INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# name -> (virtual key, extended?)
KEYS: Dict[str, Tuple[int, bool]] = {
    "left": (0x25, True), "right": (0x27, True), "up": (0x26, True), "down": (0x28, True),
    "a": (0x41, False), "d": (0x44, False), "w": (0x57, False), "s": (0x53, False),
    "space": (0x20, False),
}
VK_CONTROL, VK_MENU, VK_P = 0x11, 0x12, 0x50


def panic_pressed() -> bool:
    """Ctrl+Alt+P held down (checked globally, only those three keys)."""
    if not IS_WINDOWS:
        return False
    try:
        state = _user32.GetAsyncKeyState
        return bool(state(VK_CONTROL) & 0x8000 and state(VK_MENU) & 0x8000 and state(VK_P) & 0x8000)
    except Exception:
        return False


def _send_key(name: str, down: bool):
    vk, extended = KEYS[name]
    scan = _user32.MapVirtualKeyW(vk, 0)
    flags = KEYEVENTF_SCANCODE | (KEYEVENTF_EXTENDEDKEY if extended else 0) | (0 if down else KEYEVENTF_KEYUP)
    inp = _INPUT(type=INPUT_KEYBOARD)
    inp.u.ki = _KEYBDINPUT(0, scan, flags, 0, 0)
    _user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))


class KeyActuator:
    def __init__(self, keys: Tuple[str, str] = ("left", "right"), target_hwnd: int = 0,
                 foreground: Optional[Callable[[], int]] = None,
                 send: Optional[Callable[[str, bool], None]] = None,
                 panic: Callable[[], bool] = panic_pressed):
        for k in keys:
            if k not in KEYS:
                raise ValueError(f"unknown key '{k}' (known: {', '.join(KEYS)})")
        self.keys = {-1: keys[0], 1: keys[1]}
        self.target_hwnd = target_hwnd
        self.foreground = foreground or self._foreground
        self.send = send or (_send_key if IS_WINDOWS else (lambda k, d: None))
        self.panic = panic
        self.held: Optional[str] = None
        self.stopped = False
        self.stop_reason = ""

    @staticmethod
    def _foreground() -> int:
        return int(_user32.GetForegroundWindow() or 0) if IS_WINDOWS else 0

    def has_focus(self) -> bool:
        return not self.target_hwnd or self.foreground() == self.target_hwnd

    def apply(self, action: int) -> bool:
        """Hold the key for `action`. Returns False once the agent must stop."""
        if self.stopped:
            return False
        if self.panic():
            self.stop("panic hotkey")
            return False
        if not self.has_focus():
            self.release_all()            # never type into whatever window you switched to
            return True
        want = self.keys.get(action)
        if want != self.held:
            self.release_all()
            if want:
                self.send(want, True)
                self.held = want
        return True

    def release_all(self):
        if self.held:
            self.send(self.held, False)
            self.held = None

    def stop(self, reason: str = "stopped"):
        self.release_all()
        self.stopped = True
        self.stop_reason = reason
