"""
Focus Mode — blocks distractions, runs Pomodoro timer, silences notifications.
"""
import os
import time
import subprocess
import shutil
from pathlib import Path
from loguru import logger

FOCUS_BLOCKED_SITES = [
    "facebook.com", "twitter.com", "x.com", "instagram.com",
    "reddit.com", "youtube.com", "tiktok.com", "netflix.com",
    "twitch.tv", "discord.com"
]

class FocusManager:
    def __init__(self):
        self.active = False
        self.start_time = None
        self.duration_minutes = 25

    def _mute_notifications(self, mute: bool):
        try:
            if mute:
                subprocess.run(["gsettings", "set", "org.gnome.desktop.notifications", "show-banners", "false"], capture_output=True, timeout=3)
            else:
                subprocess.run(["gsettings", "set", "org.gnome.desktop.notifications", "show-banners", "true"], capture_output=True, timeout=3)
        except Exception:
            pass

    def _block_sites(self):
        hosts_path = "/etc/hosts"
        if not os.access(hosts_path, os.W_OK):
            logger.warning("Cannot block sites: /etc/hosts not writable")
            return False
        try:
            with open(hosts_path, "a") as f:
                for site in FOCUS_BLOCKED_SITES:
                    f.write(f"0.0.0.0 {site}\n")
                    f.write(f"0.0.0.0 www.{site}\n")
            return True
        except Exception as e:
            logger.error(f"Failed to block sites: {e}")
            return False

    def _unblock_sites(self):
        hosts_path = "/etc/hosts"
        if not os.access(hosts_path, os.W_OK):
            return
        try:
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
        return f"Focus Mode AKTIF selama {minutes} menit. Notifikasi dimatikan, situs diblokir."

    def stop(self):
        if not self.active:
            return "Focus Mode tidak aktif."
        self.active = False
        self.start_time = None
        self._mute_notifications(False)
        self._unblock_sites()
        return "Focus Mode DINONAKTIFKAN. Notifikasi dikembalikan, situs dibuka."

    def get_remaining(self) -> str:
        if not self.active or not self.start_time:
            return "Focus Mode tidak aktif."
        elapsed = time.time() - self.start_time
        remaining = max(0, self.duration_minutes * 60 - elapsed)
        mins, secs = divmod(int(remaining), 60)
        return f"Focus Mode: sisa {mins}:{secs:02d} dari {self.duration_minutes} menit."

focus_manager = FocusManager()
