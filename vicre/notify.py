import subprocess
import sys


def notify(reason):
    if sys.platform == "win32":
        from vicre import winapp
        winapp.notify(reason)
        return
    try:
        subprocess.run(["notify-send", "Vicre", reason], check=False)
    except OSError:
        pass
