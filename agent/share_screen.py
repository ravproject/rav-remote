import subprocess
import shutil
from pathlib import Path
from datetime import datetime

from agent.platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS, has_tool

SCREENSHOT_DIR = Path.home() / "Pictures"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def take_screenshot(fullscreen: bool = True) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = SCREENSHOT_DIR / f"screenshot_{ts}.png"

    if IS_LINUX:
        try:
            import mss
            import mss.tools
            with mss.mss() as sct:
                if fullscreen:
                    monitor = sct.monitors[1]
                    sct_img = sct.grab(monitor)
                else:
                    mon = sct.monitors[0]
                    sct_img = sct.grab(mon)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=str(filename))
            if filename.exists():
                return f"Screenshot: {filename} ({(filename.stat().st_size / 1024):.0f} KB)"
        except Exception:
            pass
        if has_tool("gnome-screenshot"):
            cmd = ["gnome-screenshot", "-f", str(filename)]
            if not fullscreen:
                cmd.append("-a")
            try:
                subprocess.run(cmd, capture_output=True, timeout=5)
            except Exception:
                pass
        if not filename.exists():
            if has_tool("scrot"):
                try:
                    subprocess.run(["scrot", str(filename)], capture_output=True, timeout=5)
                except Exception:
                    pass
        if not filename.exists():
            if has_tool("import"):
                cmd = ["import", "-window", "root", str(filename)] if fullscreen else ["import", str(filename)]
                try:
                    subprocess.run(cmd, capture_output=True, timeout=5)
                except Exception:
                    pass
        if not filename.exists():
            return "Install gnome-screenshot, scrot, atau imagemagick."
    elif IS_MACOS:
        cmd = ["screencapture"]
        if not fullscreen:
            cmd.append("-i")
        cmd.append(str(filename))
        subprocess.run(cmd, capture_output=True, timeout=5)
    elif IS_WINDOWS:
        try:
            import mss
            with mss.mss() as sct:
                sct.shot(output=str(filename))
        except ImportError:
            return "Install mss: pip install mss"
    else:
        return "OS tidak didukung."

    if filename.exists():
        return f"Screenshot: {filename} ({(filename.stat().st_size / 1024):.0f} KB)"
    return "Gagal mengambil screenshot."


def share_screenshot(path: str = None) -> str:
    if path and not Path(path).exists():
        return f"File '{path}' tidak ditemukan."
    result = take_screenshot()
    if "Screenshot" in result:
        return f"{result}\nScreenshot siap dibagikan."
    return result
