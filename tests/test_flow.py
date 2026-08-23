import unittest
from unittest import mock

from vicre import flow


VALID_REPEATED = """
RESPUESTA_TIPO1:
#1: respuesta
RESPUESTA_TIPO2:
Table[{n, RepeatedTiming[f[n]][[1]]}, {n, 1, 10}]
ListLinePlot[data]
PROCEDIMIENTO: timing_repeated
"""


class _Process:
    def __init__(self, returncode=0):
        self.returncode = returncode


class FlowRepairTests(unittest.IsolatedAsyncioTestCase):
    async def test_one_validation_repair_then_only_validated_result_is_saved(self):
        initial = "RESPUESTA_TIPO1: #1: respuesta\nRESPUESTA_TIPO2: Sum[x, {x, 1, n}]"
        processes = [_Process(), _Process()]
        launch_prompts = []

        async def launch(photo, request_prompt=None, expected_procedures=()):
            launch_prompts.append(request_prompt)
            return processes.pop(0)

        async def communicate(_proc):
            if len(launch_prompts) == 1:
                return initial.encode(), b""
            return VALID_REPEATED.encode(), b""

        with (
            mock.patch.object(flow.portal, "take_screenshot", new=mock.AsyncMock(return_value="file:///capture.png")),
            mock.patch.object(flow, "save_photo", return_value="/tmp/photo.png"),
            mock.patch.object(flow.routing, "ocr_image", return_value=""),
            mock.patch.object(flow, "ensure_fuentes"),
            mock.patch.object(flow, "ensure_config"),
            mock.patch.object(flow, "_launch_opencode", new=launch),
            mock.patch.object(flow, "_communicate", new=communicate),
            mock.patch.object(flow.state, "clear_state"),
            mock.patch.object(flow.state, "write_state") as write_state,
            mock.patch.object(flow.notify, "notify"),
        ):
            flow._active_proc = None
            await flow.run_capture()

        self.assertEqual(len(launch_prompts), 2)
        self.assertIsNone(launch_prompts[0])
        self.assertIn("ERROR DE VALIDACIÓN", launch_prompts[1])
        write_state.assert_called_once()
        self.assertEqual(write_state.call_args.args[:2], ("#1: respuesta", "Table[{n, RepeatedTiming[f[n]][[1]]}, {n, 1, 10}]\nListLinePlot[data]"))
        self.assertEqual(write_state.call_args.kwargs["procedures"], ("timing_repeated",))

    async def test_invalid_second_repair_is_not_saved_and_still_launches_only_twice(self):
        invalid = "RESPUESTA_TIPO1: #1\nRESPUESTA_TIPO2: Sum[x, {x, 1, n}]"
        processes = [_Process(), _Process()]
        launches = []

        async def launch(photo, request_prompt=None, expected_procedures=()):
            launches.append(request_prompt)
            return processes.pop(0)

        async def communicate(_proc):
            return invalid.encode(), b""

        with (
            mock.patch.object(flow.portal, "take_screenshot", new=mock.AsyncMock(return_value="file:///capture.png")),
            mock.patch.object(flow, "save_photo", return_value="/tmp/photo.png"),
            mock.patch.object(flow.routing, "ocr_image", return_value=""),
            mock.patch.object(flow, "ensure_fuentes"),
            mock.patch.object(flow, "ensure_config"),
            mock.patch.object(flow, "_launch_opencode", new=launch),
            mock.patch.object(flow, "_communicate", new=communicate),
            mock.patch.object(flow.state, "clear_state"),
            mock.patch.object(flow.state, "write_state") as write_state,
            mock.patch.object(flow.notify, "notify"),
        ):
            flow._active_proc = None
            await flow.run_capture()

        self.assertEqual(len(launches), 2)
        write_state.assert_not_called()

    async def test_ocr_hints_are_passed_to_prompt_and_validation(self):
        output = """
RESPUESTA_TIPO1:
#1: respuesta
RESPUESTA_TIPO2:
Table[{n, RepeatedTiming[f[n]][[1]]}, {n, 1, 10}]
ListLinePlot[data]
PROCEDIMIENTO: timing_repeated
"""
        proc = _Process()
        launch_calls = []

        async def launch(photo, request_prompt=None, expected_procedures=()):
            launch_calls.append((request_prompt, expected_procedures))
            return proc

        async def communicate(_proc):
            return output.encode(), b""

        with (
            mock.patch.object(flow.portal, "take_screenshot", new=mock.AsyncMock(return_value="file:///capture.png")),
            mock.patch.object(flow, "save_photo", return_value="/tmp/photo.png"),
            mock.patch.object(flow.routing, "ocr_image", return_value="RepeatedTiming ListLinePlot"),
            mock.patch.object(flow, "ensure_fuentes"),
            mock.patch.object(flow, "ensure_config"),
            mock.patch.object(flow, "_launch_opencode", new=launch),
            mock.patch.object(flow, "_communicate", new=communicate),
            mock.patch.object(flow.state, "clear_state"),
            mock.patch.object(flow.state, "write_state") as write_state,
            mock.patch.object(flow.notify, "notify"),
        ):
            flow._active_proc = None
            await flow.run_capture()

        self.assertEqual(launch_calls[0][1], ("timing_repeated",))
        write_state.assert_called_once()

    async def test_process_launch_oserror_is_reported_without_saving(self):
        async def launch(photo, request_prompt=None, expected_procedures=()):
            raise OSError("opencode missing")

        with (
            mock.patch.object(flow.portal, "take_screenshot", new=mock.AsyncMock(return_value="file:///capture.png")),
            mock.patch.object(flow, "save_photo", return_value="/tmp/photo.png"),
            mock.patch.object(flow.routing, "ocr_image", return_value=""),
            mock.patch.object(flow, "ensure_fuentes"),
            mock.patch.object(flow, "ensure_config"),
            mock.patch.object(flow, "_launch_opencode", new=launch),
            mock.patch.object(flow.state, "clear_state"),
            mock.patch.object(flow.state, "write_state") as write_state,
            mock.patch.object(flow.notify, "notify") as notify,
        ):
            flow._active_proc = None
            await flow.run_capture()

        write_state.assert_not_called()
        notify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
