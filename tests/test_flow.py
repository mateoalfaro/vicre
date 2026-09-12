import json
import os
import tempfile
import unittest
from unittest import mock

from vicre import flow


VALID_CAP1 = """
RESPUESTA_TIPO1:
#1: respuesta
RESPUESTA_TIPO2:
Lucas[n_] := If[n == 1, 1, If[n == 2, 3, Lucas[n - 1] + Lucas[n - 2]]]
Lucas[8]
PROCEDIMIENTO: cap1
"""


class _Process:
    def __init__(self, returncode=0):
        self.returncode = returncode


class FlowRepairTests(unittest.IsolatedAsyncioTestCase):
    def _patches(self, ocr_text=""):
        return (
            mock.patch.object(flow.portal, "take_screenshot", new=mock.AsyncMock(return_value="file:///capture.png")),
            mock.patch.object(flow, "save_photo", return_value="/tmp/photo.png"),
            mock.patch.object(flow.routing, "ocr_image", return_value=ocr_text),
            mock.patch.object(flow, "ensure_fuentes"),
            mock.patch.object(flow, "ensure_config"),
            mock.patch.object(flow, "_protected_names", return_value=("Productoria",)),
            mock.patch.object(flow.state, "clear_state"),
            mock.patch.object(flow.notify, "notify"),
        )

    async def test_one_validation_repair_then_only_validated_result_is_saved(self):
        initial = "RESPUESTA_TIPO1: #1: respuesta\nRESPUESTA_TIPO2: Lucas[8]"
        processes = [_Process(), _Process()]
        launch_prompts = []

        async def launch(photo, request_prompt=None, expected_procedures=()):
            launch_prompts.append(request_prompt)
            return processes.pop(0)

        async def communicate(_proc):
            if len(launch_prompts) == 1:
                return initial.encode(), b""
            return VALID_CAP1.encode(), b""

        screenshots, save_photo, ocr, fuentes, config, protected, clear, notify = self._patches()
        with (
            screenshots,
            save_photo,
            ocr,
            fuentes,
            config,
            protected,
            clear,
            mock.patch.object(flow, "_launch_opencode", new=launch),
            mock.patch.object(flow, "_communicate", new=communicate),
            mock.patch.object(flow.state, "write_state") as write_state,
            notify,
        ):
            flow._active_proc = None
            await flow.run_capture()

        self.assertEqual(len(launch_prompts), 2)
        self.assertIsNone(launch_prompts[0])
        self.assertIn("ERROR DE VALIDACIÓN", launch_prompts[1])
        write_state.assert_called_once()
        self.assertEqual(
            write_state.call_args.kwargs["procedures"], ("cap1",)
        )

    async def test_invalid_second_repair_is_not_saved_and_still_launches_only_twice(self):
        invalid = "RESPUESTA_TIPO1: #1\nRESPUESTA_TIPO2: Lucas[8]"
        processes = [_Process(), _Process()]
        launches = []

        async def launch(photo, request_prompt=None, expected_procedures=()):
            launches.append(request_prompt)
            return processes.pop(0)

        async def communicate(_proc):
            return invalid.encode(), b""

        screenshots, save_photo, ocr, fuentes, config, protected, clear, notify = self._patches()
        import tempfile
        with tempfile.TemporaryDirectory() as home:
            with (
                screenshots,
                save_photo,
                ocr,
                fuentes,
                config,
                protected,
                clear,
                mock.patch.object(flow, "HOME_DIR", home),
                mock.patch.object(flow, "_launch_opencode", new=launch),
                mock.patch.object(flow, "_communicate", new=communicate),
                mock.patch.object(flow.state, "write_state") as write_state,
                notify,
            ):
                flow._active_proc = None
                await flow.run_capture()

            self.assertEqual(len(launches), 2)
            write_state.assert_not_called()
            with open(os.path.join(home, "last-raw.txt")) as f:
                self.assertEqual(f.read(), invalid)

    async def test_ocr_hints_are_passed_to_prompt_and_validation(self):
        proc = _Process()
        launch_calls = []

        async def launch(photo, request_prompt=None, expected_procedures=()):
            launch_calls.append((request_prompt, expected_procedures))
            return proc

        async def communicate(_proc):
            return VALID_CAP1.encode(), b""

        screenshots, save_photo, ocr, fuentes, config, protected, clear, notify = self._patches(
            ocr_text="programa recursivo de pila Fibonacci"
        )
        with (
            screenshots,
            save_photo,
            ocr,
            fuentes,
            config,
            protected,
            clear,
            mock.patch.object(flow, "_launch_opencode", new=launch),
            mock.patch.object(flow, "_communicate", new=communicate),
            mock.patch.object(flow.state, "write_state") as write_state,
            notify,
        ):
            flow._active_proc = None
            await flow.run_capture()

        self.assertEqual(launch_calls[0][1], ("cap1",))
        self.assertIsNone(launch_calls[0][0])
        write_state.assert_called_once()

    async def test_process_launch_oserror_is_reported_without_saving(self):
        async def launch(photo, request_prompt=None, expected_procedures=()):
            raise OSError("opencode missing")

        screenshots, save_photo, ocr, fuentes, config, protected, clear, notify = self._patches()
        with (
            screenshots,
            save_photo,
            ocr,
            fuentes,
            config,
            protected,
            clear,
            mock.patch.object(flow, "_launch_opencode", new=launch),
            mock.patch.object(flow.state, "write_state") as write_state,
            notify as notify_mock,
        ):
            flow._active_proc = None
            await flow.run_capture()

        write_state.assert_not_called()
        notify_mock.assert_called_once()

    async def test_opencode2_launch_uses_model_agent_and_attachment(self):
        """OpenCode 2 receives the scoped prompt and capture attachment."""

        proc = _Process()
        exec_calls = []

        async def fake_exec(*args, **kwargs):
            exec_calls.append((args, kwargs))
            return proc

        async def communicate(_proc):
            return VALID_CAP1.encode(), b""

        screenshots, save_photo, ocr, fuentes, config, protected, clear, notify = self._patches()
        with (
            screenshots,
            save_photo,
            ocr,
            fuentes,
            config,
            mock.patch.object(flow, "MODEL", "opencode-go/glm-5.3-flash"),
            mock.patch.object(flow, "VARIANT", "max"),
            protected,
            clear,
            mock.patch.object(
                flow.asyncio,
                "create_subprocess_exec",
                new=mock.AsyncMock(side_effect=fake_exec),
            ),
            mock.patch.object(flow, "_communicate", new=communicate),
            mock.patch.object(flow.state, "write_state") as write_state,
            notify,
        ):
            flow._active_proc = None
            await flow.run_capture()

        # opencode2 run --standalone --agent vicre --model <modelo>
        #   --file <foto> --auto "<prompt con foto>"
        args = exec_calls[0][0]
        self.assertEqual(args[:2], ("opencode2", "run"))
        self.assertIn("--standalone", args)
        self.assertEqual(args[args.index("--agent") + 1], "vicre")
        self.assertEqual(
            args[args.index("--model") + 1], "opencode-go/glm-5.3-flash#max"
        )
        self.assertEqual(args[args.index("--file") + 1], "/tmp/photo.png")
        self.assertIn("--auto", args)
        self.assertIn("La imagen adjunta en /tmp/photo.png", args[-1])
        write_state.assert_called_once()

    async def test_opencode2_launch_joins_model_variant(self):
        proc = _Process()
        exec_calls = []

        async def fake_exec(*args, **kwargs):
            exec_calls.append((args, kwargs))
            return proc

        with (
            mock.patch.object(
                flow.asyncio,
                "create_subprocess_exec",
                new=mock.AsyncMock(side_effect=fake_exec),
            ),
            mock.patch.object(flow, "MODEL", "opencode-go/qwen3.7-plus"),
            mock.patch.object(flow, "VARIANT", "max"),
        ):
            flow._active_proc = None
            await flow._launch_opencode("/tmp/photo.png")

        args = exec_calls[0][0]
        self.assertEqual(args[args.index("--model") + 1], "opencode-go/qwen3.7-plus#max")

    async def test_opencode2_launch_omits_empty_model_variant(self):
        proc = _Process()
        exec_calls = []

        async def fake_exec(*args, **kwargs):
            exec_calls.append((args, kwargs))
            return proc

        with (
            mock.patch.object(
                flow.asyncio,
                "create_subprocess_exec",
                new=mock.AsyncMock(side_effect=fake_exec),
            ),
            mock.patch.object(flow, "MODEL", "opencode-go/qwen3.7-plus"),
            mock.patch.object(flow, "VARIANT", ""),
        ):
            flow._active_proc = None
            await flow._launch_opencode("/tmp/photo.png")

        args = exec_calls[0][0]
        self.assertEqual(args[args.index("--model") + 1], "opencode-go/qwen3.7-plus")

    async def test_repair_prompt_carries_photo_path(self):
        invalid = "RESPUESTA_TIPO1: #1\nRESPUESTA_TIPO2: Lucas[8]"
        processes = [_Process(), _Process()]
        repair_args = []

        async def launch(photo, request_prompt=None, expected_procedures=()):
            repair_args.append((request_prompt, photo))
            return processes.pop(0)

        async def communicate(_proc):
            if len(repair_args) == 1:
                return invalid.encode(), b""
            return VALID_CAP1.encode(), b""

        screenshots, save_photo, ocr, fuentes, config, protected, clear, notify = self._patches()
        with (
            screenshots,
            save_photo,
            ocr,
            fuentes,
            config,
            protected,
            clear,
            mock.patch.object(flow, "_launch_opencode", new=launch),
            mock.patch.object(flow, "_communicate", new=communicate),
            mock.patch.object(flow.state, "write_state") as write_state,
            notify,
        ):
            flow._active_proc = None
            await flow.run_capture()

        repair_prompt, repair_photo = repair_args[1]
        self.assertEqual(repair_photo, "/tmp/photo.png")
        self.assertIn("La imagen adjunta en /tmp/photo.png", repair_prompt)


