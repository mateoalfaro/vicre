import json
import os

STATE_FILE = os.path.expanduser("~/.vicre/state.json")


def read_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def write_state(tipo1, tipo2, photo, captured_at):
    data = {"tipo1": tipo1, "tipo2": tipo2, "photo": photo, "captured_at": captured_at}
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, STATE_FILE)