"""
Command Handler — Eksekusi perintah yang sudah divalidasi
Setiap handler WAJIB melalui sanitizer sebelum eksekusi
"""
import os
import subprocess
import platform
import asyncio
import time
from pathlib import Path
from typing import Optional
from loguru import logger
from security.sanitizer import InputSanitizer
from security.sandbox import SandboxExecutor
from agent.screenshot import take_screenshot
from agent.system_monitor import sys_monitor
from agent.file_manager import list_files, get_file
from agent.executor import run_script
from agent.video_recorder import record_video
from agent.webcam import capture_webcam


class CommandHandler:

    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.sandbox = SandboxExecutor()
        self._cwd = str(Path.home()) # Default persistent directory

    def set_cwd(self, path: str) -> str:
        """Update current working directory for all commands."""
        target = Path(path).expanduser().resolve()
        if target.exists() and target.is_dir():
            self._cwd = str(target)
            return f"📂 Direktori kerja sekarang: `{self._cwd}`"
        return f"❌ Direktori tidak ditemukan: `{path}`"

    def get_cwd(self) -> str:
        return self._cwd

    async def handle_screenshot(self) -> bytes:
        """Ambil screenshot dan return sebagai bytes PNG."""
        return await asyncio.to_thread(take_screenshot)

    async def handle_video(self, duration: int = 5) -> Optional[bytes]:
        """Rekam layar dan return sebagai bytes MP4."""
        return await asyncio.to_thread(record_video, duration)

    async def handle_webcam(self) -> Optional[bytes]:
        """Ambil foto webcam dan return sebagai bytes JPG."""
        return await asyncio.to_thread(capture_webcam)

    async def handle_webcam_video(self, duration: int = 5) -> Optional[bytes]:
        """Rekam video webcam dan return sebagai bytes MP4."""
        from agent.webcam_recorder import record_webcam
        return await asyncio.to_thread(record_webcam, duration)

    async def handle_sysinfo(self) -> str:
        """Ambil informasi sistem."""
        return await asyncio.to_thread(sys_monitor.get_system_summary)

    async def handle_list_files(self, path: str) -> str:
        """List isi direktori — dengan validasi path."""
        # Use current working directory if path is relative
        target = path if os.path.isabs(path) or path.startswith("~") else os.path.join(self._cwd, path)
        return await asyncio.to_thread(list_files, target)

    async def handle_get_file(self, filepath: str) -> dict:
        """Kirim file ke user — dengan validasi ekstensi dan ukuran."""
        target = filepath if os.path.isabs(filepath) or filepath.startswith("~") else os.path.join(self._cwd, filepath)
        return await asyncio.to_thread(get_file, target)

    async def handle_ai_cli(self, cli_name: str, args: list) -> str:
        """Jalankan AI CLI (gemini, antigravity, opencode) secara aman di CWD."""
        # ... logic flags ...
        safety_flags = {
            "gemini": "--yolo",
            "antigravity": "--yolo",
            "opencode": "--dangerously-skip-permissions"
        }
        
        flag = safety_flags.get(cli_name, "")
        cmd_args = list(args)
        
        if flag and flag not in cmd_args:
            if cli_name == "opencode" and "run" in cmd_args:
                idx = cmd_args.index("run")
                cmd_args.insert(idx + 1, flag)
            else:
                cmd_args.insert(0, flag)
        
        full_cmd = [cli_name] + cmd_args
        
        try:
            # Execute in the shared current working directory (self._cwd)
            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._cwd
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            
            output = stdout.decode().strip()
            error = stderr.decode().strip()
            
            if process.returncode != 0:
                return f"❌ Error {cli_name}:\n{error or output}"
            
            return output or "✅ Selesai (Tanpa Output)"
            
        except asyncio.TimeoutError:
            return f"⏳ Timeout: Perintah {cli_name} memakan waktu terlalu lama."
        except Exception as e:
            return f"❌ Exception running {cli_name}: {str(e)}"

    async def handle_run_script(self, script_name: str, user_id: str) -> str:
        """
        Jalankan script dari direktori aman — WAJIB di sandbox.
        Hanya file .py dan .sh dari ~/safe_scripts yang diizinkan.
        """
        return await run_script(script_name, user_id)

    async def handle_lock_screen(self) -> str:
        """Kunci layar laptop (Cross-Platform)."""
        current_os = platform.system()
        try:
            if current_os == "Linux":
                # Coba beberapa window manager
                for cmd in ["loginctl lock-session", "xdg-screensaver lock", "gnome-screensaver-command -l"]:
                    try:
                        subprocess.run(cmd.split(), timeout=5, check=True)
                        return f"🔒 Layar {current_os} berhasil dikunci."
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
            elif current_os == "Windows":
                import ctypes
                ctypes.windll.user32.LockWorkStation()
                return f"🔒 Layar {current_os} berhasil dikunci."
            elif current_os == "Darwin": # macOS
                subprocess.run(["pmset", "displaysleepnow"], capture_output=True)
                return f"🔒 Layar {current_os} berhasil dikunci."
            
            return f"❌ Fitur lock belum didukung untuk OS: {current_os}"
        except Exception as e:
            return f"❌ Gagal mengunci layar: {str(e)}"

    async def handle_unlock_screen(self, password: Optional[str] = None) -> str:
        """Buka kunci layar laptop (Cross-Platform) dengan Force Unlock (Keystroke Simulation)."""
        current_os = platform.system()
        
        if current_os != "Linux":
            if current_os == "Windows":
                return "⚠️ Windows memblokir remote unlock demi keamanan. Anda harus melakukannya secara fisik atau via RDP."
            elif current_os == "Darwin":
                subprocess.run(["caffeinate", "-u", "-t", "1"], capture_output=True)
                return "🔓 Layar macOS dibangunkan. Jika terkunci, fitur input password belum didukung."
            return f"❌ Fitur unlock belum didukung untuk OS: {current_os}"

        if not password:
            # Coba metode standar dulu jika tanpa password (Non-blocking enough)
            subprocess.run(["loginctl", "unlock-sessions"], capture_output=True)
            return "🔓 Perintah buka kunci terkirim (tanpa password). Jika layar masih meminta password, gunakan: `!unlock <password_laptop>`"

        # Offload heavy/blocking subprocess operations to a thread to prevent Agent hang
        return await asyncio.to_thread(self._force_unlock_linux_sync, password)

    def _force_unlock_linux_sync(self, password: str) -> str:
        """Synchronous forceful unlock logic isolated to prevent event loop blocking."""
        try:
            # 1. Cek apakah ydotool terinstall
            res_check = subprocess.run(["which", "ydotool"], capture_output=True, text=True)
            if res_check.returncode != 0:
                # Install ydotool tanpa apt-get update agar cepat
                install_cmd = f"echo '{password}' | sudo -S apt-get install -y ydotool"
                res_install = subprocess.run(install_cmd, shell=True, capture_output=True, text=True, timeout=30)
                if res_install.returncode != 0:
                    return f"❌ Gagal menginstall ydotool (Password sudo mungkin salah atau butuh update manual).\nDetail: {res_install.stderr}"

            # 2. Matikan daemon lama jika ada
            subprocess.run(f"echo '{password}' | sudo -S pkill ydotoold", shell=True, capture_output=True, timeout=5)
            
            # 3. Jalankan daemon ydotool
            # SANGAT PENTING: Gunakan Popen dan DEVNULL agar Python tidak menunggu output pipe daemon
            daemon_cmd = f"echo '{password}' | sudo -S ydotoold"
            subprocess.Popen(daemon_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2) # Tunggu daemon siap

            # 4. Bangunkan layar (Escape dari blank screen)
            # Menggunakan ydotool untuk menekan ESC memunculkan prompt password
            subprocess.run(f"echo '{password}' | sudo -S ydotool key 1:1 1:0", shell=True, capture_output=True, timeout=5)
            time.sleep(1)

            # 5. Ketik password dan Enter
            type_cmd = ["sudo", "-S", "ydotool", "type", password]
            proc = subprocess.Popen(type_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.communicate(input=f"{password}\n".encode(), timeout=10)
            
            time.sleep(0.5)
            # Tekan Enter (Keycode 28)
            subprocess.run(f"echo '{password}' | sudo -S ydotool key 28:1 28:0", shell=True, capture_output=True, timeout=5)

            return "🔓 Force Unlock berhasil dieksekusi! Layar seharusnya sudah terbuka."
        
        except subprocess.TimeoutExpired:
            return "⏳ Waktu Habis: Proses instalasi atau eksekusi sistem memakan waktu terlalu lama."
        except Exception as e:
            return f"❌ Gagal mengeksekusi force unlock: {str(e)}"

    async def handle_reboot(self, confirmed: bool = False) -> str:
        """Restart laptop — butuh konfirmasi (Cross-Platform)."""
        if not confirmed:
            return """⚠️ Yakin ingin restart?\nBalas: `!reboot confirm`"""

        current_os = platform.system()
        try:
            if current_os == "Windows":
                subprocess.run(["shutdown", "/r", "/t", "5"], capture_output=True)
            else: # Linux & macOS
                subprocess.run(["sudo", "reboot"], capture_output=True)
            return f"🔄 Laptop ({current_os}) akan restart dalam 5 detik..."
        except Exception as e:
            return f"❌ Gagal melakukan restart: {str(e)}"


    async def handle_test_ai(self) -> str:
        """Test koneksi ke NVIDIA NIM API."""
        from ai_module.nim_client import NIMClient
        client = NIMClient()
        if not client.enabled:
            return "❌ AI Mode dinonaktifkan atau API Key belum di-set di .env"
        
        try:
            # Test sederhana dengan input minimal
            res = await client.translate_to_command("test")
            if res:
                return "✅ Koneksi AI NIM Sukses! Server merespons dengan baik."
            return "⚠️ AI terhubung tapi memberikan respons tidak terduga."
        except Exception as e:
            return f"❌ Koneksi AI Gagal: {str(e)}"
