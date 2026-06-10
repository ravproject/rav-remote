"""
Command Handler — Eksekusi perintah yang sudah divalidasi
Setiap handler WAJIB melalui sanitizer sebelum eksekusi
"""
import os
import subprocess
import platform
from pathlib import Path
from loguru import logger
from security.sanitizer import InputSanitizer
from security.sandbox import SandboxExecutor
from agent.screenshot import take_screenshot
from agent.system_monitor import get_system_info
from agent.file_manager import list_files, get_file
from agent.executor import run_script


class CommandHandler:

    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.sandbox = SandboxExecutor()

    async def handle_screenshot(self) -> bytes:
        """Ambil screenshot dan return sebagai bytes PNG."""
        return take_screenshot()

    async def handle_sysinfo(self) -> str:
        """Ambil informasi sistem."""
        return get_system_info()

    async def handle_list_files(self, path: str) -> str:
        """List isi direktori — dengan validasi path."""
        return list_files(path)

    async def handle_get_file(self, filepath: str) -> dict:
        """Kirim file ke user — dengan validasi ekstensi dan ukuran."""
        return get_file(filepath)

    async def handle_run_script(self, script_name: str, user_id: str) -> str:
        """
        Jalankan script dari direktori aman — WAJIB di sandbox.
        Hanya file .py dan .sh dari ~/safe_scripts yang diizinkan.
        """
        return await run_script(script_name, user_id)

    async def handle_lock_screen(self) -> str:
        """Kunci layar laptop."""
        system = platform.system()
        if system == "Linux":
            # Coba beberapa window manager
            for cmd in ["loginctl lock-session", "xdg-screensaver lock", "gnome-screensaver-command -l"]:
                try:
                    subprocess.run(cmd.split(), timeout=5, check=True)
                    return "🔒 Layar dikunci."
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
        elif system == "Darwin":  # macOS
            subprocess.run(["pmset", "displaysleepnow"])
            return "🔒 Layar dikunci."
        elif system == "Windows":
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return "🔒 Layar dikunci."

        return "❌ Gagal mengunci layar."

    async def handle_reboot(self, confirmed: bool = False) -> str:
        """Restart laptop — butuh konfirmasi."""
        if not confirmed:
            return """⚠️ Yakin ingin restart?\nBalas: `!reboot confirm`"""
        system = platform.system()
        if system == "Linux":
            subprocess.Popen(["sudo", "reboot"])
        elif system == "Darwin":
            subprocess.Popen(["sudo", "reboot"])
        elif system == "Windows":
            subprocess.Popen(["shutdown", "/r", "/t", "10"])
        return "🔄 Laptop akan restart dalam 10 detik..."
