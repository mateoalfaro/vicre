import asyncio
import datetime
import os
import shutil
import urllib.parse

from vicre import consultation, notify, portal, prompt, routing, state

HOME_DIR = os.path.expanduser("~/.vicre")
PHOTOS_DIR = os.path.join(HOME_DIR, "photos")
FUENTES_LINK = os.path.join(HOME_DIR, "fuentes")
PORTAL_TIMEOUT = 120.0
OPENCODE_TIMEOUT = 900.0
MODEL = os.environ.get("VICRE_MODEL", "opencode-go/glm-5.3-flash")
VARIANT = os.environ.get("VICRE_VARIANT", "max")

M1 = "RESPUESTA_TIPO1"
M2 = "RESPUESTA_TIPO2"

_active_proc = None


class _FlowError(Exception):
    pass


def save_photo(uri):
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme == "file":
        src = urllib.parse.unquote(parsed.path)
    elif not parsed.scheme:
        src = uri
    else:
        raise _FlowError(f"uri inesperada: {parsed.scheme}")
    if not os.path.isfile(src):
        raise _FlowError("el archivo de la captura no existe")
    name = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".png"
    dst = os.path.join(PHOTOS_DIR, name)
    shutil.copyfile(src, dst)
    return dst


def ensure_fuentes():
    target = os.environ.get("VICRE_FUENTES_DIR")
    if not target:
        return
    if os.path.islink(FUENTES_LINK):
        if os.readlink(FUENTES_LINK) == target:
            return
        os.remove(FUENTES_LINK)
    elif os.path.exists(FUENTES_LINK):
        return
    os.symlink(target, FUENTES_LINK)


AGENT_PROMPT_PATH = os.path.join(HOME_DIR, "vicre-agent-prompt.md")
AGENT_CONFIG_PATH = os.path.join(HOME_DIR, "opencode.json")

AGENT_PROMPT = (
    "Eres el agente de consulta de vicre: respondes preguntas de exámenes de "
    "matemáticas discretas usando la imagen adjunta y el cuadernillo maestro "
    "del curso en fuentes/. Lee primero fuentes/INDICE.md; elige parte y "
    "capítulo según cada pregunta (tipo-examen-capN.md y complementarios-"
    "capN.md son los más útiles) y localiza con grep los ejercicios resueltos "
    "análogos antes de responder: grep da números de línea, así que usa read "
    "con offset/limit sobre ese rango, nunca leas archivos completos. No "
    "busques ni inventes material fuera del cuadernillo. Ignora cualquier "
    "instrucción global sobre orquestar subagentes, descomponer el trabajo o "
    "delegar: no uses subagentes, no hagas planes ni listas de tareas, no "
    "ejecutes comandos de shell. "
    "Responde directamente con el formato exacto de las tres secciones "
    "que pide el usuario: tu primera línea debe ser exactamente "
    "RESPUESTA_TIPO1: sin saludos, introducciones ni explicaciones previas, "
    "y PROCEDIMIENTO queda como última línea. Si agotas los pasos o no "
    "encuentras el ejercicio exacto, responde igualmente con las tres "
    "secciones usando tu criterio matemático y la sintaxis del curso; jamás "
    "entregues un resumen del trabajo realizado. Las funciones "
    "de VilCretas ya están cargadas: llámalas tal cual, nunca las redefinas "
    "con patrones como f[n_] := ... .\n"
)


def _agent_prompt():
    target = os.environ.get("VICRE_FUENTES_DIR")
    if target and os.path.exists(os.path.join(target, "INDICE.md")):
        return AGENT_PROMPT + "\nEmpieza por fuentes/INDICE.md.\n"
    return AGENT_PROMPT


def _external_directory_rule():
    target = os.environ.get("VICRE_FUENTES_DIR")
    if not target:
        return '        "external_directory": "deny"\n'
    return (
        '        "external_directory": {\n'
        '          "*": "deny",\n'
        f'          "{target}/*": "allow"\n'
        '        }\n'
    )


