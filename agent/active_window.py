import subprocess
import shutil
from loguru import logger

from agent.platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS, is_wayland, has_tool


def get_active_window_title() -> str:
    try:
        if IS_WINDOWS:
            return _get_active_window_windows()
        elif IS_LINUX:
            return _get_active_window_linux()
        elif IS_MACOS:
            return _get_active_window_macos()
        return f"Fitur active window belum didukung di OS ini."
    except Exception as e:
        logger.error(f"Error getting active window: {e}")
        return f"Gagal mendeteksi jendela aktif: {e}"


def _get_active_window_windows() -> str:
    import ctypes
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return "Unknown (No active window)"
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return "Unnamed Window"
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    return buff.value


def _get_active_window_linux() -> str:
    if has_tool("xdotool"):
        try:
            r = subprocess.run(["xdotool", "getactivewindow", "getwindowname"],
                               capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                title = r.stdout.strip()
                if "not found" not in title.lower():
                    return title
        except Exception as e:
            logger.debug(f"xdotool failed: {e}")

    if has_tool("xprop"):
        try:
            r_id = subprocess.run("xprop -root 32x '\t$0' _NET_ACTIVE_WINDOW | cut -f 2",
                                  shell=True, capture_output=True, text=True, timeout=5)
            if r_id.returncode == 0:
                win_id = r_id.stdout.strip()
                if win_id and win_id != "0x0":
                    r_title = subprocess.run(f"xprop -id {win_id} _NET_WM_NAME | cut -d '\"' -f 2",
                                             shell=True, capture_output=True, text=True, timeout=5)
                    title = r_title.stdout.strip()
                    if r_title.returncode == 0 and title and "not found" not in title.lower() and "_net_wm_name" not in title.lower():
                        return title
        except Exception as e:
            logger.debug(f"xprop failed: {e}")

    if is_wayland():
        apps = _detect_running_apps()
        return f"Wayland session. Aplikasi terdeteksi: {apps}"

    return "Unknown (Install xdotool untuk X11)"


def _detect_running_apps() -> str:
    import psutil
    common = {
        "chrome": "Chrome", "firefox": "Firefox", "brave": "Brave",
        "code": "VS Code", "nautilus": "Files",
        "gnome-terminal-server": "Terminal", "ptyxis": "Terminal",
        "spotify": "Spotify", "slack": "Slack", "discord": "Discord",
    }
    found = []
    for proc in psutil.process_iter(["name"]):
        try:
            name = proc.info["name"].lower()
            for key, label in common.items():
                if key in name and label not in found:
                    found.append(label)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return ", ".join(found) if found else "Tidak terdeteksi"


def _get_active_window_macos() -> str:
    try:
        r = subprocess.run("""osascript -e 'tell application "System Events"
            set frontmostProcess to first process whose frontmost is true
            try
                set windowName to name of first window of frontmostProcess
                return windowName
            on error
                return name of frontmostProcess
            end try
        end tell'""", shell=True, capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception as e:
        logger.debug(f"macOS active window failed: {e}")
    return "Unknown macOS window"
