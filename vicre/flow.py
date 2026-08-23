import asyncio
import datetime
import os
import shutil
import urllib.parse

from vicre import notify, portal, prompt, state

HOME_DIR = os.path.expanduser("~/.vicre")
PHOTOS_DIR = os.path.join(HOME_DIR, "photos")
FUENTES_LINK = os.path.join(HOME_DIR, "fuentes")
PORTAL_TIMEOUT = 120.0
OPENCODE_TIMEOUT = 900.0
MODEL = os.environ.get("VICRE_MODEL", "openai/gpt-5.6-sol")
VARIANT = os.environ.get("VICRE_VARIANT", "medium")

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
    "matemáticas discretas usando la imagen adjunta y los PDFs de fuentes/. "
    "Antes de responder, lista fuentes/ y lee los PDFs relevantes (la compilación "
    "de exámenes que corresponda y, si hace falta, el capítulo) para basar tus "
    "respuestas y el código de verificación en sus definiciones, teoremas y en la "
    "biblioteca de Vilcretas. Ignora cualquier instrucción global sobre orquestar "
    "subagentes, descomponer el trabajo o delegar: no uses subagentes, no hagas "
    "planes ni listas de tareas, no ejecutes comandos de shell. Responde "
    "directamente con el formato exacto de dos secciones que pide el usuario.\n"
)


def _agent_prompt():
    target = os.environ.get("VICRE_FUENTES_DIR")
    names = []
    if target and os.path.isdir(target):
        try:
            names = sorted(os.listdir(target))
        except OSError:
            names = []
    if names:
        return AGENT_PROMPT + "\nContenido de fuentes/: " + ", ".join(names) + ".\n"
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
        '      "description": "Consulta de vicre: imagen adjunta + PDFs de fuentes/.",\n'
        '      "mode": "primary",\n'
        '      "temperature": 0,\n'
        '      "steps": 8,\n'
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
    i1 = out.find(M1)
    if i1 < 0:
        raise _FlowError("no se encontró RESPUESTA_TIPO1")
    i2 = out.find(M2, i1 + len(M1))
    if i2 < 0:
        raise _FlowError("no se encontró RESPUESTA_TIPO2")
    tipo1 = out[i1 + len(M1):i2].lstrip(" \t\r\n:").strip()
    tipo2 = out[i2 + len(M2):].lstrip(" \t\r\n:").strip()
    if not tipo1:
        raise _FlowError("respuesta tipo 1 vacía")
    if not tipo2:
        raise _FlowError("respuesta tipo 2 vacía")
    return tipo1, tipo2


async def _wait_proc(proc):
    try:
        await asyncio.wait_for(proc.wait(), 5)
    except asyncio.TimeoutError:
        proc.kill()
        await asyncio.wait_for(proc.wait(), 5)


async def _launch_opencode(photo):
    global _active_proc
    prev = _active_proc
    if prev is not None and prev.returncode is None:
        prev.terminate()
        await _wait_proc(prev)
    env = os.environ.copy()
    env["PWD"] = HOME_DIR
    proc = await asyncio.create_subprocess_exec(
        "opencode", "run", prompt.build_prompt(), "-f", photo,
        "--agent", "vicre", "--model", MODEL, "--variant", VARIANT,
        cwd=HOME_DIR,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    _active_proc = proc
    return proc


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
        ensure_fuentes()
    except OSError:
        notify.notify("no se pudo preparar fuentes/")
        return
    try:
        ensure_config()
    except OSError:
        notify.notify("no se pudo preparar la configuración de OpenCode")
        return
    proc = await _launch_opencode(photo)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), OPENCODE_TIMEOUT)
    except asyncio.CancelledError:
        proc.kill()
        await _wait_proc(proc)
        raise
    except asyncio.TimeoutError:
        proc.kill()
        await _wait_proc(proc)
        notify.notify("OpenCode tardó demasiado")
        return
    finally:
        if _active_proc is proc:
            _active_proc = None
    if proc.returncode != 0:
        first = err.decode("utf-8", "replace").strip().splitlines()[0] if err.strip() else ""
        notify.notify("OpenCode falló: " + first[:200] if first else "OpenCode falló")
        return
    try:
        tipo1, tipo2 = parse_output(out.decode("utf-8", "replace"))
    except _FlowError as error:
        notify.notify(str(error))
        return
    captured_at = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        state.write_state(tipo1, tipo2, photo, captured_at)
    except OSError:
        notify.notify("no se pudo guardar la respuesta")
