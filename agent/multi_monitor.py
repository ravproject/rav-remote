import subprocess
import shutil
from loguru import logger

from agent.platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS, has_tool


def list_monitors() -> str:
    if IS_LINUX and has_tool("xrandr"):
        try:
            r = subprocess.run(["xrandr", "--listmonitors"], capture_output=True, text=True, timeout=5)
            return f"Monitor:\n{r.stdout.strip()}"
        except Exception as e:
            return f"Gagal: {e}"
    elif IS_MACOS:
        try:
            r = subprocess.run(["system_profiler", "SPDisplaysDataType"],
                               capture_output=True, text=True, timeout=10)
            lines = [l.strip() for l in r.stdout.split("\n") if "Resolution" in l or "Display" in l]
            return "Monitor:\n" + "\n".join(lines[:10]) if lines else "Gunakan system_profiler untuk detail."
        except Exception as e:
            return f"Gagal: {e}"
    elif IS_WINDOWS:
        try:
            import ctypes
            user32 = ctypes.windll.user32
            count = user32.GetSystemMetrics(80)  # SM_CMONITORS
            w = user32.GetSystemMetrics(0)
            h = user32.GetSystemMetrics(1)
            return f"Monitor: {count} detected, primary: {w}x{h}"
        except Exception as e:
            return f"Gagal: {e}"
    return "Fitur monitor belum didukung di OS ini."


def switch_monitor(target: str = "auto") -> str:
    if IS_LINUX and has_tool("xrandr"):
        try:
            r = subprocess.run(["xrandr"], capture_output=True, text=True, timeout=5)
            connected = [l.split()[0] for l in r.stdout.split("\n") if " connected " in l]
            if not connected:
                return "Tidak ada monitor terdeteksi."
            if target == "auto":
                return f"Monitor: {', '.join(connected)}. Gunakan: !multi monitor switch <nama>"
            if target in connected:
                subprocess.run(["xrandr", "--output", target, "--primary", "--auto"],
                               capture_output=True, timeout=5)
                others = [m for m in connected if m != target]
                for m in others:
                    subprocess.run(["xrandr", "--output", m, "--off"], capture_output=True, timeout=3)
                return f"Monitor '{target}' diaktifkan."
            return f"Monitor '{target}' tidak terdeteksi. Tersedia: {', '.join(connected)}"
        except Exception as e:
            return f"Gagal: {e}"
    elif IS_MACOS:
        try:
            subprocess.run(["osascript", "-e",
                           f'do shell script "open -a System\\ Settings" with administrator privileges'],
                           capture_output=True, timeout=5)
            return "Buka System Settings > Displays untuk atur monitor."
        except Exception:
            return "Atur monitor manual via System Settings."
    elif IS_WINDOWS:
        try:
            subprocess.run(["DisplaySwitch.exe", "/extend"], capture_output=True, timeout=5)
            return "Monitor mode: extend."
        except Exception:
            return "Gunakan Win+P untuk atur monitor."
    return "Fitur switch monitor belum didukung."
