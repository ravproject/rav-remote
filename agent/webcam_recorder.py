import subprocess
import tempfile
import os
import time
from loguru import logger
from typing import Optional

from agent.platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS, has_tool


def record_webcam(duration: int = 5) -> Optional[bytes]:
    temp_mp4 = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name

    try:
        logger.info(f"Starting Webcam Record ({duration}s)...")

        if IS_LINUX:
            success = _record_linux(duration, temp_mp4)
        elif IS_MACOS:
            success = _record_macos(duration, temp_mp4)
        elif IS_WINDOWS:
            success = _record_windows(duration, temp_mp4)
        else:
            logger.error(f"OS not supported")
            success = False

        if success and os.path.exists(temp_mp4) and os.path.getsize(temp_mp4) > 1000:
            with open(temp_mp4, "rb") as f:
                data = f.read()
            return {
                "type": "video",
                "data": data,
                "filename": f"webcam_{int(time.time())}.mp4",
                "mimetype": "video/mp4"
            }
        return None
    except Exception as e:
        logger.error(f"Webcam recording failed: {e}")
        return None
    finally:
        if os.path.exists(temp_mp4):
            try:
                os.remove(temp_mp4)
            except Exception:
                pass


def _record_linux(duration: int, output: str) -> bool:
    fps = 15
    num_buffers = int(duration * fps)
    try:
        if has_tool("gst-launch-1.0"):
            pipeline = [
                "gst-launch-1.0",
                "v4l2src", f"num-buffers={num_buffers}", "!",
                "videoconvert", "!",
                "x264enc", "tune=zerolatency", "speed-preset=ultrafast", "!",
                "mp4mux", "!",
                "filesink", f"location={output}"
            ]
            subprocess.run(pipeline, capture_output=True, text=True, timeout=duration + 20)
            return os.path.exists(output) and os.path.getsize(output) > 1000
    except Exception:
        pass

    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return False
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output, fourcc, fps, (640, 480))
        for _ in range(duration * fps):
            ret, frame = cap.read()
            if ret:
                out.write(frame)
        cap.release()
        out.release()
        return os.path.exists(output) and os.path.getsize(output) > 1000
    except Exception:
        return False


def _record_macos(duration: int, output: str) -> bool:
    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "avfoundation",
            "-framerate", "15",
            "-video_size", "640x480",
            "-i", "0",
            "-t", str(duration),
            output
        ]
        subprocess.run(cmd, capture_output=True, timeout=duration + 20)
        return os.path.exists(output) and os.path.getsize(output) > 1000
    except Exception as e:
        logger.error(f"macOS webcam failed: {e}")
        return False


def _record_windows(duration: int, output: str) -> bool:
    try:
        import cv2
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return False
        fps = 15
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output, fourcc, fps, (640, 480))
        for _ in range(duration * fps):
            ret, frame = cap.read()
            if ret:
                out.write(frame)
        cap.release()
        out.release()
        return os.path.exists(output) and os.path.getsize(output) > 1000
    except Exception as e:
        logger.error(f"Windows webcam failed: {e}")
        return False
