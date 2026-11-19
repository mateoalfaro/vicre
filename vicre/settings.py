"""Runtime overrides from a plain ``vicre.env`` file (no rebuild needed).

Lookup order for each setting: real environment variable, then the file, then
the built-in default.  The file is re-read on every call, so edits apply to the
next capture without restarting Vicre.

Location: ``VICRE_CONFIG`` if set; else ``vicre.env`` next to ``vicre.exe`` when
frozen (the USB folder); else ``~/.vicre/vicre.env``.

Format: ``KEY=value`` lines; ``#`` starts a comment; values may be quoted.
Example::

    VICRE_MODEL=opencode-go/glm-5.3-flash
    VICRE_VARIANT=max
"""

import os
import sys


def config_path():
    override = os.environ.get("VICRE_CONFIG")
    if override:
        return os.path.abspath(override)
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "vicre.env")
    return os.path.expanduser("~/.vicre/vicre.env")


def parse(text):
    values = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def load():
    try:
        with open(config_path(), encoding="utf-8-sig") as f:
            return parse(f.read())
    except (OSError, UnicodeDecodeError):
        return {}


def get(name, default=None):
    if name in os.environ:
        return os.environ[name]
    return load().get(name, default)
