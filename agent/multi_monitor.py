"""
Multi Monitor — list, switch, arrange displays.
"""
import subprocess
import shutil
from loguru import logger

def list_monitors() -> str:
    if shutil.which("xrandr"):
        try:
            res = subprocess.run(["xrandr", "--listmonitors"], capture_output=True, text=True, timeout=5)
            return f"🖥️ Monitor:\n{res.stdout.strip()}"
        except Exception as e:
            return f"Gagal: {e}"
    return "xrandr tidak ditemukan."

def switch_monitor(target: str = "auto") -> str:
    if not shutil.which("xrandr"):
        return "xrandr tidak ditemukan."
    try:
        res = subprocess.run(["xrandr"], capture_output=True, text=True, timeout=5)
        lines = res.stdout.split("\n")
        connected = []
        for line in lines:
            if " connected " in line:
                connected.append(line.split()[0])
        if not connected:
            return "Tidak ada monitor terdeteksi."
        if target == "auto":
            return f"Monitor terdeteksi: {', '.join(connected)}. Gunakan: !multi monitor switch <nama>"
        if target in connected:
            subprocess.run(["xrandr", "--output", target, "--auto"], capture_output=True, timeout=5)
            return f"Monitor {target} diaktifkan."
        return f"Monitor '{target}' tidak ditemukan. Tersedia: {', '.join(connected)}"
    except Exception as e:
        return f"Gagal: {e}"

def arrange_monitors(layout: str = "grid") -> str:
    if not shutil.which("xrandr"):
        return "xrandr tidak ditemukan."
    try:
        res = subprocess.run(["xrandr"], capture_output=True, text=True, timeout=5)
        lines = res.stdout.split("\n")
        monitors = [line.split()[0] for line in lines if " connected " in line]
        if len(monitors) < 2:
            return f"Hanya 1 monitor terdeteksi. Tidak perlu diatur."
        if layout == "grid":
            import math
            cols = math.ceil(math.sqrt(len(monitors)))
            for i, m in enumerate(monitors):
                x = (i % cols) * 1920
                y = (i // cols) * 1080
                subprocess.run(["xrandr", "--output", m, "--pos", f"{x}x{y}"], capture_output=True, timeout=5)
            return f"Monitor diatur grid {cols}x{math.ceil(len(monitors)/cols)}."
        elif layout == "horizontal":
            x = 0
            for m in monitors:
                subprocess.run(["xrandr", "--output", m, "--pos", f"{x}x0"], capture_output=True, timeout=5)
                x += 1920
            return f"Monitor diatur horizontal."
        elif layout == "mirror":
            primary = monitors[0]
            for m in monitors[1:]:
                subprocess.run(["xrandr", "--output", m, "--same-as", primary], capture_output=True, timeout=5)
            return f"Monitor di-mirror ke {primary}."
        return f"Layout tidak dikenal: {layout}. Gunakan: grid, horizontal, mirror"
    except Exception as e:
        return f"Gagal: {e}"
