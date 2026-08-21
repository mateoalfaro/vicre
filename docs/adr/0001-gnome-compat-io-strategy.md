# GNOME-compatible I/O strategy: portal screenshot, ydotool typing, gsettings keybinds

Vicre must work on GNOME Wayland (primary target) without excluding wlroots compositors like labwc. We therefore avoid every wlroots-only protocol: screenshots go through `org.freedesktop.portal.Screenshot` instead of grim (Mutter lacks `wlr-screencopy-unstable-v1`, so grim cannot work on GNOME), text injection goes through ydotool/uinput instead of wtype (Mutter declined `zwp_virtual_keyboard_manager_v1`), and the ctrl+i/ctrl+o/ctrl+p bindings are written as GNOME custom keybindings via gsettings at login instead of using the GlobalShortcuts portal (GNOME 48+ only, per-session approval dialog, unreliable persistence).

## Considered Options

- **grim** — simplest on wlroots, impossible on GNOME. Rejected as primary; portal covers both.
- **wtype / wl-copy** — wtype unsupported by Mutter; wl-copy only works there via a focus-grab fallback hack. Rejected for typing.
- **GlobalShortcuts portal** — the "proper" mechanism, but version-gated and its binding UX was not deterministic enough for a fire-and-forget tool.

## Consequences

- Requires a system-level `ydotoold` (`programs.ydotool.enable` in NixOS) and group membership — pulled in automatically by the Vicre module.
- Portal screenshots capture all monitors stitched into one image; single-monitor capture is not possible through this API.
- First capture triggers a one-time GNOME permission prompt for screenshots.
