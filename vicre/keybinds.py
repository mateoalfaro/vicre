import ast
import os
import subprocess

SCHEMA = "org.gnome.settings-daemon.plugins.media-keys"
KEY = "custom-keybindings"
BINDING_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
BASE = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/"
TAILS = ["vicre0/", "vicre1/", "vicre2/"]
NAMES = ["Vicre Capturar", "Vicre Pegar respuesta", "Vicre Pegar código"]
BINDINGS = ["<Ctrl><Alt>i", "<Ctrl><Alt>o", "<Ctrl><Alt>p"]
STABLE_BIN = "/run/current-system/sw/bin/vicre"


def _vicre_bin():
    """Prefer the current system generation over a pinned store path.

    GNOME custom keybindings persist across ``nh os switch``, so a command
    baked with a store path keeps pointing at the old generation after every
    switch (the vicre-keybinds oneshot only runs at login).  The
    ``/run/current-system`` symlink always tracks the active generation, so
    the keybinds never go stale.  VICRE_BIN / PATH keep working when the
    module is not installed system-wide.
    """
    if os.access(STABLE_BIN, os.X_OK):
        return STABLE_BIN
    return os.environ.get("VICRE_BIN", "vicre")


COMMANDS = [f"{_vicre_bin()} capture", f"{_vicre_bin()} paste1", f"{_vicre_bin()} paste2"]


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