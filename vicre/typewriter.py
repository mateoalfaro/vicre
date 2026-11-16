import os
import shutil
import subprocess
import sys
import time


def _socket():
    env = os.environ.get("YDOTOOL_SOCKET")
    if env:
        return env
    for candidate in ("/run/ydotoold/socket",
                      os.path.join(os.environ.get("XDG_RUNTIME_DIR", ""), ".ydotool_socket")):
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def paste_delay():
    try:
        return float(os.environ.get("VICRE_PASTE_DELAY", "0.35"))
    except (TypeError, ValueError):
        return 0.35


def type_text(text):
    if sys.platform == "win32":
        from vicre import wintype
        wintype.paste_text(text, paste_delay())
        return
    socket_path = _socket()
    env = os.environ.copy()
    if socket_path:
        env["YDOTOOL_SOCKET"] = socket_path
    if not shutil.which("wl-copy"):
        raise RuntimeError("wl-copy no está disponible")
    subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=True, env=env)
    time.sleep(paste_delay())
    subprocess.run(["ydotool", "key", "29:1", "47:1", "47:0", "29:0"], check=True, env=env)