class FlowStallRetryTests(unittest.IsolatedAsyncioTestCase):
    """A provider-side stall surfaces as the OPENCODE_TIMEOUT timeout; the
    same request bytes complete when relaunched, so one retry is attempted."""

    def _patches(self, ocr_text=""):
        return (
            mock.patch.object(flow.portal, "take_screenshot", new=mock.AsyncMock(return_value="file:///capture.png")),
            mock.patch.object(flow, "save_photo", return_value="/tmp/photo.png"),
            mock.patch.object(flow.routing, "ocr_image", return_value=ocr_text),
            mock.patch.object(flow, "ensure_fuentes"),
            mock.patch.object(flow, "ensure_config"),
            mock.patch.object(flow, "_protected_names", return_value=("Productoria",)),
            mock.patch.object(flow.state, "clear_state"),
            mock.patch.object(flow.notify, "notify"),
        )

    async def test_stalled_main_pass_is_retried_once_and_delivers(self):
        launches = []

        async def launch(photo, request_prompt=None, expected_procedures=()):
            launches.append(request_prompt)
            return _Process()

        async def communicate(_proc):
            if len(launches) == 1:
                raise flow._FlowError("OpenCode tardó demasiado")
            return VALID_CAP1.encode(), b""

        screenshots, save_photo, ocr, fuentes, config, protected, clear, notify = self._patches()
        with (
            screenshots,
            save_photo,
            ocr,
            fuentes,
            config,
            protected,
            clear,
            mock.patch.object(flow, "_launch_opencode", new=launch),
            mock.patch.object(flow, "_communicate", new=communicate),
            mock.patch.object(flow.state, "write_state") as write_state,
            notify as notify_mock,
        ):
            flow._active_proc = None
            await flow.run_capture()

        self.assertEqual(len(launches), 2)
        self.assertIsNone(launches[0])
        self.assertIsNone(launches[1])
        write_state.assert_called_once()
        notify_mock.assert_not_called()

    async def test_stall_on_both_attempts_is_reported_without_saving(self):
        launches = []

        async def launch(photo, request_prompt=None, expected_procedures=()):
            launches.append(request_prompt)
            return _Process()

        async def communicate(_proc):
            raise flow._FlowError("OpenCode tardó demasiado")

        screenshots, save_photo, ocr, fuentes, config, protected, clear, notify = self._patches()
        with (
            screenshots,
            save_photo,
            ocr,
            fuentes,
            config,
            protected,
            clear,
            mock.patch.object(flow, "_launch_opencode", new=launch),
            mock.patch.object(flow, "_communicate", new=communicate),
            mock.patch.object(flow.state, "write_state") as write_state,
            notify as notify_mock,
        ):
            flow._active_proc = None
            await flow.run_capture()

        self.assertEqual(len(launches), 2)
        write_state.assert_not_called()
        notify_mock.assert_called_once_with("OpenCode tardó demasiado")

    async def test_stalled_repair_pass_is_retried_once_and_delivers(self):
        invalid = "RESPUESTA_TIPO1: #1\nRESPUESTA_TIPO2: Lucas[8]"
        launches = []
        calls = 0

        async def launch(photo, request_prompt=None, expected_procedures=()):
            launches.append(request_prompt)
            return _Process()

        async def communicate(_proc):
            nonlocal calls
            calls += 1
            if calls == 1:
                return invalid.encode(), b""  # main pass: invalid output
            if calls == 2:
                raise flow._FlowError("OpenCode tardó demasiado")  # repair stalls
            return VALID_CAP1.encode(), b""  # repair retry succeeds

        screenshots, save_photo, ocr, fuentes, config, protected, clear, notify = self._patches()
        with (
            screenshots,
            save_photo,
            ocr,
            fuentes,
            config,
            protected,
            clear,
            mock.patch.object(flow, "_launch_opencode", new=launch),
            mock.patch.object(flow, "_communicate", new=communicate),
            mock.patch.object(flow.state, "write_state") as write_state,
            notify as notify_mock,
        ):
            flow._active_proc = None
            await flow.run_capture()

        self.assertEqual(len(launches), 3)
        self.assertIsNone(launches[0])
        self.assertIn("ERROR DE VALIDACIÓN", launches[1])
        self.assertEqual(launches[1], launches[2])
        write_state.assert_called_once()
        notify_mock.assert_not_called()