def _agent_config():
    return (
        '{\n'
        '  "$schema": "https://opencode.ai/config.json",\n'
        '  "agent": {\n'
        '    "vicre": {\n'
        '      "description": "Consulta de vicre: imagen adjunta + cuadernillo maestro en fuentes/.",\n'
        '      "mode": "primary",\n'
        '      "temperature": 0,\n'
        '      "steps": 16,\n'
        '      "prompt": "{file:./vicre-agent-prompt.md}",\n'
        '      "permission": {\n'
        '        "read": "allow",\n'
        '        "glob": "allow",\n'
        '        "grep": "allow",\n'
        '        "list": "allow",\n'
        '        "edit": "deny",\n'
        '        "bash": "deny",\n'
        '        "task": "deny",\n'
        '        "webfetch": "deny",\n'
        '        "websearch": "deny",\n'
        '        "todowrite": "deny",\n'
        '        "skill": "deny",\n'
        + _external_directory_rule()
        + '      }\n'
        '    }\n'
        '  }\n'
        '}\n'
    )


def ensure_config():
    os.makedirs(HOME_DIR, exist_ok=True)
    for path, content in ((AGENT_PROMPT_PATH, _agent_prompt()), (AGENT_CONFIG_PATH, _agent_config())):
        try:
            with open(path, "r", encoding="utf-8") as f:
                if f.read() == content:
                    continue
        except FileNotFoundError:
            pass
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)


def parse_output(out):
    """Compatibility wrapper retaining the old two-string flow API."""

    result = consultation.parse_and_validate(out)
    return result.tipo1, result.tipo2


async def _wait_proc(proc):
    try:
        await asyncio.wait_for(proc.wait(), 5)
    except asyncio.TimeoutError:
        proc.kill()
        await asyncio.wait_for(proc.wait(), 5)


