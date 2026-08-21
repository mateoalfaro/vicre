import os
import subprocess
import tempfile


def _socket():
    env = os.environ.get("YDOTOOL_SOCKET")
    if env:
        return env
    for candidate in ("/run/ydotoold/socket",
                      os.path.join(os.environ.get("XDG_RUNTIME_DIR", ""), ".ydotool_socket")):
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def type_text(text):
    socket_path = _socket()
    env = os.environ.copy()
    if socket_path:
        env["YDOTOOL_SOCKET"] = socket_path
    fd, tmp = tempfile.mkstemp(prefix="vicre-type-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        subprocess.run(["ydotool", "type", "--file", tmp], env=env, check=True)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass