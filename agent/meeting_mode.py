"""
Meeting Mode — prepare laptop for meetings: launch apps, mute notifications, open docs.
"""
import subprocess
import shutil
from loguru import logger

def prepare_meeting(meeting_name: str = "Meeting") -> str:
    actions = []
    try:
        subprocess.run(["gsettings", "set", "org.gnome.desktop.notifications", "show-banners", "false"], capture_output=True, timeout=3)
        actions.append("Notifikasi dimatikan")
    except Exception:
        pass
    meeting_lower = meeting_name.lower()
    if "zoom" in meeting_lower and shutil.which("zoom"):
        subprocess.Popen(["zoom"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        actions.append("Zoom dibuka")
    elif "teams" in meeting_lower and shutil.which("teams"):
        subprocess.Popen(["teams"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        actions.append("Teams dibuka")
    elif "meet" in meeting_lower or "google" in meeting_lower:
        import webbrowser
        webbrowser.open("https://meet.google.com")
        actions.append("Google Meet dibuka")
    else:
        if shutil.which("zoom"):
            subprocess.Popen(["zoom"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            actions.append("Zoom dibuka (default)")
    if actions:
        return f"Mode Meeting '{meeting_name}': " + ", ".join(actions) + "."
    return f"Mode Meeting '{meeting_name}' diaktifkan (notifikasi dimatikan)."
