import subprocess
import shutil
import webbrowser
from loguru import logger

from agent.platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS, has_tool, launch_app


def prepare_meeting(meeting_name: str = "Meeting") -> str:
    actions = []
    if IS_LINUX:
        try:
            subprocess.run(["gsettings", "set", "org.gnome.desktop.notifications", "show-banners", "false"],
                           capture_output=True, timeout=3)
            actions.append("Notifikasi dimatikan")
        except Exception:
            pass
    elif IS_MACOS:
        try:
            subprocess.run(["osascript", "-e",
                           'tell application "System Events" to tell notification center to set its dnd state to true'],
                           capture_output=True, timeout=5)
            actions.append("Notifikasi dimatikan")
        except Exception:
            pass
    elif IS_WINDOWS:
        import ctypes
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000003)
            actions.append("Notifikasi dimatikan")
        except Exception:
            pass

    meeting_lower = meeting_name.lower()
    if "zoom" in meeting_lower:
        if IS_LINUX and has_tool("zoom"):
            subprocess.Popen(["zoom"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            actions.append("Zoom dibuka")
        elif IS_MACOS:
            subprocess.Popen(["open", "-a", "zoom.us"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            actions.append("Zoom dibuka")
        elif IS_WINDOWS:
            subprocess.Popen(["start", "zoom"], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            actions.append("Zoom dibuka")
    elif "teams" in meeting_lower:
        if IS_LINUX and has_tool("teams"):
            subprocess.Popen(["teams"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            actions.append("Teams dibuka")
        elif IS_MACOS:
            subprocess.Popen(["open", "-a", "Microsoft Teams"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            actions.append("Teams dibuka")
        elif IS_WINDOWS:
            subprocess.Popen(["start", "Teams"], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            actions.append("Teams dibuka")
    elif "meet" in meeting_lower or "google" in meeting_lower:
        webbrowser.open("https://meet.google.com")
        actions.append("Google Meet dibuka")

    if actions:
        return f"Mode Meeting '{meeting_name}': " + ", ".join(actions) + "."
    return f"Mode Meeting '{meeting_name}' diaktifkan."
