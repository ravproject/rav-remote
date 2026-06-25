import os
import subprocess
import tempfile
import platform
import io
import json
import re
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SS_PORTAL_SCRIPT = os.path.join(SCRIPT_DIR, "ss_portal.py")

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

def _get_monitor_layout() -> list[dict]:
    """Detect monitor layout. Returns list of {name, x, y, width, height}."""
    # Try xrandr (via XWayland, works on most setups)
    try:
        out = subprocess.run(
            ["xrandr", "--query"], capture_output=True, text=True, timeout=5
        ).stdout
        monitors = []
        for line in out.splitlines():
            m = re.match(r'^(\S+) connected (?:primary )?(\d+)x(\d+)\+(\d+)\+(\d+)', line)
            if m:
                monitors.append({
                    "name": m.group(1),
                    "x": int(m.group(4)),
                    "y": int(m.group(5)),
                    "width": int(m.group(2)),
                    "height": int(m.group(3)),
                })
        if monitors:
            return monitors
    except Exception:
        pass

    # Fallback: assume single 1920x1080
    return [{"name": "default", "x": 0, "y": 0, "width": 1920, "height": 1080}]


def _crop_monitor(img_bytes: bytes, monitor_index: int) -> bytes | None:
    """Crop a full screenshot to the specified monitor."""
    monitors = _get_monitor_layout()
    if not monitors or monitor_index < 0 or monitor_index >= len(monitors):
        return None
    m = monitors[monitor_index]
    img = Image.open(io.BytesIO(img_bytes))
    cropped = img.crop((m["x"], m["y"], m["x"] + m["width"], m["y"] + m["height"]))
    buf = io.BytesIO()
    cropped.save(buf, format="PNG")
    return buf.getvalue()


def _screenshot_linux(temp_path: str, monitor: int = -1) -> bytes | None:
    """Attempt screenshot on Linux using various methods (Wayland & X11)."""
    env = os.environ.copy()
    env["DISPLAY"] = os.environ.get("DISPLAY", ":0")
    raw_bytes = None

    # 1. flameshot (works on X11/Wayland via XWayland)
    if not raw_bytes:
        try:
            subprocess.run(
                ["flameshot", "config", "--notifications", "false"],
                capture_output=True, timeout=5, env=env
            )
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            subprocess.run(
                ["flameshot", "full", "-p", temp_path],
                capture_output=True, timeout=15, env=env
            )
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                with open(temp_path, "rb") as f:
                    raw_bytes = f.read()
                logger.info("Screenshot via flameshot")
        except Exception as e:
            logger.warning(f"flameshot failed: {e}")

    # 3. Gdk.pixbuf (via X11 XWayland)
    if not raw_bytes:
        try:
            import gi
            gi.require_version("Gdk", "3.0")
            from gi.repository import Gdk
            win = Gdk.get_default_root_window()
            if win:
                pb = Gdk.pixbuf_get_from_window(win, 0, 0, win.get_width(), win.get_height())
                if pb:
                    raw_bytes = pb.save_to_bufferv("png", [], [])[0]
                    logger.info("Screenshot via Gdk.pixbuf")
        except Exception as e:
            logger.debug(f"Gdk screenshot failed: {e}")

    # 4. MSS (X11 fallback)
    if not raw_bytes:
        try:
            import mss
            import mss.tools
            with mss.mss() as sct:
                img = sct.grab(sct.monitors[0])
                raw_bytes = mss.tools.to_png(img.rgb, img.size)
                logger.info("Screenshot via MSS (fallback)")
        except Exception as e:
            logger.warning(f"MSS fallback failed: {e}")

    # 5. xdg-desktop-portal (last resort, may show dialog)
    if not raw_bytes and os.path.exists(SS_PORTAL_SCRIPT):
        try:
            result = subprocess.run(
                [SS_PORTAL_SCRIPT],
                capture_output=True, timeout=20,
                env={**os.environ}
            )
            if result.returncode == 0 and len(result.stdout) > 100:
                raw_bytes = result.stdout
                logger.info("Screenshot via xdg-desktop-portal")
        except Exception as e:
            logger.warning(f"Portal screenshot failed: {e}")

    # Crop to specific monitor if requested
    if raw_bytes and monitor >= 0:
        cropped = _crop_monitor(raw_bytes, monitor)
        if cropped:
            logger.info(f"Cropped to monitor {monitor}")
            return cropped

    return raw_bytes


def take_screenshot(grid: bool = False, monitor: int = -1) -> bytes | str:
    """
    Enhanced screenshot taker for Cross-Platform (Windows, Linux, macOS).
    Automatically detects OS and uses the most silent/effective method.
    
    Args:
        grid: Draw coordinate grid overlay.
        monitor: Monitor index (-1 = all monitors, 0 = first, 1 = second, etc.).
    """
    current_os = platform.system()

    raw_bytes = None
    temp_path = None

    if current_os == "Linux":
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temp_path = tmp.name
        tmp.close()
        raw_bytes = _screenshot_linux(temp_path, monitor)

    elif current_os == "Windows":
        try:
            import mss
            import mss.tools
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                raw_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
        except Exception as e:
            logger.debug(f"MSS Windows failed: {e}")

    elif current_os == "Darwin":
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temp_path = tmp.name
        tmp.close()
        try:
            subprocess.run(["screencapture", "-x", temp_path], check=True, timeout=15)
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                with open(temp_path, "rb") as f:
                    raw_bytes = f.read()
        except Exception as e:
            logger.debug(f"macOS screencapture failed: {e}")

    if temp_path and os.path.exists(temp_path):
        try:
            os.unlink(temp_path)
        except Exception:
            pass

    if raw_bytes:
        if grid:
            return draw_grid_on_screenshot(raw_bytes)
        return raw_bytes

    return "❌ Gagal mengambil screenshot pada platform ini."

if __name__ == "__main__":
    res = take_screenshot()
    if isinstance(res, bytes):
        print(f"Success! Captured {len(res)} bytes.")
    else:
        print(res)
