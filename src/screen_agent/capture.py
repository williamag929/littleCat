"""
capture.py - grab a screen region as a numpy RGB array (Windows GDI via ctypes).

No mss / PIL needed, so it works inside LittleCat.exe. Frames are only kept
in memory for the current decision - nothing is ever written to disk.
"""

from __future__ import annotations

import sys
from typing import Optional, Tuple

import numpy as np

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.windll.user32
    _gdi32 = ctypes.windll.gdi32
    # 64-bit handles: declare every signature, or ctypes truncates them to int
    _user32.GetDC.restype = wintypes.HDC
    _user32.GetDC.argtypes = [wintypes.HWND]
    _user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    _gdi32.CreateCompatibleDC.restype = wintypes.HDC
    _gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    _gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    _gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    _gdi32.SelectObject.restype = wintypes.HGDIOBJ
    _gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    _gdi32.BitBlt.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                              wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.DWORD]
    _gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
                                 ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT]
    _gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    _gdi32.DeleteDC.argtypes = [wintypes.HDC]

    class _BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                    ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD),
                    ("biCompression", wintypes.DWORD), ("biSizeImage", wintypes.DWORD),
                    ("biXPelsPerMeter", wintypes.LONG), ("biYPelsPerMeter", wintypes.LONG),
                    ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]

SRCCOPY = 0x00CC0020


def make_dpi_aware() -> bool:
    """Use real (physical) pixels for window positions AND screen captures.

    Without this, on a scaled display (125 %, 150 %...) window coordinates are
    "logical" while BitBlt captures physical pixels, so the capture lands in the
    wrong place. Call it once at process start - NOT in the LittleCat overlay
    process (the overlay is laid out in logical pixels).
    """
    if not IS_WINDOWS:
        return False
    try:
        return bool(ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)))  # per-monitor v2
    except Exception:
        try:
            return ctypes.windll.shcore.SetProcessDpiAwareness(2) == 0
        except Exception:
            return False


class ScreenCapture:
    """Reusable capturer for one region (left, top, width, height) in screen coords."""

    def __init__(self, region: Tuple[int, int, int, int]):
        if not IS_WINDOWS:
            raise OSError("screen capture is only implemented for Windows")
        self.left, self.top, self.w, self.h = map(int, region)
        self.screen_dc = _user32.GetDC(None)
        self.mem_dc = _gdi32.CreateCompatibleDC(self.screen_dc)
        self.bmp = _gdi32.CreateCompatibleBitmap(self.screen_dc, self.w, self.h)
        _gdi32.SelectObject(self.mem_dc, self.bmp)
        self.info = _BITMAPINFOHEADER()
        self.info.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        self.info.biWidth = self.w
        self.info.biHeight = -self.h          # top-down rows
        self.info.biPlanes = 1
        self.info.biBitCount = 32
        self.buf = np.empty((self.h, self.w, 4), dtype=np.uint8)

    def grab(self) -> Optional[np.ndarray]:
        if not _gdi32.BitBlt(self.mem_dc, 0, 0, self.w, self.h, self.screen_dc, self.left, self.top, SRCCOPY):
            return None
        got = _gdi32.GetDIBits(self.mem_dc, self.bmp, 0, self.h, self.buf.ctypes.data_as(ctypes.c_void_p),
                               ctypes.byref(self.info), 0)
        if got != self.h:
            return None
        return self.buf[:, :, 2::-1]          # BGRA -> RGB view

    def close(self):
        try:
            _gdi32.DeleteObject(self.bmp)
            _gdi32.DeleteDC(self.mem_dc)
            _user32.ReleaseDC(None, self.screen_dc)
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
