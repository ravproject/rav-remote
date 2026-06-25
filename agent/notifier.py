import subprocess
import shutil
from loguru import logger

from agent.platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS, has_tool, has_python_module


def send_notification(title: str, message: str) -> bool:
    if IS_LINUX:
        if has_tool("notify-send"):
            try:
                subprocess.run(["notify-send", title, message], capture_output=True, timeout=5)
                return True
            except Exception:
                pass
        if has_python_module("plyer"):
            try:
                from plyer import notification
                notification.notify(title=title, message=message)
                return True
            except Exception:
                pass
        return False

    if IS_MACOS:
        try:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
            return True
        except Exception:
            pass
        if has_python_module("plyer"):
            try:
                from plyer import notification
                notification.notify(title=title, message=message)
                return True
            except Exception:
                pass
        return False

    if IS_WINDOWS:
        try:
            from plyer import notification
            notification.notify(title=title, message=message)
            return True
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, title, 0)
            return True
        except Exception:
            pass
        return False

    return False
