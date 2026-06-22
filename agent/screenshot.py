import os
import subprocess
import tempfile
import platform
import io
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

def draw_grid_on_screenshot(img_bytes: bytes) -> bytes:
    """Draw a coordinate grid with labels on the screenshot bytes."""
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        draw = ImageDraw.Draw(img, "RGBA")
        width, height = img.size
        
        # Grid spacing: 100 pixels
        spacing = 100
        
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
            
        # Draw vertical lines and labels
        for x in range(0, width, spacing):
            is_major = (x % 500 == 0)
            color = (255, 0, 0, 100) if is_major else (128, 128, 128, 50)
            draw.line([(x, 0), (x, height)], fill=color, width=2 if is_major else 1)
            
            if x > 0:
                text = str(x)
                if font:
                    try:
                        left, top, right, bottom = draw.textbbox((x + 2, 5), text, font=font)
                        draw.rectangle([left - 2, top - 1, right + 2, bottom + 1], fill=(0, 0, 0, 160))
                    except AttributeError:
                        pass
                draw.text((x + 2, 5), text, fill=(255, 255, 255) if is_major else (220, 220, 220), font=font)

        # Draw horizontal lines and labels
        for y in range(0, height, spacing):
            is_major = (y % 500 == 0)
            color = (255, 0, 0, 100) if is_major else (128, 128, 128, 50)
            draw.line([(0, y), (width, y)], fill=color, width=2 if is_major else 1)
            
            if y > 0:
                text = str(y)
                if font:
                    try:
                        left, top, right, bottom = draw.textbbox((5, y + 2), text, font=font)
                        draw.rectangle([left - 2, top - 1, right + 2, bottom + 1], fill=(0, 0, 0, 160))
                    except AttributeError:
                        pass
                draw.text((5, y + 2), text, fill=(255, 255, 255) if is_major else (220, 220, 220), font=font)

        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()
    except Exception as e:
        logger.error(f"Failed to draw grid on screenshot: {e}")
        return img_bytes

def take_screenshot(grid: bool = False) -> bytes | str:
    """
    Enhanced screenshot taker for Cross-Platform (Windows, Linux, macOS).
    Automatically detects OS and uses the most silent/effective method.
    """
    current_os = platform.system()
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    raw_bytes = None

    try:
        if current_os == "Linux":
            # Linux logic (optimized for Wayland/GNOME)
            # 1. Super Silent Mode: Disable animations
            subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "enable-animations", "false"], capture_output=True)
            
            # 2. Try flameshot (Works on Wayland)
            try:
                subprocess.run(["flameshot", "config", "--notifications", "false"], capture_output=True)
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                subprocess.run(["flameshot", "full", "-p", temp_path], check=True, capture_output=True, timeout=10)
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    with open(temp_path, "rb") as f:
                        raw_bytes = f.read()
            except: pass

            # 3. Try DBus fallback
            if not raw_bytes:
                try:
                    cmd = ["dbus-send", "--session", "--print-reply", "--dest=org.gnome.Shell.Screenshot", "/org/gnome/Shell/Screenshot", "org.gnome.Shell.Screenshot.Screenshot", "boolean:false", "boolean:false", f"string:{temp_path}"]
                    subprocess.run(cmd, capture_output=True, timeout=5)
                    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                        with open(temp_path, "rb") as f:
                            raw_bytes = f.read()
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
                    raw_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
            except Exception as e:
                logger.debug(f"MSS Windows failed: {e}")

        elif current_os == "Darwin": # macOS
            try:
                subprocess.run(["screencapture", "-x", temp_path], check=True)
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    with open(temp_path, "rb") as f:
                        raw_bytes = f.read()
            except Exception as e:
                logger.debug(f"macOS screencapture failed: {e}")

        # Universal Fallback: MSS (Multi-platform)
        if not raw_bytes:
            try:
                import mss
                import mss.tools
                with mss.mss() as sct:
                    img = sct.grab(sct.monitors[0])
                    raw_bytes = mss.tools.to_png(img.rgb, img.size)
            except: pass

        if raw_bytes:
            if grid:
                return draw_grid_on_screenshot(raw_bytes)
            return raw_bytes

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