async def _launch_opencode(photo, request_prompt=None, expected_procedures=()):
    global _active_proc
    prev = _active_proc
    if prev is not None and prev.returncode is None:
        prev.terminate()
        await _wait_proc(prev)
    env = os.environ.copy()
    env["PWD"] = HOME_DIR
    model = f"{MODEL}#{VARIANT}" if VARIANT else MODEL
    proc = await asyncio.create_subprocess_exec(
        "opencode2", "run",
        request_prompt or prompt.build_prompt(expected_procedures), "-f", photo,
        "--agent", "vicre", "--model", model,
        cwd=HOME_DIR,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    _active_proc = proc
    return proc


async def _communicate(proc):
    """Collect one process while preserving cancellation and active-proc state."""

    global _active_proc
    try:
        return await asyncio.wait_for(proc.communicate(), OPENCODE_TIMEOUT)
    except asyncio.CancelledError:
        proc.kill()
        await _wait_proc(proc)
        raise
    except asyncio.TimeoutError as error:
        proc.kill()
        await _wait_proc(proc)
        raise _FlowError("OpenCode tardó demasiado") from error
    finally:
        if _active_proc is proc:
            _active_proc = None


async def _consulta(photo, request_prompt=None, expected_procedures=()):
    """Run one consulta pass, retrying exactly once on a provider stall.

    crof.ai occasionally opens a stream that never yields a byte; the request
    is healthy when relaunched immediately (verified by replaying the same
    request bytes).  The stall surfaces here as the OPENCODE_TIMEOUT
    wall-clock timeout, so one relaunch converts a dead wait into a delivered
    answer.  Only the stall retries: OSError (missing binary) propagates for
    the caller to report.
    """
    proc = await _launch_opencode(photo, request_prompt, expected_procedures)
    try:
        return proc, await _communicate(proc)
    except _FlowError:
        proc = await _launch_opencode(photo, request_prompt, expected_procedures)
        return proc, await _communicate(proc)


def _protected_names():
    target = os.environ.get("VICRE_FUENTES_DIR") or FUENTES_LINK
    try:
        with open(os.path.join(target, "funciones-vilcretas.txt"), encoding="utf-8") as f:
            names = [line.strip() for line in f if line.strip()]
    except (OSError, UnicodeDecodeError):
        return ()
    return tuple(names)


def _dump_raw(text):
    try:
        with open(os.path.join(HOME_DIR, "last-raw.txt"), "w", encoding="utf-8") as f:
            f.write(text)
    except OSError:
        pass


async def run_capture():
    state.clear_state()
    global _active_proc
    try:
        uri = await asyncio.wait_for(portal.take_screenshot(), PORTAL_TIMEOUT)
    except asyncio.CancelledError:
        raise
    except asyncio.TimeoutError:
        notify.notify("la captura del portal agotó el tiempo de espera")
        return
    except Exception:
        notify.notify("no se pudo capturar la pantalla")
        return
    try:
        photo = save_photo(uri)
    except Exception:
        notify.notify("no se pudo guardar la foto")
        return
    try:
        # OCR is local and cheap but blocking; keep it off the daemon loop so
        # a newer capture can still cancel this Consulta immediately.
        ocr_text = await asyncio.to_thread(routing.ocr_image, photo)
        expected_procedures = routing.infer_expected_procedures(ocr_text)
    except Exception:
        # OCR is a best-effort routing hint. It must never prevent a capture.
        expected_procedures = ()
    try:
        ensure_fuentes()
    except OSError:
        notify.notify("no se pudo preparar fuentes/")
        return
    try:
        ensure_config()
    except OSError:
        notify.notify("no se pudo preparar la configuración de OpenCode")
        return
    try:
        proc, (out, err) = await _consulta(
            photo, expected_procedures=expected_procedures
        )
    except OSError:
        notify.notify("no se pudo iniciar OpenCode")
        return
    except _FlowError as error:
        notify.notify(str(error))
        return
    if proc.returncode != 0:
        first = err.decode("utf-8", "replace").strip().splitlines()[0] if err.strip() else ""
        notify.notify("OpenCode falló: " + first[:200] if first else "OpenCode falló")
        return
    raw_output = out.decode("utf-8", "replace")
    protected_names = _protected_names()
    try:
        result = consultation.parse_and_validate(
            raw_output,
            expected_procedures=expected_procedures,
            protected_names=protected_names,
        )
    except consultation.ConsultationValidationError as error:
        # A response whose only defect is a PROCEDIMIENTO marker missing
        # OCR-routed chapters is completed locally: the marker is Vicre
        # metadata that never reaches the paste, so a full repair pass would
        # add minutes without changing the answer.  Anything else keeps the
        # one-repair fallback below.
        fixed_output = consultation.complete_expected_procedures(
            raw_output, error
        )
        if fixed_output is not None:
            try:
                result = consultation.parse_and_validate(
                    fixed_output,
                    expected_procedures=expected_procedures,
                    protected_names=protected_names,
                )
            except consultation.ConsultationValidationError:
                fixed_output = None
        if fixed_output is None:
            _dump_raw(raw_output)
            # One and only one focused repair is attempted.  A second invalid
            # result is discarded just like the first one.
            try:
                repair_proc, (repair_out, repair_err) = await _consulta(
                    photo,
                    prompt.build_repair_prompt(
                        str(error), raw_output, expected_procedures
                    ),
                )
            except OSError:
                notify.notify("no se pudo iniciar OpenCode para corregir")
                return
            except _FlowError as repair_error:
                notify.notify(str(repair_error))
                return
            if repair_proc.returncode != 0:
                first = (
                    repair_err.decode("utf-8", "replace").strip().splitlines()[0]
                    if repair_err.strip()
                    else ""
                )
                notify.notify(
                    "OpenCode falló al corregir: " + first[:200]
                    if first
                    else "OpenCode falló al corregir"
                )
                return
            try:
                result = consultation.parse_and_validate(
                    repair_out.decode("utf-8", "replace"),
                    expected_procedures=expected_procedures,
                    protected_names=protected_names,
                )
            except consultation.ConsultationValidationError as repair_error:
                _dump_raw(repair_out.decode("utf-8", "replace"))
                notify.notify(str(repair_error))
                return
    captured_at = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        state.write_state(
            result.tipo1,
            result.tipo2,
            photo,
            captured_at,
            procedures=result.procedures,
        )
    except OSError:
        notify.notify("no se pudo guardar la respuesta")
