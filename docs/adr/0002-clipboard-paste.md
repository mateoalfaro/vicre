# Clipboard paste (wl-copy + single ctrl+v) instead of ydotool keystroke typing

Vicre writes Respuesta Tipo 1/2 into whatever window has focus. The original strategy typed the whole text with `ydotool type` (per-character uinput synthesis). In practice the pastes came out garbled and incomplete for two independent reasons:

1. **Non-ASCII damage.** `ydotool type` maps characters through a US keymap. Accented Spanish (`á`, `é`, `ñ`) and Wolfram symbols (`π`, `≤`, `→`) that appear in the responses are unmappable or get mis-mapped, and aggressive default key delays let some focused applications drop keystrokes outright.
2. **Modifier union on keybind press.** GNOME custom keybindings fire on key *press*. When the paste command starts, the user's physical `ctrl`/`alt` are often still held. uinput events union with the physical keyboard's modifier state at the compositor, so the first injected characters arrive as `ctrl+alt+<char>` (select-all, menus, control codes) instead of text. The failure looked random because it depended on how long the user held the chord.

## Decision

Paste through the Wayland clipboard instead of typing characters:

1. Set the selection with `wl-copy` (wl-clipboard). It daemonizes after the compositor roundtrip and keeps serving the data, which works fine on GNOME — ADR 0001 only rejected wl-copy as a *keystroke* mechanism, not as a selection owner.
2. Sleep a short, configurable interval (`VICRE_PASTE_DELAY`, default 0.35 s) so the physical chord is released before injection.
3. Inject a single synthetic `ctrl+v` via `ydotool key 29:1 47:1 47:0 29:0`.
4. If `wl-copy` is unavailable or the keystroke fails, fall back to the old `ydotool type --file` path with an explicit `--key-delay 25`.

The receiving application does the text insertion itself, so any Unicode the model produced arrives intact, long texts paste instantly, and no per-character timing race exists.

## Consequences

- Requires `wl-clipboard` on PATH (pulled in by the Vicre package) and a Wayland display in the daemon's environment — both are satisfied inside the graphical session target.
- The Vicre response stays in the clipboard after pasting; a manual `ctrl+v` repeats it. Accepted: it doubles as a re-paste affordance.
- The fallback typing path still mangles non-ASCII; it exists only for environments without wl-clipboard.
