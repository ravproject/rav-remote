"""
Module for taking screenshots.
"""
import mss
import mss.tools
from loguru import logger

def take_screenshot() -> bytes:
    """
    Take a screenshot and return as PNG bytes.
    """
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Main monitor
        screenshot = sct.grab(monitor)
        png_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)

    logger.info("Screenshot captured")
    return png_bytes
