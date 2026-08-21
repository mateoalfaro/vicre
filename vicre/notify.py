import subprocess


def notify(reason):
    try:
        subprocess.run(["notify-send", "Vicre", reason], check=False)
    except OSError:
        pass