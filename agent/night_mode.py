import subprocess
import shutil
from loguru import logger

from agent.platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS, has_tool, detect_desktop


def night_mode_on() -> str:
    actions = []

    if IS_LINUX:
        de = detect_desktop()
        if de == "gnome":
            try:
                subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "prefer-dark"],
                               capture_output=True, timeout=3)
                actions.append("Dark mode GNOME")
            except Exception:
                pass
        if has_tool("redshift"):
            try:
                subprocess.Popen(["redshift", "-O", "3500"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                actions.append("Redshift 3500K")
            except Exception:
                pass
        elif has_tool("gammastep"):
            try:
                subprocess.Popen(["gammastep", "-O", "3500"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                actions.append("Gammastep 3500K")
            except Exception:
                pass
        if not any("redshift" in a.lower() or "gammastep" in a.lower() or "dark" in a.lower() for a in actions):
            actions.append("Install redshift/gammastep untuk filter cahaya biru")

    elif IS_MACOS:
        try:
            subprocess.run(["defaults", "write", "-g", "AppleInterfaceStyle", "Dark"],
                           capture_output=True, timeout=5)
            actions.append("Dark mode macOS")
        except Exception:
            pass
        try:
            subprocess.run(["osascript", "-e",
                           'tell application "System Events" to tell appearance preferences to set dark mode to true'],
                           capture_output=True, timeout=5)
            actions.append("Dark mode (Appearance)")
        except Exception:
            pass

    elif IS_WINDOWS:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            actions.append("Dark mode Windows")
        except Exception:
            pass

    if not actions:
        return "Night Mode tidak didukung di sistem ini."
    return "Night Mode AKTIF: " + ", ".join(actions) + "."


def night_mode_off() -> str:
    actions = []

    if IS_LINUX:
        de = detect_desktop()
        if de == "gnome":
            try:
                subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "default"],
                               capture_output=True, timeout=3)
                actions.append("Dark mode dimatikan")
            except Exception:
                pass
        if has_tool("redshift"):
            try:
                subprocess.run(["redshift", "-x"], capture_output=True, timeout=3)
                actions.append("Redshift direset")
            except Exception:
                pass
        elif has_tool("gammastep"):
            try:
                subprocess.run(["gammastep", "-x"], capture_output=True, timeout=3)
                actions.append("Gammastep direset")
            except Exception:
                pass

    elif IS_MACOS:
        try:
            subprocess.run(["defaults", "write", "-g", "AppleInterfaceStyle", "Light"],
                           capture_output=True, timeout=5)
            actions.append("Light mode macOS")
        except Exception:
            pass
        try:
            subprocess.run(["osascript", "-e",
                           'tell application "System Events" to tell appearance preferences to set dark mode to false'],
                           capture_output=True, timeout=5)
            actions.append("Light mode (Appearance)")
        except Exception:
            pass

    elif IS_WINDOWS:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            actions.append("Light mode Windows")
        except Exception:
            pass

    if not actions:
        return "Night Mode tidak aktif."
    return "Night Mode NONAKTIF: " + ", ".join(actions) + "."
