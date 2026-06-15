"""
Professional Webcam Recorder — High-performance GStreamer with v4l2.
Smooth, silent, and optimized for laptop cameras.
"""
import subprocess
import tempfile
import os
import time
from loguru import logger
from typing import Optional

def record_webcam(duration: int = 5) -> Optional[bytes]:
    """
    Record laptop camera using GStreamer.
    """
    temp_mp4 = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
    
    try:
        logger.info(f"Starting Webcam Record ({duration}s)...")
        
        # Determine number of buffers (frames)
        fps = 15
        num_buffers = int(duration * fps)

        # GStreamer Pipeline for Camera:
        # v4l2src: Standard Linux camera source
        pipeline = [
            "gst-launch-1.0",
            "v4l2src", f"num-buffers={num_buffers}", "!",
            "videoconvert", "!",
            "videoscale", "!",
            "video/x-raw,width=1280,height=720", "!",
            "x264enc", "tune=zerolatency", "speed-preset=ultrafast", "!",
            "video/x-h264,profile=baseline", "!",
            "mp4mux", "!",
            "filesink", f"location={temp_mp4}"
        ]
        
        result = subprocess.run(pipeline, capture_output=True, text=True, timeout=duration + 20)
        
        if result.returncode != 0:
            logger.error(f"Webcam record failed: {result.stderr}")
            return None

        if os.path.exists(temp_mp4) and os.path.getsize(temp_mp4) > 1000:
            # Add faststart
            final_mp4 = temp_mp4 + ".webcam.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_mp4, 
                "-c", "copy", "-movflags", "+faststart", final_mp4
            ], capture_output=True)
            
            target = final_mp4 if os.path.exists(final_mp4) else temp_mp4
            with open(target, "rb") as f:
                video_data = f.read()
            
            if os.path.exists(final_mp4): os.remove(final_mp4)
            return video_data
        
        return None

    except Exception as e:
        logger.error(f"Webcam recording failed: {e}")
        return None
    finally:
        if os.path.exists(temp_mp4):
            try: os.remove(temp_mp4)
            except: pass

if __name__ == "__main__":
    res = record_webcam(3)
    if res:
        print(f"Success! Captured {len(res)} bytes.")
    else:
        print("Failed to record webcam.")
