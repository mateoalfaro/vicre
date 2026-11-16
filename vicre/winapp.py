"""Windows entry point: tray app with global hotkeys instead of daemon + gsettings.

ctrl+alt+i  capture and consult      ctrl+alt+o  paste Respuesta Tipo 1
ctrl+alt+p  paste Respuesta Tipo 2   (tray menu: Quit)
"""

import asyncio
import ctypes
import sys
import threading
from ctypes import wintypes

from vicre import flow, state, typewriter

MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x0001, 0x0002, 0x4000
WM_HOTKEY, WM_QUIT = 0x0312, 0x0012
HOTKEYS = {1: ("capture", ord("I")), 2: ("tipo1", ord("O")), 3: ("tipo2", ord("P"))}

_icon = None
_loop = None
_capture_task = None
_hotkey_thread_id = None


def notify(reason):
    """Tray balloon when the icon is up, else a non-blocking message box."""
    if _icon is not None:
        try:
            _icon.notify(reason, "Vicre")
            return
        except Exception:
            pass
    threading.Thread(
        target=lambda: ctypes.windll.user32.MessageBoxW(None, reason, "Vicre", 0x40),
        daemon=True,
    ).start()


def _start_capture():
    global _capture_task
    if _capture_task is not None and not _capture_task.done():
        _capture_task.cancel()
    _capture_task = asyncio.ensure_future(flow.run_capture())


def _paste(key):
    data = state.read_state()
    text = data.get(key, "") if isinstance(data, dict) else ""
    if not text:
        notify("No hay respuesta aún")
        return
    try:
        typewriter.type_text(text)
    except Exception:
        notify("no se pudo escribir la respuesta")


def _dispatch(action):
    if action == "capture":
        _loop.call_soon_threadsafe(_start_capture)
    else:
        threading.Thread(target=_paste, args=(action,), daemon=True).start()


def _hotkey_loop(ready):
    global _hotkey_thread_id
    user32 = ctypes.windll.user32
    _hotkey_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
    failed = [name for ident, (name, vk) in HOTKEYS.items()
              if not user32.RegisterHotKey(None, ident, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, vk)]
    ready.set()
    if failed:
        notify("atajo ya en uso: " + ", ".join(failed))
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == WM_HOTKEY and msg.wParam in HOTKEYS:
            _dispatch(HOTKEYS[msg.wParam][0])
    for ident in HOTKEYS:
        user32.UnregisterHotKey(None, ident)


def _quit():
    if _hotkey_thread_id:
        ctypes.windll.user32.PostThreadMessageW(_hotkey_thread_id, WM_QUIT, 0, 0)
    if _icon is not None:
        _icon.stop()
    if _loop is not None:
        _loop.call_soon_threadsafe(_loop.stop)


def _make_icon():
    import pystray
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (64, 64), (30, 30, 30, 255))
    ImageDraw.Draw(image).polygon([(12, 14), (32, 52), (52, 14), (42, 14), (32, 34), (22, 14)],
                                  fill=(240, 240, 240, 255))
    menu = pystray.Menu(pystray.MenuItem("Salir de Vicre", lambda *_: _quit()))
    return pystray.Icon("vicre", image, "Vicre (ctrl+alt+i/o/p)", menu)


def _single_instance():
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\VicreSingleInstance")
    return ctypes.windll.kernel32.GetLastError() != 183  # ERROR_ALREADY_EXISTS


def main():
    global _icon, _loop
    if sys.platform != "win32":
        print("vicre-win solo funciona en Windows", file=sys.stderr)
        return 1
    if not _single_instance():
        return 0
    _loop = asyncio.new_event_loop()
    loop_thread = threading.Thread(target=_loop.run_forever, daemon=True)
    loop_thread.start()
    ready = threading.Event()
    threading.Thread(target=_hotkey_loop, args=(ready,), daemon=True).start()
    ready.wait(5)
    try:
        _icon = _make_icon()
    except ImportError:
        _icon = None
    try:
        if _icon is not None:
            _icon.run()  # blocks until Quit
        else:
            loop_thread.join()
    except KeyboardInterrupt:
        _quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
