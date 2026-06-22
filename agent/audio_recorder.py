"""
Audio Recorder Modul — Merekam audio sekitar menggunakan FFmpeg dalam format MP3 agar dapat langsung diputar di Telegram/WhatsApp.
"""
import subprocess
import tempfile
import os
import time
import platform
from loguru import logger
from typing import Optional

def record_audio(duration: int = 5) -> Optional[dict]:
    """
    Record ambient audio from default microphone using FFmpeg as MP3.
    Returns a dictionary compatible with the Agent's audio sender.
    """
    current_os = platform.system()
    temp_mp3 = os.path.join(tempfile.gettempdir(), f"audio_{int(time.time())}.mp3")
    
    try:
        logger.info(f"Starting {current_os} Audio Record ({duration}s, MP3 format)...")
        
        if current_os == "Linux":
            success = _record_linux(duration, temp_mp3)
        elif current_os == "Windows":
            success = _record_windows(duration, temp_mp3)
        elif current_os == "Darwin": # macOS
            success = _record_macos(duration, temp_mp3)
        else:
            logger.error(f"OS {current_os} not supported for audio recording.")
            success = False
            
        if success and os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 1000:
            with open(temp_mp3, "rb") as f:
                data = f.read()
            return {
                "type": "audio",
                "data": data,
                "filename": f"audio_{int(time.time())}.mp3",
                "mimetype": "audio/mpeg"
            }
            
        return None

    except Exception as e:
        logger.error(f"Audio recording failed on {current_os}: {e}")
        return None
    finally:
        if os.path.exists(temp_mp3):
            try: os.remove(temp_mp3)
            except: pass

def _record_linux(duration: int, output_path: str) -> bool:
    """Linux Audio Capture trying pulse first, then falling back to alsa."""
    # Try PulseAudio with libmp3lame encoder
    cmd_pulse = [
        "ffmpeg", "-y", "-f", "pulse", "-i", "default",
        "-t", str(duration), "-acodec", "libmp3lame", "-ar", "44100", "-ab", "128k", output_path
    ]
    logger.debug(f"Executing: {' '.join(cmd_pulse)}")
    res = subprocess.run(cmd_pulse, capture_output=True)
    if res.returncode == 0:
        return True
        
    logger.warning("PulseAudio recording failed, falling back to ALSA...")
    # Try ALSA with libmp3lame encoder
    cmd_alsa = [
        "ffmpeg", "-y", "-f", "alsa", "-i", "default",
        "-t", str(duration), "-acodec", "libmp3lame", "-ar", "44100", "-ab", "128k", output_path
    ]
    logger.debug(f"Executing: {' '.join(cmd_alsa)}")
    res = subprocess.run(cmd_alsa, capture_output=True)
    return res.returncode == 0

def _record_windows(duration: int, output_path: str) -> bool:
    """Windows Audio Capture using dshow default audio device as MP3."""
    cmd = [
        "ffmpeg", "-y", "-f", "dshow", "-i", "audio=default",
        "-t", str(duration), "-acodec", "libmp3lame", "-ar", "44100", "-ab", "128k", output_path
    ]
    logger.debug(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True)
    return res.returncode == 0

def _record_macos(duration: int, output_path: str) -> bool:
    """macOS Audio Capture using avfoundation default audio input device as MP3."""
    cmd = [
        "ffmpeg", "-y", "-f", "avfoundation", "-i", ":0",
        "-t", str(duration), "-acodec", "libmp3lame", "-ar", "44100", "-ab", "128k", output_path
    ]
    logger.debug(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True)
    return res.returncode == 0
