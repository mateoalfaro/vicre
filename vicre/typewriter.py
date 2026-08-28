import os
import shutil
import subprocess
import tempfile
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
    socket_path = _socket()
    env = os.environ.copy()
    if socket_path:
        env["YDOTOOL_SOCKET"] = socket_path
    if shutil.which("wl-copy"):
        try:
            result = subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=False, env=env)
            if result.returncode == 0:
                time.sleep(paste_delay())
                subprocess.run(["ydotool", "key", "29:1", "47:1", "47:0", "29:0"], check=True, env=env)
                return
        except Exception:
            pass
    fd, tmp = tempfile.mkstemp(prefix="vicre-type-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        subprocess.run(["ydotool", "type", "--key-delay", "25", "--file", tmp], env=env, check=True)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass