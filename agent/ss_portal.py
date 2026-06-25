#!/usr/bin/env python3
"""
Wayland screenshot via GNOME Shell D-Bus API (no dialog).
Fallback ke xdg-desktop-portal jika GNOME Shell API tidak tersedia.
Outputs PNG bytes to stdout.
Exit code 0 on success, 1 on failure.
"""
import dbus
import dbus.mainloop.glib
import sys
import os
import tempfile
import subprocess

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
from gi.repository import GLib


def screenshot_via_gnome_shell() -> bytes:
    """GNOME Shell Screenshot API — no dialog, langsung capture."""
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    try:
        bus = dbus.SessionBus()
        shell_iface = bus.get_object(
            "org.gnome.Shell.Screenshot",
            "/org/gnome/Shell/Screenshot"
        )
        iface = dbus.Interface(shell_iface, "org.gnome.Shell.Screenshot")
        success, filename = iface.Screenshot(
            dbus.Boolean(False),  # include_cursor
            dbus.Boolean(False),  # flash
            dbus.String(tmp.name)  # filename
        )
        if success and os.path.exists(tmp.name):
            with open(tmp.name, "rb") as f:
                return f.read()
    except Exception as e:
        print(f"GNOME Shell Screenshot failed: {e}", file=sys.stderr)
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
    return None


def screenshot_via_portal() -> bytes:
    """Fallback ke xdg-desktop-portal (mungkin muncul dialog)."""
    result = [None]
    loop = GLib.MainLoop()

    bus = dbus.SessionBus()
    portal = bus.get_object(
        "org.freedesktop.portal.Desktop",
        "/org/freedesktop/portal/desktop"
    )
    iface = dbus.Interface(portal, "org.freedesktop.portal.Screenshot")

    def handle_response(response, results, path=""):
        if response == 0:
            uri = results.get("uri", "")
            if uri:
                file_path = uri.replace("file://", "")
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        result[0] = f.read()
                    try:
                        os.unlink(file_path)
                    except Exception:
                        pass
        loop.quit()

    bus.add_signal_receiver(
        handle_response,
        signal_name="Response",
        dbus_interface="org.freedesktop.portal.Request",
        path_keyword="path",
    )

    try:
        iface.Screenshot(
            "",
            {"handle_token": dbus.String("rav_ss", variant_level=1), "interactive": False}
        )
    except Exception as e:
        print(f"Portal call failed: {e}", file=sys.stderr)
        loop.quit()
        return None

    GLib.timeout_add_seconds(15, loop.quit)
    loop.run()
    return result[0]


def main():
    data = screenshot_via_gnome_shell()
    if not data:
        data = screenshot_via_portal()
    if data:
        sys.stdout.buffer.write(data)
        return True
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