class AgentConfigTests(unittest.TestCase):
    def test_agent_prompt_contract_is_self_contained(self):
        """The task scope and response rules remain in the per-request prompt."""

        prompt = flow.prompt.build_prompt(())
        self.assertIn("grep y read", prompt)
        self.assertIn("Puedes usar subagentes", prompt)
        self.assertIn("comandos de shell", prompt)
        for utility in ("Python 3", "ImageMagick", "GraphicsMagick", "FFmpeg"):
            self.assertIn(utility, prompt)
        self.assertIn("Mantén esos recursos dentro del alcance", prompt)
        self.assertIn("RESPUESTA_TIPO1:", prompt)
        self.assertIn("PROCEDIMIENTO: capN[, capN...]", prompt)

    def test_agent_prompt_mentions_index_when_available(self):
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as fuentes:
            with open(os.path.join(fuentes, "INDICE.md"), "w") as f:
                f.write("x")
            with mock.patch.dict(
                "os.environ", {"VICRE_FUENTES_DIR": fuentes}
            ):
                prompt = flow.prompt.build_prompt(())

        self.assertIn("INDICE.md", prompt)

    def test_agent_prompt_warns_against_whole_file_reads(self):
        self.assertIn("offset/limit", flow.prompt.build_prompt(()))

    def test_agent_config_uses_unrestricted_opencode2_permissions(self):
        config = json.loads(flow._agent_config())

        agent = config["agent"]["vicre"]
        self.assertEqual(config["permission"], "allow")
        self.assertEqual(agent["mode"], "primary")
        self.assertNotIn("prompt", agent)
        self.assertEqual(agent["permission"], "allow")

    def test_ensure_config_writes_under_current_workspace(self):
        with tempfile.TemporaryDirectory() as home:
            with mock.patch.object(flow, "HOME_DIR", home):
                flow.ensure_config()
                path = os.path.join(home, "opencode.json")
                with open(path, encoding="utf-8") as config_file:
                    first = config_file.read()
                flow.ensure_config()
                with open(path, encoding="utf-8") as config_file:
                    second = config_file.read()

        self.assertEqual(first, second)
        self.assertEqual(json.loads(first)["$schema"], "https://opencode.ai/config.json")


