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
MODEL = os.environ.get("VICRE_MODEL", "openai/gpt-5.6-terra")
VARIANT = os.environ.get("VICRE_VARIANT", "xhigh")

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
    proc = await asyncio.create_subprocess_exec(
        "opencode", "run", prompt.build_prompt(), "-f", photo,
        "--model", MODEL, "--variant", VARIANT,
        cwd=HOME_DIR,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        env=os.environ.copy(),
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
    proc = await _launch_opencode(photo)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), OPENCODE_TIMEOUT)
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
        notify.notify("OpenCode falló")
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