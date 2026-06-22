"""
Night Mode — toggle dark mode and blue light filter.
"""
import subprocess
import shutil
from loguru import logger

def night_mode_on() -> str:
    actions = []
    try:
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "prefer-dark"],
                       capture_output=True, timeout=3)
        actions.append("Dark mode GNOME")
    except Exception:
        pass
    if shutil.which("redshift"):
        try:
            subprocess.Popen(["redshift", "-O", "3500"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            actions.append("Redshift 3500K")
        except Exception:
            pass
    elif shutil.which("gammastep"):
        try:
            subprocess.Popen(["gammastep", "-O", "3500"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            actions.append("Gammastep 3500K")
        except Exception:
            pass
    else:
        actions.append("blue light filter tidak tersedia (install redshift atau gammastep)")
    if not actions:
        return "Night Mode tidak didukung di sistem ini."
    return "🌙 Night Mode AKTIF: " + ", ".join(actions) + "."

def night_mode_off() -> str:
    actions = []
    try:
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "default"],
                       capture_output=True, timeout=3)
        actions.append("Dark mode dimatikan")
    except Exception:
        pass
    if shutil.which("redshift"):
        try:
            subprocess.run(["redshift", "-x"], capture_output=True, timeout=3)
            actions.append("Redshift direset")
        except Exception:
            pass
    elif shutil.which("gammastep"):
        try:
            subprocess.run(["gammastep", "-x"], capture_output=True, timeout=3)
            actions.append("Gammastep direset")
        except Exception:
            pass
    if not actions:
        return "Night Mode tidak aktif."
    return "🌙 Night Mode NONAKTIF: " + ", ".join(actions) + "."
