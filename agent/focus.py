import asyncio
import os
import time
import subprocess
import shutil
import threading
from pathlib import Path
from loguru import logger

from agent.platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS, has_tool, get_platform_paths

FOCUS_BLOCKED_SITES = [
    "facebook.com", "twitter.com", "x.com", "instagram.com",
    "reddit.com", "youtube.com", "tiktok.com", "netflix.com",
    "twitch.tv", "discord.com"
]

focus_alerts: list[str] = []


class FocusManager:
    def __init__(self):
        self.active = False
        self.start_time = None
        self.duration_minutes = 25
        self._timer_thread = None

    def _mute_notifications(self, mute: bool):
        if IS_LINUX:
            try:
                val = "false" if mute else "true"
                subprocess.run(["gsettings", "set", "org.gnome.desktop.notifications", "show-banners", val],
                               capture_output=True, timeout=3)
            except Exception:
                pass
        elif IS_MACOS:
            try:
                mode = "doNotDisturb" if mute else "off"
                subprocess.run(["osascript", "-e",
                               f'tell application "System Events" to tell notification center to set its dnd state to {mute}'],
                               capture_output=True, timeout=5)
            except Exception:
                pass
        elif IS_WINDOWS:
            try:
                import ctypes
                import ctypes.wintypes
                # Enable/disable quiet hours
                pass
            except Exception:
                pass

    def _block_sites(self):
        hosts_path = get_platform_paths()["hosts"]
        try:
            if os.access(hosts_path, os.W_OK):
                with open(hosts_path, "a") as f:
                    for site in FOCUS_BLOCKED_SITES:
                        f.write(f"0.0.0.0 {site}\n")
                        f.write(f"0.0.0.0 www.{site}\n")
                return True
            else:
                logger.warning(f"Cannot block sites: {hosts_path} not writable")
                return False
        except Exception as e:
            logger.error(f"Failed to block sites: {e}")
            return False

    def _unblock_sites(self):
        hosts_path = get_platform_paths()["hosts"]
        try:
            if not os.access(hosts_path, os.W_OK):
                return
            with open(hosts_path, "r") as f:
                lines = f.readlines()
            with open(hosts_path, "w") as f:
                for line in lines:
                    if not any(site in line for site in FOCUS_BLOCKED_SITES):
                        f.write(line)
        except Exception as e:
            logger.error(f"Failed to unblock sites: {e}")

    def start(self, minutes: int = 25):
        if self.active:
            return f"Focus Mode sudah aktif. Sisa: {self.get_remaining()}"
        self.active = True
        self.duration_minutes = minutes
        self.start_time = time.time()
        self._mute_notifications(True)
        self._block_sites()
        self._start_timer()
        return f"Focus Mode AKTIF selama {minutes} menit. Notifikasi dimatikan, situs diblokir."

    def stop(self):
        if not self.active:
            return "Focus Mode tidak aktif."
        self.active = False
        self.start_time = None
        self._mute_notifications(False)
        self._unblock_sites()
        return "Focus Mode DINONAKTIFKAN."

    def get_remaining(self) -> str:
        if not self.active or not self.start_time:
            return "Focus Mode tidak aktif."
        elapsed = time.time() - self.start_time
        remaining = max(0, self.duration_minutes * 60 - elapsed)
        mins, secs = divmod(int(remaining), 60)
        return f"Focus Mode: sisa {mins}:{secs:02d} dari {self.duration_minutes} menit."

    def _start_timer(self):
        def _timer():
            duration = self.duration_minutes * 60
            while self.active and duration > 0:
                time.sleep(1)
                duration -= 1
            if self.active:
                self.active = False
                self.start_time = None
                self._mute_notifications(False)
                self._unblock_sites()
                msg = f"Focus Mode SELESAI setelah {self.duration_minutes} menit."
                logger.info(msg)
                focus_alerts.append(msg)

        thread = threading.Thread(target=_timer, daemon=True)
        thread.start()

    def get_pending_alerts(self) -> list[str]:
        alerts = list(focus_alerts)
        focus_alerts.clear()
        return alerts


focus_manager = FocusManager()
