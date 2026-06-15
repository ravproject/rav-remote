import os
import subprocess
import tempfile
import platform
from loguru import logger

def take_screenshot() -> bytes | str:
    """
    Enhanced screenshot taker for Cross-Platform (Windows, Linux, macOS).
    Automatically detects OS and uses the most silent/effective method.
    """
    current_os = platform.system()
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    try:
        if current_os == "Linux":
            # Linux logic (optimized for Wayland/GNOME)
            # 1. Super Silent Mode: Disable animations
            subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "enable-animations", "false"], capture_output=True)
            
            # 2. Try flameshot (Works on Wayland)
            try:
                subprocess.run(["flameshot", "config", "--notifications", "false"], capture_output=True)
                subprocess.run(["flameshot", "full", "-p", temp_path], check=True, capture_output=True, timeout=10)
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    with open(temp_path, "rb") as f: return f.read()
            except: pass

            # 3. Try DBus fallback
            try:
                cmd = ["dbus-send", "--session", "--print-reply", "--dest=org.gnome.Shell.Screenshot", "/org/gnome/Shell/Screenshot", "org.gnome.Shell.Screenshot.Screenshot", "boolean:false", "boolean:false", f"string:{temp_path}"]
                subprocess.run(cmd, capture_output=True, timeout=5)
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    with open(temp_path, "rb") as f: return f.read()
            except: pass

        elif current_os == "Windows":
            # Windows logic: MSS is very silent and reliable
            try:
                import mss
                import mss.tools
                with mss.mss() as sct:
                    # Capture primary monitor
                    monitor = sct.monitors[1]
                    sct_img = sct.grab(monitor)
                    return mss.tools.to_png(sct_img.rgb, sct_img.size)
            except Exception as e:
                logger.debug(f"MSS Windows failed: {e}")

        elif current_os == "Darwin": # macOS
            try:
                subprocess.run(["screencapture", "-x", temp_path], check=True)
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    with open(temp_path, "rb") as f: return f.read()
            except Exception as e:
                logger.debug(f"macOS screencapture failed: {e}")

        # Universal Fallback: MSS (Multi-platform)
        try:
            import mss
            import mss.tools
            with mss.mss() as sct:
                img = sct.grab(sct.monitors[0])
                return mss.tools.to_png(img.rgb, img.size)
        except: pass

        return "❌ Gagal mengambil screenshot pada platform ini."

    finally:
        # Restore Linux settings if needed
        if current_os == "Linux":
            subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "enable-animations", "true"], capture_output=True)
        
        if os.path.exists(temp_path):
            try: os.remove(temp_path)
            except: pass

if __name__ == "__main__":
    res = take_screenshot()
    if isinstance(res, bytes):
        print(f"Success! Captured {len(res)} bytes.")
    else:
        print(res)
