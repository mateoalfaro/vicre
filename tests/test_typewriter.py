import os
import subprocess
import unittest
from unittest import mock

from vicre.typewriter import paste_delay, type_text


class PasteDelayTests(unittest.TestCase):
    def test_unset_uses_default(self):
        with mock.patch.dict("os.environ", {}, clear=False):
            os.environ.pop("VICRE_PASTE_DELAY", None)
            self.assertEqual(paste_delay(), 0.35)

    def test_parses_float(self):
        with mock.patch.dict("os.environ", {"VICRE_PASTE_DELAY": "0.1"}, clear=False):
            self.assertEqual(paste_delay(), 0.1)

    def test_invalid_uses_default(self):
        with mock.patch.dict("os.environ", {"VICRE_PASTE_DELAY": "abc"}, clear=False):
            self.assertEqual(paste_delay(), 0.35)

    def test_zero_disables(self):
        with mock.patch.dict("os.environ", {"VICRE_PASTE_DELAY": "0"}, clear=False):
            self.assertEqual(paste_delay(), 0.0)


class TypeTextTests(unittest.TestCase):
    def test_wl_copy_path_sets_clipboard_sleeps_then_pastes(self):
        with mock.patch.dict("os.environ", {"VICRE_PASTE_DELAY": "0.35"}, clear=False), \
                mock.patch("vicre.typewriter._socket", return_value="/tmp/fake-sock"), \
                mock.patch("vicre.typewriter.shutil.which", return_value="/usr/bin/wl-copy"), \
                mock.patch("vicre.typewriter.time.sleep") as sleep, \
                mock.patch("vicre.typewriter.subprocess.run",
                           return_value=mock.Mock(returncode=0)) as run:
            type_text("hola π ≤ →")
            self.assertEqual(run.call_count, 2)
            wl_call, key_call = run.call_args_list
            self.assertEqual(wl_call.args[0], ["wl-copy"])
            self.assertEqual(wl_call.kwargs["input"], "hola π ≤ →".encode("utf-8"))
            self.assertIs(wl_call.kwargs["check"], True)
            self.assertEqual(wl_call.kwargs["env"]["YDOTOOL_SOCKET"], "/tmp/fake-sock")
            self.assertIsNot(wl_call.kwargs["env"], os.environ)
            sleep.assert_called_once_with(0.35)
            self.assertEqual(key_call.args[0], ["ydotool", "key", "29:1", "47:1", "47:0", "29:0"])
            self.assertIs(key_call.kwargs["check"], True)
            self.assertEqual(key_call.kwargs["env"]["YDOTOOL_SOCKET"], "/tmp/fake-sock")
            self.assertFalse(any("--file" in c.args[0] for c in run.call_args_list))

    def test_missing_wl_copy_raises_without_typing(self):
        with mock.patch("vicre.typewriter._socket", return_value="/tmp/fake-sock"), \
                mock.patch("vicre.typewriter.shutil.which", return_value=None), \
                mock.patch("vicre.typewriter.time.sleep") as sleep, \
                mock.patch("vicre.typewriter.subprocess.run") as run:
            with self.assertRaises(RuntimeError):
                type_text("á é π")
            run.assert_not_called()
            sleep.assert_not_called()

    def test_wl_copy_failure_raises_without_typing(self):
        with mock.patch("vicre.typewriter._socket", return_value="/tmp/fake-sock"), \
                mock.patch("vicre.typewriter.shutil.which", return_value="/usr/bin/wl-copy"), \
                mock.patch("vicre.typewriter.time.sleep") as sleep, \
                mock.patch("vicre.typewriter.subprocess.run",
                           side_effect=subprocess.CalledProcessError(1, ["wl-copy"])) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                type_text("x")
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0], ["wl-copy"])
            sleep.assert_not_called()
            self.assertFalse(any(c.args[0][:2] == ["ydotool", "type"]
                                 for c in run.call_args_list))

    def test_key_injection_failure_propagates_without_typing(self):
        with mock.patch.dict("os.environ", {"VICRE_PASTE_DELAY": "0.35"}, clear=False), \
                mock.patch("vicre.typewriter._socket", return_value="/tmp/fake-sock"), \
                mock.patch("vicre.typewriter.shutil.which", return_value="/usr/bin/wl-copy"), \
                mock.patch("vicre.typewriter.time.sleep") as sleep, \
                mock.patch("vicre.typewriter.subprocess.run",
                           side_effect=[mock.Mock(returncode=0),
                                        subprocess.CalledProcessError(1, ["ydotool"])]) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                type_text("x")
            self.assertEqual(run.call_count, 2)
            self.assertEqual(run.call_args_list[1].args[0],
                             ["ydotool", "key", "29:1", "47:1", "47:0", "29:0"])
            sleep.assert_called_once_with(0.35)
            self.assertFalse(any(c.args[0][:2] == ["ydotool", "type"]
                                 for c in run.call_args_list))

    def test_socket_reaches_env_of_wl_copy_and_ydotool(self):
        with mock.patch("vicre.typewriter._socket", return_value="/tmp/fake-sock"), \
                mock.patch("vicre.typewriter.shutil.which", return_value="/usr/bin/wl-copy"), \
                mock.patch("vicre.typewriter.time.sleep"), \
                mock.patch("vicre.typewriter.subprocess.run",
                           return_value=mock.Mock(returncode=0)) as run:
            type_text("ok")
            self.assertEqual(len(run.call_args_list), 2)
            for call in run.call_args_list:
                self.assertEqual(call.kwargs["env"]["YDOTOOL_SOCKET"], "/tmp/fake-sock")
                self.assertIsNot(call.kwargs["env"], os.environ)


if __name__ == "__main__":
    unittest.main()
