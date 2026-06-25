import subprocess
import shutil
import webbrowser
from loguru import logger

from agent.platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS, has_tool
from agent.input_simulator import simulate_press


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
    key = "pagedown" if direction == "down" else "pageup"
    return simulate_press(key)


def browser_refresh() -> str:
    return simulate_press("f5")


def browser_close(tab_index: int = None) -> str:
    if IS_LINUX and has_tool("xdotool"):
        try:
            if tab_index:
                subprocess.run(["xdotool", "key", f"ctrl+{tab_index}"], capture_output=True, timeout=3)
                subprocess.run(["xdotool", "key", "ctrl+w"], capture_output=True, timeout=3)
                return f"Tab {tab_index} ditutup."
            subprocess.run(["xdotool", "key", "ctrl+w"], capture_output=True, timeout=3)
            return "Tab aktif ditutup."
        except Exception as e:
            return f"Gagal menutup tab: {e}"
    if IS_MACOS:
        cmd = 'osascript -e \'tell application "System Events" to keystroke "w" using command down\''
        try:
            subprocess.run(cmd, shell=True, capture_output=True, timeout=3)
            return "Tab ditutup."
        except Exception as e:
            return f"Gagal: {e}"
    if IS_WINDOWS:
        return simulate_press("ctrl+w")
    return "Belum didukung."
