"""Windows paste backend: set the clipboard, then inject one ctrl+v.

Same strategy as ADR 0002 (clipboard + single ctrl+v), using ctypes only so
the portable executable needs no extra dependencies.  Hotkeys fire on key
press, so the physical ctrl/alt are usually still down; injecting ctrl+v then
would arrive as ctrl+alt+v.  We wait for the modifiers to be released first.
"""

import ctypes
import time
from ctypes import wintypes

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN, VK_V = 0x10, 0x11, 0x12, 0x5B, 0x5C, 0x56
MODIFIERS = (VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN)
RELEASE_TIMEOUT = 3.0


def _apis():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    return user32, kernel32


def set_clipboard(text):
    user32, kernel32 = _apis()
    data = (text.replace("\r\n", "\n").replace("\n", "\r\n") + "\0").encode("utf-16-le")
    for _ in range(20):  # the clipboard can be briefly held by another app
        if user32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("no se pudo abrir el portapapeles")
    try:
        user32.EmptyClipboard()
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not handle:
            raise RuntimeError("sin memoria para el portapapeles")
        ptr = kernel32.GlobalLock(handle)
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            kernel32.GlobalFree(handle)
            raise RuntimeError("no se pudo escribir el portapapeles")
    finally:
        user32.CloseClipboard()


def wait_modifiers_released(timeout=RELEASE_TIMEOUT):
    user32, _ = _apis()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not any(user32.GetAsyncKeyState(vk) & 0x8000 for vk in MODIFIERS):
            return
        time.sleep(0.02)


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _MOUSEINPUT(ctypes.Structure):  # only here to give the union its real size
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT)]
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


def send_ctrl_v():
    user32, _ = _apis()
    keys = [(VK_CONTROL, 0), (VK_V, 0), (VK_V, KEYEVENTF_KEYUP), (VK_CONTROL, KEYEVENTF_KEYUP)]
    events = (_INPUT * len(keys))()
    for event, (vk, flags) in zip(events, keys):
        event.type = INPUT_KEYBOARD
        event.ki = _KEYBDINPUT(vk, 0, flags, 0, 0)
    sent = user32.SendInput(len(keys), events, ctypes.sizeof(_INPUT))
    if sent != len(keys):
        raise RuntimeError("no se pudo enviar ctrl+v")


def paste_text(text, delay=0.35):
    set_clipboard(text)
    wait_modifiers_released()
    time.sleep(delay)
    send_ctrl_v()
