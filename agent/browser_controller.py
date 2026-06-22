"""
Browser Controller — control Chrome/Chromium browser via D-Bus and xdotool.
"""
import subprocess
import shutil
import webbrowser
from loguru import logger

def browser_new(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return f"Browser membuka: {url}"
    except Exception as e:
        return f"Gagal membuka browser: {e}"

def browser_search(query: str) -> str:
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    return browser_new(url)

def browser_scroll(direction: str = "down") -> str:
    key = "Page_Down" if direction == "down" else "Page_Up"
    if shutil.which("xdotool"):
        try:
            subprocess.run(["xdotool", "key", key], capture_output=True, timeout=3)
            return f"Scrolling {direction}."
        except Exception as e:
            return f"Gagal scroll: {e}"
    return "xdotool tidak ditemukan."

def browser_refresh() -> str:
    if shutil.which("xdotool"):
        try:
            subprocess.run(["xdotool", "key", "F5"], capture_output=True, timeout=3)
            return "Browser di-refresh."
        except Exception as e:
            return f"Gagal refresh: {e}"
    return "xdotool tidak ditemukan."

def browser_close(tab_index: int = None) -> str:
    if shutil.which("xdotool"):
        try:
            if tab_index:
                subprocess.run(["xdotool", "key", f"ctrl+{tab_index}"], capture_output=True, timeout=3)
                subprocess.run(["xdotool", "key", "ctrl+w"], capture_output=True, timeout=3)
                return f"Tab {tab_index} ditutup."
            subprocess.run(["xdotool", "key", "ctrl+w"], capture_output=True, timeout=3)
            return "Tab aktif ditutup."
        except Exception as e:
            return f"Gagal menutup tab: {e}"
    return "xdotool tidak ditemukan."
