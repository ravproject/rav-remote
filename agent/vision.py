import os
import io
import time
import subprocess
import numpy as np
from PIL import Image
from loguru import logger

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SS_PORTAL_SCRIPT = os.path.join(SCRIPT_DIR, "ss_portal.py")

_cv2 = None
def _get_cv2():
    global _cv2
    if _cv2 is None:
        try:
            import cv2
            _cv2 = cv2
        except ImportError:
            pass
    return _cv2

def _capture_screen() -> bytes:
    if os.path.exists(SS_PORTAL_SCRIPT):
        try:
            result = subprocess.run(
                [SS_PORTAL_SCRIPT], capture_output=True, timeout=20,
                env={**os.environ}
            )
            if result.returncode == 0 and len(result.stdout) > 100:
                return result.stdout
        except Exception as e:
            logger.warning(f"Portal screenshot failed: {e}")
    try:
        import pyautogui
        img = pyautogui.screenshot()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        logger.warning(f"pyautogui screenshot failed: {e}")
    return None

def find_image(template_path: str, confidence: float = 0.8) -> list[dict]:
    cv2 = _get_cv2()
    if not cv2:
        return None

    screen_bytes = _capture_screen()
    if not screen_bytes:
        return None

    if not os.path.exists(template_path):
        logger.error(f"Template not found: {template_path}")
        return None

    try:
        screen_arr = np.frombuffer(screen_bytes, np.uint8)
        screen = cv2.imdecode(screen_arr, cv2.IMREAD_COLOR)
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)

        if screen is None or template is None:
            return None

        h, w = template.shape[:2]
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= confidence)
        matches = []

        screen_h, screen_w = screen.shape[:2]
        for pt in zip(*locations[::-1]):
            cx = int(pt[0] + w / 2)
            cy = int(pt[1] + h / 2)
            if 0 <= cx <= screen_w and 0 <= cy <= screen_h:
                matches.append({"x": cx, "y": cy, "width": w, "height": h})

        if matches:
            unique = []
            seen = set()
            for m in matches:
                key = (m["x"] // 10, m["y"] // 10)
                if key not in seen:
                    seen.add(key)
                    unique.append(m)
            return unique

        return []
    except Exception as e:
        logger.error(f"Image recognition failed: {e}")
        return None

def wait_for_image(template_path: str, timeout: float = 10, confidence: float = 0.8) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        matches = find_image(template_path, confidence)
        if matches:
            return matches[0]
        time.sleep(0.5)
    return None

def click_image(template_path: str, confidence: float = 0.8) -> str:
    matches = find_image(template_path, confidence)
    if not matches:
        return None
    target = matches[0]
    from agent.input_simulator import simulate_click
    return simulate_click(target["x"], target["y"])
