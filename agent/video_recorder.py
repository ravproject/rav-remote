"""
Module for recording live screen stream.
"""
import mss
import imageio
import tempfile
import time
import os
from loguru import logger
from typing import Optional

def record_video(duration: int = 5) -> Optional[bytes]:
    """
    Record screen for `duration` seconds and return MP4 bytes.
    Uses imageio which automatically fetches ffmpeg binary if needed.
    """
    try:
        if "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = ":0"
            
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_path = temp_file.name
        temp_file.close()

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            fps = 10 # Lower FPS for smaller file size
            
            # Using imageio to write mp4
            writer = imageio.get_writer(temp_path, fps=fps, macro_block_size=None)
            
            start_time = time.time()
            while time.time() - start_time < duration:
                # Capture screen
                img = sct.grab(monitor)
                # Convert to format suitable for imageio (RGB)
                # MSS gives BGRA, we need RGB
                frame = imageio.core.util.Image(img.rgb)
                writer.append_data(frame)
                
                # Sleep to maintain rough FPS
                time.sleep(1 / fps)
                
            writer.close()

        with open(temp_path, "rb") as f:
            video_bytes = f.read()
            
        os.remove(temp_path)
        return video_bytes
        
    except Exception as e:
        logger.error(f"Video recording failed: {e}")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return None
