import subprocess
import shutil
from pathlib import Path
from datetime import datetime

SCREENSHOT_DIR = Path.home() / "Pictures"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def take_screenshot(fullscreen: bool = True) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = SCREENSHOT_DIR / f"screenshot_{ts}.png"
    if shutil.which("gnome-screenshot"):
        cmd = ["gnome-screenshot", "-f", str(filename)]
        if not fullscreen:
            cmd.append("-a")
        subprocess.run(cmd, capture_output=True, timeout=5)
    elif shutil.which("scrot"):
        subprocess.run(["scrot", str(filename)], capture_output=True, timeout=5)
    elif shutil.which("import"):
        cmd = ["import", "-window", "root", str(filename)] if fullscreen else ["import", str(filename)]
        subprocess.run(cmd, capture_output=True, timeout=5)
    else:
        return "Tidak ada tool screenshot (install gnome-screenshot, scrot, atau imagemagick)."
    if filename.exists():
        return f"📸 Screenshot: {filename} ({(filename.stat().st_size / 1024):.0f} KB)"
    return "Gagal mengambil screenshot."

def share_screenshot(path: str = None) -> str:
    if path and not Path(path).exists():
        return f"File '{path}' tidak ditemukan."
    result = take_screenshot()
    if "Screenshot" in result:
        return f"{result}\n📤 Screenshot siap dibagikan."
    return result
