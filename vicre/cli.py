import argparse
import asyncio
import os
import socket
import sys

from vicre import daemon, flow, keybinds, notify, state, typewriter


def _socket_path():
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime:
        return None
    return os.path.join(runtime, "vicre.sock")


def _send_capture():
    path = _socket_path()
    if not path:
        return False
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        sock.connect(path)
        sock.sendall(b"capture\n")
        reply = sock.recv(64)
        return reply.strip() == b"ok"
    except OSError:
        return False
    finally:
        sock.close()


def _capture():
    if _send_capture():
        return 0
    asyncio.run(flow.run_capture())
    return 0


def _paste(key):
    data = state.read_state()
    text = data.get(key, "") if isinstance(data, dict) else ""
    if not text:
        notify.notify("No hay respuesta aún")
        return 0
    try:
        typewriter.type_text(text)
    except Exception:
        notify.notify("no se pudo escribir la respuesta")
        return 1
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="vicre", description="Captura, consulta a OpenCode y escribe respuestas")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("daemon", help="servicio de captura")
    sub.add_parser("capture", help="captura de pantalla y consulta")
    sub.add_parser("paste1", help="pega la respuesta tipo 1")
    sub.add_parser("paste2", help="pega la respuesta tipo 2")
    sub.add_parser("apply-keybinds", help="configura los atajos de GNOME")
    args = parser.parse_args(argv)
    try:
        if args.command == "daemon":
            return asyncio.run(daemon.main())
        if args.command == "capture":
            return _capture()
        if args.command == "paste1":
            return _paste("tipo1")
        if args.command == "paste2":
            return _paste("tipo2")
        if args.command == "apply-keybinds":
            keybinds.apply()
            return 0
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        print(f"vicre: {error}", file=sys.stderr)
        return 1
    return 2