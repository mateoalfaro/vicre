import asyncio
import os

from vicre import flow

_capture_task = None


def _socket_path():
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime:
        raise RuntimeError("XDG_RUNTIME_DIR no está definido")
    return os.path.join(runtime, "vicre.sock")


async def _handle_client(reader, writer):
    try:
        line = await asyncio.wait_for(reader.readline(), 10)
    except (asyncio.TimeoutError, ConnectionError, OSError):
        writer.close()
        return
    writer.write(b"ok\n")
    await writer.drain()
    writer.close()
    global _capture_task
    if line.strip() == b"capture":
        if _capture_task is not None and not _capture_task.done():
            _capture_task.cancel()
            try:
                await _capture_task
            except (asyncio.CancelledError, Exception):
                pass
        _capture_task = asyncio.create_task(flow.run_capture())


async def main():
    path = _socket_path()
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    server = await asyncio.start_unix_server(_handle_client, path=path)
    try:
        async with server:
            await server.serve_forever()
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
    return 0