import unittest
from unittest import mock

from vicre import keybinds


class VicreBinTests(unittest.TestCase):
    def test_current_system_generation_is_preferred(self):
        """Keybinds must survive `nh os switch`: the /run/current-system
        symlink always tracks the active generation, a store path does not."""

        with mock.patch.object(keybinds.os, "access", return_value=True):
            self.assertEqual(keybinds._vicre_bin(), keybinds.STABLE_BIN)
        self.assertEqual(keybinds.STABLE_BIN, "/run/current-system/sw/bin/vicre")

    def test_env_bin_is_used_without_system_install(self):
        with mock.patch.object(keybinds.os, "access", return_value=False):
            with mock.patch.dict(
                keybinds.os.environ, {"VICRE_BIN": "/nix/store/abc/bin/vicre"}
            ):
                self.assertEqual(keybinds._vicre_bin(), "/nix/store/abc/bin/vicre")

    def test_bare_name_is_the_last_resort(self):
        with mock.patch.object(keybinds.os, "access", return_value=False):
            with mock.patch.dict(keybinds.os.environ, {}, clear=False):
                keybinds.os.environ.pop("VICRE_BIN", None)
                self.assertEqual(keybinds._vicre_bin(), "vicre")


class ApplyTests(unittest.TestCase):
    def test_apply_registers_the_resolved_commands(self):
        runs = []
        commands = [
            "/run/current-system/sw/bin/vicre capture",
            "/run/current-system/sw/bin/vicre paste1",
            "/run/current-system/sw/bin/vicre paste2",
        ]

        with (
            mock.patch.object(keybinds, "_current_list", return_value=[]),
            mock.patch.object(keybinds, "COMMANDS", commands),
            mock.patch.object(keybinds, "_run", side_effect=lambda *args: runs.append(args)),
        ):
            keybinds.apply()

        set_calls = [args for args in runs if args[0] == "set"]
        registered = [args[-1] for args in set_calls if args[-2] == "command"]
        self.assertEqual(registered, commands)
        # the keybinding paths are registered in the custom list
        merged = [args[-1] for args in set_calls if args[1] == keybinds.SCHEMA]
        self.assertIn(repr([keybinds.BASE + tail for tail in keybinds.TAILS]), merged)

    def test_apply_keeps_existing_custom_keybindings(self):
        runs = []
        existing = ["/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/other/"]

        with (
            mock.patch.object(keybinds, "_current_list", return_value=list(existing)),
            mock.patch.object(keybinds, "COMMANDS", []),
            mock.patch.object(keybinds, "_run", side_effect=lambda *args: runs.append(args)),
        ):
            keybinds.apply()

        merged = [args[-1] for args in runs if args[0] == "set" and args[1] == keybinds.SCHEMA]
        self.assertIn(repr(existing + [keybinds.BASE + tail for tail in keybinds.TAILS]), merged)


if __name__ == "__main__":
    unittest.main()
