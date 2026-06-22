"""
Sleep & Wake — put laptop to sleep or schedule wake.
"""
import subprocess
import shutil
from datetime import datetime, timedelta
from loguru import logger

def sleep_laptop(delay: str = None) -> str:
    if delay:
        try:
            delay = delay.lower().strip()
            if delay.endswith("s"):
                seconds = int(delay[:-1])
            elif delay.endswith("m") or delay.endswith("menit"):
                seconds = int(delay.replace("menit", "").replace("m", "").strip()) * 60
            elif delay.endswith("jam") or delay.endswith("h"):
                seconds = int(delay.replace("jam", "").replace("h", "").strip()) * 3600
            else:
                seconds = int(delay)
            import time as t
            t.sleep(seconds)
        except Exception as e:
            return f"Format delay salah: {e}. Contoh: 30s, 5m, 1jam"
    try:
        subprocess.run(["systemctl", "suspend"], capture_output=True, timeout=5)
        return "💤 Laptop sleep..."
    except Exception:
        try:
            subprocess.run(["loginctl", "suspend"], capture_output=True, timeout=5)
            return "💤 Laptop sleep..."
        except Exception as e:
            return f"Gagal sleep: {e}"

def wake_laptop(time_str: str) -> str:
    if not shutil.which("rtcwake"):
        return "rtcwake tidak ditemukan. Install: sudo apt install util-linux"
    try:
        if ":" in time_str:
            now = datetime.now()
            parts = time_str.split(":")
            target = now.replace(hour=int(parts[0]), minute=int(parts[1]), second=0)
            if target < now:
                target += timedelta(days=1)
            seconds = int((target - now).total_seconds())
            subprocess.run(["sudo", "rtcwake", "-m", "no", "-s", str(seconds)], capture_output=True, timeout=5)
            return f"⏰ Wake dijadwalkan: {time_str}"
        elif time_str.endswith("s") or time_str.endswith("m"):
            subprocess.run(["sudo", "rtcwake", "-m", "no", "-s", time_str], capture_output=True, timeout=5)
            return f"⏰ Wake dalam {time_str}"
        else:
            subprocess.run(["sudo", "rtcwake", "-m", "no", "-s", time_str], capture_output=True, timeout=5)
            return f"⏰ Wake dijadwalkan dalam {time_str} detik."
    except Exception as e:
        return f"Gagal menjadwalkan wake: {e}"
