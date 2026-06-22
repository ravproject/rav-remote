"""
Active Window Modul — Mendeteksi jendela aplikasi yang sedang aktif/fokus saat ini secara cross-platform.
"""
import subprocess
import platform
import shutil
from loguru import logger

def get_active_window_title() -> str:
    """
    Get the title of the currently active/focused window.
    Supports Windows, Linux (X11), and macOS.
    """
    current_os = platform.system()
    try:
        if current_os == "Windows":
            return _get_active_window_windows()
        elif current_os == "Linux":
            return _get_active_window_linux()
        elif current_os == "Darwin": # macOS
            return _get_active_window_macos()
        else:
            return f"❌ Fitur active window belum didukung di OS: {current_os}"
    except Exception as e:
        logger.error(f"Error getting active window title: {e}")
        return f"❌ Gagal mendeteksi jendela aktif: {str(e)}"

def _get_active_window_windows() -> str:
    """Get active window title on Windows using ctypes."""
    import ctypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return "Unknown (No active window)"
        
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return "Unnamed Window"
        
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    return buff.value

def _get_active_gui_apps() -> str:
    import psutil
    import os
    try:
        current_user = os.getlogin()
    except Exception:
        import getpass
        current_user = getpass.getuser()

    common_apps = {
        "chrome": "Google Chrome",
        "firefox": "Firefox",
        "code": "VS Code",
        "telegram-desktop": "Telegram",
        "slack": "Slack",
        "discord": "Discord",
        "spotify": "Spotify",
        "gnome-terminal-server": "GNOME Terminal",
        "nautilus": "Files (Nautilus)",
        "sublime_text": "Sublime Text",
        "thunderbird": "Thunderbird",
        "vlc": "VLC Media Player",
    }

    found_apps = []
    for proc in psutil.process_iter(['name', 'username']):
        try:
            if proc.info['username'] == current_user:
                name = proc.info['name'].lower()
                for app_key, app_name in common_apps.items():
                    if app_key in name and app_name not in found_apps:
                        found_apps.append(app_name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if found_apps:
        return ", ".join(found_apps)
    return "Tidak ada aplikasi GUI umum yang terdeteksi."

def _get_active_window_linux() -> str:
    """Get active window title on Linux using xprop or xdotool (handles missing executables)."""
    # Method 1: Try xdotool if installed
    if shutil.which("xdotool"):
        try:
            res = subprocess.run(["xdotool", "getactivewindow", "getwindowname"], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                title = res.stdout.strip()
                if "not found" not in title.lower():
                    return title
        except Exception as e:
            logger.debug(f"xdotool active window check failed: {e}")
        
    # Method 2: Try xprop (failsafe for X11)
    if shutil.which("xprop") and shutil.which("cut"):
        try:
            # Get active window id
            res_id = subprocess.run(
                "xprop -root 32x '\t$0' _NET_ACTIVE_WINDOW | cut -f 2",
                shell=True, capture_output=True, text=True
            )
            if res_id.returncode == 0:
                win_id = res_id.stdout.strip()
                if win_id and win_id != "0x0":
                    # Get window title by id
                    res_title = subprocess.run(
                        f"xprop -id {win_id} _NET_WM_NAME | cut -d '\"' -f 2",
                        shell=True, capture_output=True, text=True
                    )
                    title = res_title.stdout.strip()
                    if res_title.returncode == 0 and title and "not found" not in title.lower() and "_net_wm_name" not in title.lower():
                        return title
                        
                    # Try WM_NAME
                    res_title = subprocess.run(
                        f"xprop -id {win_id} WM_NAME | cut -d '\"' -f 2",
                        shell=True, capture_output=True, text=True
                    )
                    title = res_title.stdout.strip()
                    if res_title.returncode == 0 and title and "not found" not in title.lower() and "wm_name" not in title.lower():
                        return title
                        
                    # Try WM_CLASS
                    res_title = subprocess.run(
                        f"xprop -id {win_id} WM_CLASS | cut -d '\"' -f 2",
                        shell=True, capture_output=True, text=True
                    )
                    title = res_title.stdout.strip()
                    if res_title.returncode == 0 and title and "not found" not in title.lower() and "wm_class" not in title.lower():
                        return title
        except Exception as e:
            logger.debug(f"xprop active window check failed: {e}")
            
    # Check if we are on Wayland
    import os
    if os.environ.get("XDG_SESSION_TYPE") == "wayland":
        gui_apps = _get_active_gui_apps()
        return f"Wayland Session (Window title diisolasi untuk keamanan). Aplikasi aktif terdeteksi: {gui_apps}"
                
    # If both tools are missing
    return "Unknown (Instal 'xdotool' atau 'x11-utils' untuk mendeteksi nama jendela aktif di Linux)"

def _get_active_window_macos() -> str:
    """Get active window title on macOS using AppleScript."""
    cmd = """osascript -e 'tell application "System Events"
        set frontmostProcess to first process whose frontmost is true
        set windowName to name of first window of frontmostProcess
        return windowName
    end tell'"""
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()
        
    # Fallback to process name if window title fails
    cmd_proc = "osascript -e 'tell application \"System Events\" to get name of first process whose frontmost is true'"
    res_proc = subprocess.run(cmd_proc, shell=True, capture_output=True, text=True)
    if res_proc.returncode == 0 and res_proc.stdout.strip():
        return f"App: {res_proc.stdout.strip()}"
        
    return "Unknown macOS window"
