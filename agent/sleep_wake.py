import subprocess
import shutil
from datetime import datetime, timedelta
from loguru import logger

from agent.platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS, has_tool


def sleep_laptop(delay: str = None) -> str:
    if delay:
        try:
            from agent.time_utils import parse_duration
            seconds = parse_duration(delay)
            import time as t
            t.sleep(seconds)
        except Exception as e:
            return f"Format delay salah: {e}"

    if IS_LINUX:
        for cmd in [["systemctl", "suspend"], ["loginctl", "suspend"]]:
            try:
                subprocess.run(cmd, capture_output=True, timeout=5)
                return "Laptop sleep..."
            except Exception:
                continue
        return "Gagal sleep. Install systemd atau logind."
    elif IS_MACOS:
        try:
            subprocess.run(["pmset", "sleepnow"], capture_output=True, timeout=5)
            return "Laptop sleep..."
        except Exception as e:
            return f"Gagal sleep: {e}"
    elif IS_WINDOWS:
        try:
            import ctypes
            ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
            return "Laptop sleep..."
        except Exception as e:
            return f"Gagal sleep: {e}"
    return "Sleep belum didukung di OS ini."


def wake_laptop(time_str: str) -> str:
    if IS_LINUX:
        if not has_tool("rtcwake"):
            return "rtcwake tidak ditemukan. Install util-linux."
        try:
            if ":" in time_str:
                now = datetime.now()
                parts = time_str.split(":")
                target = now.replace(hour=int(parts[0]), minute=int(parts[1]), second=0)
                if target < now:
                    target += timedelta(days=1)
                seconds = int((target - now).total_seconds())
                subprocess.run(["sudo", "rtcwake", "-m", "no", "-s", str(seconds)],
                               capture_output=True, timeout=5)
                return f"Wake dijadwalkan: {time_str}"
            else:
                subprocess.run(["sudo", "rtcwake", "-m", "no", "-s", time_str],
                               capture_output=True, timeout=5)
                return f"Wake dalam {time_str} detik."
        except Exception as e:
            return f"Gagal menjadwalkan wake: {e}"

    elif IS_MACOS:
        try:
            if ":" in time_str:
                subprocess.run(["pmset", "schedule", "wake", time_str],
                               capture_output=True, timeout=5)
                return f"Wake dijadwalkan: {time_str}"
            else:
                return "Gunakan format HH:MM untuk macOS."
        except Exception as e:
            return f"Gagal: {e}"

    elif IS_WINDOWS:
        try:
            t = time_str.replace(":", " ")
            subprocess.run(["schtasks", "/create", "/tn", "rav_remote_wake",
                           "/tr", "shutdown /r", "/sc", "once",
                           "/st", t, "/f"],
                           capture_output=True, timeout=5)
            return f"Wake dijadwalkan: {time_str}"
        except Exception as e:
            return f"Gagal: {e}"

    return "Wake belum didukung di OS ini."
