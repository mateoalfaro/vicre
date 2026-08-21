import asyncio
import uuid

from dbus_next.aio import MessageBus
from dbus_next import BusType, Variant

PORTAL_BUS = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
REQUEST_IFACE = "org.freedesktop.portal.Request"
REQUEST_XML = ('<node><interface name="org.freedesktop.portal.Request">'
               '<signal name="Response"><arg type="u" name="response"/>'
               '<arg type="a{sv}" name="results"/></signal></interface></node>')


class PortalError(Exception):
    pass


def _predicted_handle(token, unique_name):
    sender = unique_name.lstrip(":").replace(".", "_")
    return f"{PORTAL_PATH}/request/{sender}/{token}"


async def _request_uri(bus):
    token = "vicre_" + uuid.uuid4().hex
    handle = _predicted_handle(token, bus.unique_name)
    portal_node = await bus.introspect(PORTAL_BUS, PORTAL_PATH)
    portal_proxy = bus.get_proxy_object(PORTAL_BUS, PORTAL_PATH, portal_node)
    screenshot = portal_proxy.get_interface("org.freedesktop.portal.Screenshot")
    request_proxy = bus.get_proxy_object(PORTAL_BUS, handle, REQUEST_XML)
    request_iface = request_proxy.get_interface(REQUEST_IFACE)
    loop = asyncio.get_running_loop()
    done = loop.create_future()

    def on_response(code, results):
        if not done.done():
            done.set_result((code, results))

    request_iface.on_response = on_response
    reply = await screenshot.call_screenshot("", {"handle_token": Variant("s", token)})
    actual = reply if isinstance(reply, str) else reply[0]
    if actual != handle:
        extra = bus.get_proxy_object(PORTAL_BUS, actual, REQUEST_XML)
        extra.get_interface(REQUEST_IFACE).on_response = on_response
    code, results = await done
    if code != 0:
        raise PortalError(f"el portal respondió con código {code}")
    uri = results.get("uri")
    if uri is None:
        raise PortalError("el portal no devolvió una uri")
    return uri.value


async def take_screenshot(timeout=120.0):
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    try:
        return await asyncio.wait_for(_request_uri(bus), timeout)
    finally:
        bus.disconnect()