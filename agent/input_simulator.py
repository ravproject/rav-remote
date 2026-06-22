"""
Input Simulator Modul — Mensimulasikan klik mouse, mengetik teks, dan menekan tombol secara cross-platform.
"""
import subprocess
import platform
import shutil
from loguru import logger

# Lazy import pyautogui to prevent failure on headless Linux systems
pyautogui = None
try:
    import pyautogui
except ImportError:
    pass

def simulate_click(x: int, y: int) -> str:
    """Simulasi klik mouse kiri pada koordinat (x, y)."""
    current_os = platform.system()
    
    # Try pyautogui first if available
    global pyautogui
    if pyautogui is not None:
        try:
            pyautogui.click(x, y)
            return f"🖱️ Berhasil klik mouse pada koordinat ({x}, {y}) menggunakan pyautogui."
        except Exception as e:
            logger.warning(f"PyAutoGUI click failed: {e}. Trying system utilities...")

    if current_os == "Linux":
        # Try xdotool (standard for X11)
        if shutil.which("xdotool"):
            try:
                res = subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"], capture_output=True)
                if res.returncode == 0:
                    return f"🖱️ Berhasil klik mouse pada ({x}, {y}) menggunakan xdotool."
            except Exception as e:
                logger.debug(f"xdotool click execution failed: {e}")
            
        # Fallback to ydotool (Wayland/Daemon)
        if shutil.which("ydotool"):
            try:
                res_ydo = subprocess.run(["ydotool", "mousemove", "-a", str(x), str(y)], capture_output=True)
                if res_ydo.returncode == 0:
                    subprocess.run(["ydotool", "click", "0x110"], capture_output=True) # 0x110 is BTN_LEFT
                    return f"🖱️ Berhasil klik mouse pada ({x}, {y}) menggunakan ydotool."
            except Exception as e:
                logger.debug(f"ydotool click execution failed: {e}")
            
        return "❌ Gagal simulasi klik. Silakan instal 'xdotool' (untuk X11) atau 'ydotool' (untuk Wayland)."
        
    elif current_os == "Windows":
        return "⚠️ Modul pyautogui tidak terinstall. Jalankan `pip install pyautogui` untuk Windows."
    elif current_os == "Darwin":
        # macOS apple script fallback
        cmd = f"osascript -e 'tell application \"System Events\" to click at {{{x}, {y}}}'"
        res = subprocess.run(cmd, shell=True, capture_output=True)
        if res.returncode == 0:
            return f"🖱️ Berhasil klik mouse pada ({x}, {y}) menggunakan AppleScript."
        return "⚠️ Modul pyautogui tidak terinstall atau AppleScript ditolak."
        
    return f"❌ Fitur klik belum didukung di OS {current_os} tanpa pyautogui."

def simulate_type(text: str) -> str:
    """Simulasi mengetik teks."""
    current_os = platform.system()
    
    global pyautogui
    if pyautogui is not None:
        try:
            pyautogui.write(text, interval=0.01)
            return f"⌨️ Berhasil mengetik teks: '{text}' menggunakan pyautogui."
        except Exception as e:
            logger.warning(f"PyAutoGUI type failed: {e}. Trying system utilities...")

    if current_os == "Linux":
        # Use xdotool type
        if shutil.which("xdotool"):
            try:
                res = subprocess.run(["xdotool", "type", text], capture_output=True)
                if res.returncode == 0:
                    return f"⌨️ Berhasil mengetik teks menggunakan xdotool."
            except Exception as e:
                logger.debug(f"xdotool type execution failed: {e}")
            
        # Fallback to ydotool type
        if shutil.which("ydotool"):
            try:
                res_ydo = subprocess.run(["ydotool", "type", text], capture_output=True)
                if res_ydo.returncode == 0:
                    return f"⌨️ Berhasil mengetik teks menggunakan ydotool."
            except Exception as e:
                logger.debug(f"ydotool type execution failed: {e}")
            
        return "❌ Gagal simulasi ketik. Silakan instal 'xdotool' atau 'ydotool'."
        
    elif current_os == "Windows":
        return "⚠️ Modul pyautogui tidak terinstall. Jalankan `pip install pyautogui` untuk Windows."
    elif current_os == "Darwin":
        # AppleScript keystroke
        escaped_text = text.replace('"', '\\"')
        cmd = f'osascript -e \'tell application "System Events" to keystroke "{escaped_text}"\''
        res = subprocess.run(cmd, shell=True, capture_output=True)
        if res.returncode == 0:
            return f"⌨️ Berhasil mengetik teks menggunakan AppleScript."
        return "⚠️ Modul pyautogui tidak terinstall atau AppleScript ditolak."
        
    return f"❌ Fitur ketik belum didukung di OS {current_os} tanpa pyautogui."

def simulate_press(key: str) -> str:
    """Simulasi menekan sebuah tombol keyboard (seperti 'enter', 'esc', 'space')."""
    current_os = platform.system()
    
    global pyautogui
    if pyautogui is not None:
        try:
            pyautogui.press(key)
            return f"⌨️ Berhasil menekan tombol '{key}' menggunakan pyautogui."
        except Exception as e:
            logger.warning(f"PyAutoGUI press failed: {e}. Trying system utilities...")

    if current_os == "Linux":
        # Map some common keys to xdotool keys
        if shutil.which("xdotool"):
            try:
                res = subprocess.run(["xdotool", "key", key], capture_output=True)
                if res.returncode == 0:
                    return f"⌨️ Berhasil menekan tombol '{key}' menggunakan xdotool."
            except Exception as e:
                logger.debug(f"xdotool press execution failed: {e}")
            
        return f"❌ Gagal menekan tombol '{key}'. Silakan instal 'xdotool'."
        
    elif current_os == "Windows":
        return "⚠️ Modul pyautogui tidak terinstall. Jalankan `pip install pyautogui` untuk Windows."
    elif current_os == "Darwin":
        # AppleScript key code / keystroke
        cmd = f'osascript -e \'tell application "System Events" to keystroke "{key}"\''
        if key.lower() == "enter":
            cmd = 'osascript -e \'tell application "System Events" to key code 36\''
        elif key.lower() == "space":
            cmd = 'osascript -e \'tell application "System Events" to key code 49\''
            
        res = subprocess.run(cmd, shell=True, capture_output=True)
        if res.returncode == 0:
            return f"⌨️ Berhasil menekan tombol '{key}' menggunakan AppleScript."
        return "⚠️ Modul pyautogui tidak terinstall atau AppleScript ditolak."
        
    return f"❌ Fitur tekan tombol belum didukung di OS {current_os} tanpa pyautogui."
