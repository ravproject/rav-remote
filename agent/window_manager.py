"""
Window Manager — arrange, snap, minimize all, close all windows.
"""
import subprocess
import shutil
from loguru import logger

def arrange_windows(layout: str = "cascade") -> str:
    has_wmctrl = shutil.which("wmctrl")
    has_xdotool = shutil.which("xdotool")
    if not has_wmctrl and not has_xdotool:
        return "wmctrl atau xdotool diperlukan. Install: sudo apt install wmctrl"
    try:
        if has_wmctrl:
            res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=5)
            raw = res.stdout.strip()
            windows = [line for line in raw.split("\n") if line]
        else:
            res = subprocess.run(["xdotool", "search", "--name", ""], capture_output=True, text=True, timeout=5)
            raw = res.stdout.strip()
            windows = [f"{wid} _ " for wid in raw.split("\n") if wid.strip()]
        if len(windows) < 2:
            return "Hanya 1 jendela terbuka."
        screen_w, screen_h = 1920, 1080
        if layout == "cascade":
            x, y = 0, 0
            for w in windows:
                wid = w.split()[0]
                if has_wmctrl:
                    subprocess.run(["wmctrl", "-i", "-r", wid, "-e", f"0,{x},{y},800,600"],
                                   capture_output=True, timeout=3)
                else:
                    subprocess.run(["xdotool", "windowmove", wid, str(x), str(y)], capture_output=True, timeout=5)
                    subprocess.run(["xdotool", "windowsize", wid, "800", "600"], capture_output=True, timeout=5)
                x += 30
                y += 30
            return f"Jendela di-cascade ({len(windows)} window)."
        elif layout == "tile":
            import math
            cols = math.ceil(math.sqrt(len(windows)))
            w_w = screen_w // cols
            w_h = screen_h // math.ceil(len(windows) / cols)
            for i, w in enumerate(windows):
                wid = w.split()[0]
                x = (i % cols) * w_w
                y = (i // cols) * w_h
                if has_wmctrl:
                    subprocess.run(["wmctrl", "-i", "-r", wid, "-e", f"0,{x},{y},{w_w},{w_h}"],
                                   capture_output=True, timeout=3)
                else:
                    subprocess.run(["xdotool", "windowmove", wid, str(x), str(y)], capture_output=True, timeout=5)
                    subprocess.run(["xdotool", "windowsize", wid, str(w_w), str(w_h)], capture_output=True, timeout=5)
            return f"Jendela di-tile ({len(windows)} window)."
        return f"Layout tidak dikenal: {layout}"
    except Exception as e:
        return f"Gagal: {e}"

def snap_window(position: str = "left") -> str:
    if not shutil.which("xdotool"):
        return "xdotool diperlukan."
    key_map = {"left": "ctrl+super+Left", "right": "ctrl+super+Right",
               "top": "ctrl+super+Up", "bottom": "ctrl+super+Down"}
    key = key_map.get(position)
    if not key:
        return "Posisi tidak dikenal. Gunakan: left, right, top, bottom"
    try:
        subprocess.run(["xdotool", "key", key], capture_output=True, timeout=5)
        return f"Jendela di-snap ke {position}."
    except Exception as e:
        return f"Gagal snap: {e}"

def minimize_all() -> str:
    if shutil.which("xdotool"):
        try:
            subprocess.run(["xdotool", "key", "super+d"], capture_output=True, timeout=5)
            return "Semua jendela diminimalkan."
        except Exception:
            pass
    if shutil.which("wmctrl"):
        try:
            res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=5)
            for line in res.stdout.strip().split("\n"):
                if line:
                    wid = line.split()[0]
                    subprocess.run(["wmctrl", "-i", "-r", wid, "-b", "add,hidden"],
                                   capture_output=True, timeout=3)
            return "Semua jendela diminimalkan."
        except Exception:
            pass
    return "Minimize all membutuhkan xdotool atau wmctrl."

def close_all() -> str:
    if shutil.which("wmctrl"):
        try:
            res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=5)
            count = 0
            for line in res.stdout.strip().split("\n"):
                if line:
                    wid = line.split()[0]
                    subprocess.run(["wmctrl", "-i", "-c", wid], capture_output=True, timeout=3)
                    count += 1
            return f"{count} jendela ditutup."
        except Exception:
            pass
    return "Close all membutuhkan wmctrl."
