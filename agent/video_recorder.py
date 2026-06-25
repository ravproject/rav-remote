"""
LOCKED ARCHITECTURE — Cross-Platform Video Recorder.
Automatically detects OS and uses the most robust/silent method.
"""
import subprocess
import tempfile
import os
import time
import platform
from loguru import logger
from typing import Optional

def record_video(duration: int = 5) -> Optional[dict]:
    """
    Record screen across platforms (Windows, Linux, macOS).
    Stability-first and Zero-flash.
    """
    current_os = platform.system()
    temp_mp4 = os.path.join(tempfile.gettempdir(), f"screen_{int(time.time())}.mp4")
    
    try:
        logger.info(f"Starting {current_os} Record ({duration}s)...")
        
        if current_os == "Linux":
            # Optimized Linux Hybrid Capture (proven zero-flash)
            return _record_linux(duration, temp_mp4)
            
        elif current_os == "Windows":
            # Windows direct capture using FFmpeg gdigrab
            return _record_windows(duration, temp_mp4)
            
        elif current_os == "Darwin": # macOS
            # macOS capture using avfoundation
            return _record_macos(duration, temp_mp4)
            
        return None

    except Exception as e:
        logger.error(f"Recording failed on {current_os}: {e}")
        return None
    finally:
        if os.path.exists(temp_mp4):
            try: os.remove(temp_mp4)
            except: pass

def _record_linux(duration, temp_mp4):
    """Linux Wayland recording via wf-recorder (GNOME/Wayland)."""
    env = os.environ.copy()
    env["WAYLAND_DISPLAY"] = env.get("WAYLAND_DISPLAY", "wayland-0")
    try:
        cmd = ["wf-recorder", "-f", temp_mp4, "-r", "15", "-c", "libx264",
               "-p", "preset=ultrafast", "-p", "crf=28"]
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc.wait(timeout=duration + 2)
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        if os.path.exists(temp_mp4) and os.path.getsize(temp_mp4) > 1000:
            return _finalize_video_dict(temp_mp4)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        if os.path.exists(temp_mp4) and os.path.getsize(temp_mp4) > 1000:
            return _finalize_video_dict(temp_mp4)
    except FileNotFoundError:
        logger.error("wf-recorder not found. Install: sudo apt install wf-recorder")
    except Exception as e:
        logger.error(f"wf-recorder failed: {e}")
    return None

def _record_windows(duration, temp_mp4):
    """Windows capture using gdigrab."""
    cmd = [
        "ffmpeg", "-y", "-f", "gdigrab", "-framerate", "15", "-i", "desktop",
        "-t", str(duration), "-vf", "scale=1280:720,format=yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-movflags", "+faststart", temp_mp4
    ]
    subprocess.run(cmd, capture_output=True)
    return _finalize_video_dict(temp_mp4)

def _record_macos(duration, temp_mp4):
    """macOS capture using avfoundation."""
    cmd = [
        "ffmpeg", "-y", "-f", "avfoundation", "-framerate", "15", "-i", "1",
        "-t", str(duration), "-vf", "scale=1280:720,format=yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-movflags", "+faststart", temp_mp4
    ]
    subprocess.run(cmd, capture_output=True)
    return _finalize_video_dict(temp_mp4)

def _finalize_video_dict(path):
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        with open(path, "rb") as f:
            data = f.read()
        return {
            "type": "video",
            "data": data,
            "filename": f"screen_{int(time.time())}.mp4",
            "mimetype": "video/mp4"
        }
    return None

if __name__ == "__main__":
    res = record_video(3)
    if res:
        print(f"Success! Captured {len(res['data'])} bytes.")
    else:
        print("Failed to record video.")
