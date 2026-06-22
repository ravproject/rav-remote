"""
Window Manager — arrange, snap, minimize all, close all windows.
"""
import subprocess
import shutil
from loguru import logger

def arrange_windows(layout: str = "cascade") -> str:
    if not shutil.which("wmctrl") and not shutil.which("xdotool"):
        return "wmctrl atau xdotool diperlukan."
    try:
        res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=5)
        windows = [line for line in res.stdout.strip().split("\n") if line]
        if len(windows) < 2:
            return "Hanya 1 jendela terbuka."
        if layout == "cascade":
            x, y = 0, 0
            for w in windows:
                wid = w.split()[0]
                subprocess.run(["wmctrl", "-i", "-r", wid, "-e", f"0,{x},{y},800,600"],
                               capture_output=True, timeout=3)
                x += 30
                y += 30
            return f"Jendela di-cascade ({len(windows)} window)."
        elif layout == "tile":
            import math
            cols = math.ceil(math.sqrt(len(windows)))
            w_w, w_h = 1920 // cols, 1080 // math.ceil(len(windows) / cols)
            for i, w in enumerate(windows):
                wid = w.split()[0]
                x = (i % cols) * w_w
                y = (i // cols) * w_h
                subprocess.run(["wmctrl", "-i", "-r", wid, "-e", f"0,{x},{y},{w_w},{w_h}"],
                               capture_output=True, timeout=3)
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
        subprocess.run(["xdotool", "key", key], capture_output=True, timeout=3)
        return f"Jendela di-snap ke {position}."
    except Exception as e:
        return f"Gagal snap: {e}"

def minimize_all() -> str:
    if shutil.which("xdotool"):
        try:
            subprocess.run(["xdotool", "key", "super+d"], capture_output=True, timeout=3)
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
