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
    """Linux Hybrid High-FPS capture (The proven method)."""
    frames_dir = tempfile.TemporaryDirectory()
    try:
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "enable-animations", "false"], capture_output=True)
        fps = 6
        total_frames = int(duration * fps)
        interval = 1.0 / fps
        start_time = time.time()
        
        for i in range(total_frames):
            frame_path = os.path.join(frames_dir.name, f"frame_{i:04d}.png")
            res = subprocess.run(["flameshot", "full", "--raw"], capture_output=True, timeout=3)
            if res.returncode == 0:
                with open(frame_path, "wb") as f: f.write(res.stdout)
            
            elapsed = time.time() - start_time
            expected = (i + 1) * interval
            if expected > elapsed: time.sleep(expected - elapsed)

        merge_cmd = [
            "ffmpeg", "-y", "-framerate", str(fps), "-i", os.path.join(frames_dir.name, "frame_%04d.png"),
            "-vf", "scale=1280:720,format=yuv420p", "-c:v", "libx264", "-profile:v", "main",
            "-level", "4.0", "-preset", "ultrafast", "-crf", "24", "-movflags", "+faststart", temp_mp4
        ]
        subprocess.run(merge_cmd, capture_output=True)
        return _finalize_video_dict(temp_mp4)
    finally:
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "enable-animations", "true"], capture_output=True)
        frames_dir.cleanup()

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