class FlowChapterFixupTests(unittest.IsolatedAsyncioTestCase):
    def _patches(self, ocr_text=""):
        return (
            mock.patch.object(flow.portal, "take_screenshot", new=mock.AsyncMock(return_value="file:///capture.png")),
            mock.patch.object(flow, "save_photo", return_value="/tmp/photo.png"),
            mock.patch.object(flow.routing, "ocr_image", return_value=ocr_text),
            mock.patch.object(flow, "ensure_fuentes"),
            mock.patch.object(flow, "ensure_config"),
            mock.patch.object(flow, "_protected_names", return_value=("Productoria",)),
            mock.patch.object(flow.state, "clear_state"),
            mock.patch.object(flow.notify, "notify"),
        )

    async def test_missing_chapter_marker_is_fixed_without_repair(self):
        missing_cap1 = (
            "RESPUESTA_TIPO1:\n"
            "#1: 7\n"
            "RESPUESTA_TIPO2:\n"
            "Productoria[{2, n, 1 + 2/i}, 5]\n"
            "PROCEDIMIENTO: cap2\n"
        )

        processes = [_Process()]

        async def launch(photo, request_prompt=None, expected_procedures=()):
            if request_prompt is not None:
                raise AssertionError("chapter-only fixes must not launch a repair")
            return processes.pop(0)

        async def communicate(_proc):
            return missing_cap1.encode(), b""

        screenshots, save_photo, ocr, fuentes, config, protected, clear, notify = self._patches(
            ocr_text="programa recursivo de pila Fibonacci"
        )
        with (
            screenshots,
            save_photo,
            ocr,
            fuentes,
            config,
            protected,
            clear,
            mock.patch.object(flow, "_launch_opencode", new=launch),
            mock.patch.object(flow, "_communicate", new=communicate),
            mock.patch.object(flow.state, "write_state") as write_state,
            notify,
        ):
            flow._active_proc = None
            await flow.run_capture()

        write_state.assert_called_once()
        self.assertEqual(
            write_state.call_args.kwargs["procedures"], ("cap2", "cap1")
        )


if __name__ == "__main__":
    unittest.main()
