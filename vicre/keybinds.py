import ast
import os
import subprocess

SCHEMA = "org.gnome.settings-daemon.plugins.media-keys"
KEY = "custom-keybindings"
BINDING_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
BASE = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/"
TAILS = ["vicre0/", "vicre1/", "vicre2/"]
NAMES = ["Vicre Capturar", "Vicre Pegar respuesta", "Vicre Pegar código"]
BINDINGS = ["<Ctrl>i", "<Ctrl>o", "<Ctrl>p"]
VICRE_BIN = os.environ.get("VICRE_BIN", "vicre")
COMMANDS = [f"{VICRE_BIN} capture", f"{VICRE_BIN} paste1", f"{VICRE_BIN} paste2"]


def _run(*args):
    subprocess.run(["gsettings", *args], check=True)


def _current_list():
    out = subprocess.check_output(["gsettings", "get", SCHEMA, KEY], text=True).strip()
    if out.startswith("@as"):
        return []
    parsed = ast.literal_eval(out)
    if not isinstance(parsed, list):
        raise ValueError(f"formato inesperado de custom-list: {out}")
    return parsed


def apply():
    paths = [BASE + tail for tail in TAILS]
    current = _current_list()
    merged = list(current)
    for path in paths:
        if path not in merged:
            merged.append(path)
    if merged != current:
        _run("set", SCHEMA, KEY, repr(merged))
    for path, name, binding, command in zip(paths, NAMES, BINDINGS, COMMANDS):
        schema_path = f"{BINDING_SCHEMA}:{path}"
        _run("set", schema_path, "name", name)
        _run("set", schema_path, "binding", binding)
        _run("set", schema_path, "command", command)