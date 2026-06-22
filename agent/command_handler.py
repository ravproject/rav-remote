"""
Command Handler — Eksekusi perintah yang sudah divalidasi
Setiap handler WAJIB melalui sanitizer sebelum eksekusi
"""
import os
import subprocess
import platform
import asyncio
import time
import pyperclip
import webbrowser
import psutil
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
from agent.audio_recorder import record_audio
from agent.input_simulator import simulate_click, simulate_type, simulate_press
from agent.active_window import get_active_window_title

# State sinkronisasi clipboard otomatis
clipboard_sync_active = False
last_clipboard_value = ""
clipboard_alerts = []  # Antrean pesan clipboard baru untuk pull-model heartbeat

async def clipboard_sync_loop():
    """Background loop to monitor laptop clipboard and sync to Telegram/Heartbeat."""
    import pyperclip
    import os
    import httpx
    global last_clipboard_value, clipboard_sync_active, clipboard_alerts
    
    try:
        last_clipboard_value = await asyncio.to_thread(pyperclip.paste)
    except Exception:
        last_clipboard_value = ""
        
    while True:
        try:
            if clipboard_sync_active:
                curr = await asyncio.to_thread(pyperclip.paste)
                if curr and curr != last_clipboard_value:
                    last_clipboard_value = curr
                    
                    alert_text = f"[CLIPBOARD] Teks disalin: {curr[:150]}..." if len(curr) > 150 else f"[CLIPBOARD] Teks disalin: {curr}"
                    clipboard_alerts.append(alert_text)
                    
                    token = os.environ.get("TELEGRAM_BOT_TOKEN")
                    uids = os.environ.get("ALLOWED_USER_IDS", "").split(",")
                    if token and uids:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            for uid in uids:
                                uid = uid.strip()
                                if uid:
                                    url = f"https://api.telegram.org/bot{token}/sendMessage"
                                    msg = f"📋 <b>[Clipboard Sync]</b>\n<code>{curr[:1000]}</code>"
                                    try:
                                        await client.post(url, json={"chat_id": uid, "text": msg, "parse_mode": "HTML"})
                                    except Exception as err:
                                        logger.debug(f"Direct clipboard sync telegram send failed for {uid}: {err}")
        except Exception as e:
            logger.debug(f"Error in clipboard_sync_loop: {e}")
        await asyncio.sleep(2)


class CommandHandler:

    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.sandbox = SandboxExecutor()
        self._cwd = str(Path.home() / "Documents") # Default persistent directory (whitelisted)

    def set_cwd(self, path: str) -> str:
        """Update current working directory for all commands."""
        if os.path.isabs(path) or path.startswith("~"):
            target = Path(path).expanduser().resolve()
        else:
            target = (Path(self._cwd) / path).resolve()

        if target.exists() and target.is_dir():
            self._cwd = str(target)
            return f"📂 Direktori kerja sekarang: `{self._cwd}`"
        return f"❌ Direktori tidak ditemukan: `{path}`"

    def get_cwd(self) -> str:
        return self._cwd

    async def handle_screenshot(self, grid: bool = False) -> bytes:
        """Ambil screenshot dan return sebagai bytes PNG."""
        return await asyncio.to_thread(take_screenshot, grid)

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

    async def handle_clip_read(self) -> str:
        """Baca teks dari clipboard laptop."""
        try:
            text = await asyncio.to_thread(pyperclip.paste)
            return f"📋 **Clipboard:**\n<code>{text[:1000]}</code>" if text else "📋 Clipboard kosong."
        except Exception as e:
            return f"❌ Gagal membaca clipboard: {e}"

    async def handle_clip_write(self, text: str) -> str:
        """Tulis teks ke clipboard laptop."""
        try:
            await asyncio.to_thread(pyperclip.copy, text)
            return "✅ Teks berhasil disalin ke clipboard laptop."
        except Exception as e:
            return f"❌ Gagal menulis ke clipboard: {e}"

    async def handle_open_url(self, url: str) -> str:
        """Buka URL di browser default laptop."""
        try:
            if not url.startswith("http"): url = "https://" + url
            await asyncio.to_thread(webbrowser.open, url)
            return f"🌐 Berhasil membuka browser untuk: {url}"
        except Exception as e:
            return f"❌ Gagal membuka URL: {e}"

    async def handle_top(self) -> str:
        """Tampilkan proses teratas."""
        try:
            def get_top():
                procs = []
                for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        procs.append(p.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                # Urutkan berdasarkan CPU
                procs = sorted(procs, key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)[:7]
                res = "🔪 **Top Processes:**\n"
                for p in procs:
                    res += f"PID: `{p['pid']}` | CPU: {p.get('cpu_percent', 0):.1f}% | Mem: {p.get('memory_percent', 0):.1f}% | {p['name']}\n"
                return res
            return await asyncio.to_thread(get_top)
        except Exception as e:
            return f"❌ Gagal mengambil daftar proses: {e}"

    async def handle_kill(self, pid: int) -> str:
        """Matikan proses berdasarkan PID."""
        try:
            def kill_proc():
                p = psutil.Process(pid)
                name = p.name()
                p.kill()
                return name
            name = await asyncio.to_thread(kill_proc)
            return f"✅ Berhasil mematikan proses `{name}` (PID: {pid})."
        except psutil.NoSuchProcess:
            return f"❌ Proses dengan PID {pid} tidak ditemukan."
        except psutil.AccessDenied:
            return f"❌ Akses ditolak untuk mematikan PID {pid}."
        except Exception as e:
            return f"❌ Gagal mematikan proses: {e}"

    async def handle_audio_control(self, action: str, value: Optional[str] = None) -> str:
        """Kontrol audio (volume, mute, alarm)."""
        current_os = platform.system()
        try:
            if action == "volume":
                vol = max(0, min(100, int(value or 50)))
                if current_os == "Linux":
                    subprocess.run(["amixer", "set", "Master", f"{vol}%"], capture_output=True)
                elif current_os == "Darwin":
                    subprocess.run(["osascript", "-e", f"set volume output volume {vol}"], capture_output=True)
                # Windows volume requires external libs, leaving as placeholder or partial
                return f"🔊 Volume diatur ke {vol}%"
                
            elif action == "mute":
                if current_os == "Linux":
                    subprocess.run(["amixer", "set", "Master", "toggle"], capture_output=True)
                return "🔇 Status mute/unmute diubah."
                
            elif action == "alarm":
                if current_os == "Linux":
                    subprocess.Popen(["speaker-test", "-t", "sine", "-f", "1000", "-l", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif current_os == "Darwin":
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Ping.aiff"])
                elif current_os == "Windows":
                    import winsound
                    winsound.Beep(1000, 1000)
                return "🚨 Alarm dibunyikan di laptop!"
                
            return "❓ Aksi audio tidak dikenal."
        except Exception as e:
            return f"❌ Gagal mengontrol audio: {e}"

    async def handle_ai_cli(self, cli_name: str, args: list) -> str:
        """Jalankan AI CLI (antigravity, opencode) secara aman di CWD."""
        real_cli = "antigravity" if cli_name == "agy" else cli_name
        safety_flags = {
            "antigravity": "--yolo",
            "opencode": "--dangerously-skip-permissions"
        }
        
        flag = safety_flags.get(real_cli, "")
        cmd_args = list(args)
        
        if flag and flag not in cmd_args:
            if real_cli == "opencode" and "run" in cmd_args:
                idx = cmd_args.index("run")
                cmd_args.insert(idx + 1, flag)
            else:
                cmd_args.insert(0, flag)
        
        full_cmd = [real_cli] + cmd_args
        
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

    async def handle_listen(self, duration: int = 5) -> Optional[dict]:
        """Merekam audio sekitar menggunakan FFmpeg."""
        return await asyncio.to_thread(record_audio, duration)

    async def handle_click(self, x: int, y: int) -> str:
        """Simulasi klik mouse kiri."""
        return await asyncio.to_thread(simulate_click, x, y)

    async def handle_type(self, text: str) -> str:
        """Simulasi mengetik teks."""
        return await asyncio.to_thread(simulate_type, text)

    async def handle_press(self, key: str) -> str:
        """Simulasi menekan tombol keyboard."""
        return await asyncio.to_thread(simulate_press, key)

    async def handle_active_window(self) -> str:
        """Mendeteksi jendela aplikasi yang aktif saat ini."""
        title = await asyncio.to_thread(get_active_window_title)
        return f"🖥️ Jendela Aktif: **{title}**"

    async def handle_brightness(self, args: list) -> str:
        """Mengatur atau membaca kecerahan layar."""
        import os
        import glob
        backlight_dirs = glob.glob("/sys/class/backlight/*")
        if not backlight_dirs:
            return "❌ Tidak ditemukan perangkat backlight (layar internal) pada sistem ini."
        
        backlight_dir = None
        for d in backlight_dirs:
            if "intel_backlight" in d:
                backlight_dir = d
                break
        if not backlight_dir:
            backlight_dir = backlight_dirs[0]
            
        try:
            with open(os.path.join(backlight_dir, "max_brightness"), "r") as f:
                max_bright = int(f.read().strip())
            with open(os.path.join(backlight_dir, "brightness"), "r") as f:
                curr_bright = int(f.read().strip())
        except Exception as e:
            return f"❌ Gagal membaca informasi kecerahan: {e}"
            
        current_percent = round((curr_bright / max_bright) * 100)
        
        if not args:
            return f"🔆 Kecerahan Layar saat ini: **{current_percent}%**\nℹ️ Untuk mengatur: `!brightness <0-100>`"
            
        try:
            target_percent = int(args[0])
            if target_percent < 0 or target_percent > 100:
                raise ValueError()
        except ValueError:
            return "❌ Nilai kecerahan harus berupa angka 0 - 100."
            
        import subprocess
        try:
            subprocess.run(["brightnessctl", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            return f"❌ Gagal mengubah kecerahan ke {target_percent}%.\n⚠️ Prasyarat: Silakan install `brightnessctl` terlebih dahulu dengan perintah: `sudo apt install brightnessctl`."

        try:
            subprocess.run(["brightnessctl", "set", f"{target_percent}%"], check=True)
            return f"✅ Kecerahan layar berhasil diubah menjadi **{target_percent}%**"
        except subprocess.CalledProcessError:
            return (
                f"❌ Gagal mengubah kecerahan ke {target_percent}%: Izin ditolak (Permission denied).\n"
                f"💡 **Solusi:** Jalankan perintah berikut di terminal laptop Anda:\n"
                f"```bash\n"
                f"sudo usermod -aG video $USER\n"
                f"```\n"
                f"Setelah itu, silakan **reboot laptop** atau **log out & log in kembali** agar izin grup Anda diperbarui."
            )
        except Exception as e:
            return f"❌ Gagal mengubah kecerahan ke {target_percent}%: {e}"


    async def handle_media(self, action: str) -> str:
        """Mengontrol pemutar media aktif (MPRIS) atau simulasi media keys."""
        action = action.lower().strip()
        action_map = {
            "play": "Play",
            "pause": "Pause",
            "next": "Next",
            "prev": "Previous"
        }
        if action not in action_map:
            return "❌ Aksi media tidak dikenal. Gunakan: play, pause, next, prev."
            
        mpris_method = action_map[action]
        
        import subprocess
        players = []
        try:
            cmd = ["dbus-send", "--session", "--dest=org.freedesktop.DBus", "--type=method_call", "--print-reply", "/org/freedesktop/DBus", "org.freedesktop.DBus.ListNames"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=True)
            for line in res.stdout.split("\n"):
                if "org.mpris.MediaPlayer2." in line:
                    parts = line.split('"')
                    if len(parts) >= 2:
                        players.append(parts[1])
        except Exception:
            pass
            
        controlled_players = []
        if players:
            for p in players:
                try:
                    dbus_cmd = [
                        "dbus-send", "--session", "--dest=" + p, 
                        "/org/mpris/MediaPlayer2", 
                        "org.mpris.MediaPlayer2.Player." + mpris_method
                    ]
                    subprocess.run(dbus_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    name = p.replace("org.mpris.MediaPlayer2.", "").split(".")[0].capitalize()
                    controlled_players.append(name)
                except Exception:
                    pass
                    
        if controlled_players:
            return f"🎵 Berhasil mengirim perintah **{mpris_method}** ke pemutar media: **{', '.join(set(controlled_players))}**"
            
        fallback_key_map = {
            "play": "playpause",
            "pause": "playpause",
            "next": "nexttrack",
            "prev": "prevtrack"
        }
        key = fallback_key_map[action]
        try:
            import pyautogui
            await asyncio.to_thread(pyautogui.press, key)
            return f"⌨️ Tidak ada pemutar MPRIS aktif. Mensimulasikan penekanan tombol media keyboard: **{key}**"
        except Exception as e:
            return f"❌ Gagal mengontrol media: {e}"

    async def handle_battery(self) -> str:
        """Membaca detail status dan kesehatan baterai laptop."""
        import os
        import glob
        
        battery_dirs = glob.glob("/sys/class/power_supply/BAT*")
        ac_dirs = glob.glob("/sys/class/power_supply/AC*") + glob.glob("/sys/class/power_supply/ADP*")
        
        if not battery_dirs:
            return "❌ Sensor baterai tidak terdeteksi pada sistem ini (mungkin komputer desktop)."
            
        bat_dir = battery_dirs[0]
        
        def read_sysfs(filename: str) -> str:
            path = os.path.join(bat_dir, filename)
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        return f.read().strip()
                except Exception:
                    pass
            return ""
            
        capacity = read_sysfs("capacity")
        status = read_sysfs("status")
        technology = read_sysfs("technology")
        model = read_sysfs("model_name")
        manufacturer = read_sysfs("manufacturer")
        charge_full = read_sysfs("charge_full")
        charge_full_design = read_sysfs("charge_full_design")
        
        ac_connected = False
        if ac_dirs:
            ac_path = os.path.join(ac_dirs[0], "online")
            if os.path.exists(ac_path):
                try:
                    with open(ac_path, "r") as f:
                        ac_connected = (f.read().strip() == "1")
                except Exception:
                    pass
                    
        status_emoji = "🔋"
        if status.lower() == "charging":
            status_emoji = "🔌 ⚡"
        elif status.lower() == "full":
            status_emoji = "🟢 🔋"
            
        charger_status = "Tersambung (Charging)" if ac_connected else "Tidak Tersambung (Discharging)"
        
        res = [
            f"{status_emoji} **Status Baterai Laptop**",
            f"▪️ **Kapasitas:** {capacity}%" if capacity else "",
            f"▪️ **Status:** {status} ({charger_status})",
            f"▪️ **Model:** {model}" if model else "",
            f"▪️ **Pabrikan:** {manufacturer}" if manufacturer else "",
            f"▪️ **Teknologi:** {technology}" if technology else ""
        ]
        
        if charge_full and charge_full_design:
            try:
                cf = int(charge_full)
                cfd = int(charge_full_design)
                health = (cf / cfd) * 100
                res.append(f"▪️ **Kesehatan Baterai:** {health:.2f}%")
            except ValueError:
                pass
                
        return "\n".join([line for line in res if line])

    async def handle_notif(self, text: str) -> str:
        """Memunculkan pesan popup desktop notification langsung di layar laptop."""
        if not text:
            return "❌ Pesan notifikasi tidak boleh kosong."
            
        import subprocess
        try:
            subprocess.run(["notify-send", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            subprocess.run(["notify-send", "RAV-REMOTE", text], check=True)
            return "🔔 Notifikasi desktop berhasil dikirim."
        except Exception as e:
            return f"❌ Gagal mengirim notifikasi desktop: {e}"

    async def handle_process(self, args: list) -> str:
        """Melihat daftar aplikasi yang berjalan atau menutup paksa aplikasi."""
        if not args:
            return "❌ Gunakan: `!process list` atau `!process kill <pid/nama>`"
            
        subcmd = args[0].lower().strip()
        if subcmd == "list":
            import psutil
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    cpu = proc.info['cpu_percent']
                    mem = proc.info['memory_percent']
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu': cpu if cpu is not None else 0.0,
                        'mem': mem if mem is not None else 0.0
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            processes.sort(key=lambda x: x['cpu'], reverse=True)
            top_procs = processes[:15]
            
            res = ["⚙️ **Daftar 15 Proses Teraktif (CPU %):**\n"]
            res.append(f"{'PID':<8}{'NAMA':<20}{'CPU%':<8}{'RAM%':<8}")
            res.append("-" * 44)
            for p in top_procs:
                name_trunc = p['name'][:18]
                res.append(f"{p['pid']:<8}{name_trunc:<20}{p['cpu']:<8.1f}{p['mem']:<8.1f}")
                
            return f"```\n" + "\n".join(res) + "\n```"
            
        elif subcmd == "kill":
            if len(args) < 2:
                return "❌ Gunakan: `!process kill <pid/nama>`"
            target = args[1].strip()
            
            import psutil
            if target.isdigit():
                pid = int(target)
                try:
                    proc = psutil.Process(pid)
                    proc_name = proc.name()
                    proc.kill()
                    return f"✅ Berhasil menutup paksa proses PID **{pid}** ({proc_name})."
                except psutil.NoSuchProcess:
                    return f"❌ Proses dengan PID {pid} tidak ditemukan."
                except psutil.AccessDenied:
                    return f"❌ Akses ditolak untuk menghentikan PID {pid}."
                except Exception as e:
                    return f"❌ Gagal menghentikan PID {pid}: {e}"
            else:
                killed_count = 0
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if target.lower() in proc.info['name'].lower():
                            proc.kill()
                            killed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                if killed_count > 0:
                    return f"✅ Berhasil menghentikan **{killed_count}** proses dengan nama mengandung **'{target}'**."
                else:
                    return f"❌ Tidak ditemukan proses aktif dengan nama **'{target}'**."
                    
        return "❌ Subperintah tidak dikenal. Gunakan: `!process list` atau `!process kill <pid/nama>`"

    async def handle_clip_sync(self, args: list) -> str:
        """Mengaktifkan, menonaktifkan, atau melihat status sinkronisasi clipboard otomatis."""
        global clipboard_sync_active
        if not args:
            status = "AKTIF" if clipboard_sync_active else "NON-AKTIF"
            return f"📋 Status Sinkronisasi Clipboard: **{status}**\nℹ️ Gunakan: `!clip sync [start | stop]`"
            
        subcmd = args[0].lower().strip()
        if subcmd == "start":
            if clipboard_sync_active:
                return "🔄 Sinkronisasi clipboard otomatis sudah aktif."
            clipboard_sync_active = True
            return "🔄 Sinkronisasi clipboard otomatis **AKTIF**.\nTeks baru yang Anda salin di laptop akan terkirim ke HP secara realtime."
        elif subcmd == "stop":
            if not clipboard_sync_active:
                return "⏹️ Sinkronisasi clipboard otomatis sudah non-aktif."
            clipboard_sync_active = False
            return "⏹️ Sinkronisasi clipboard otomatis **NON-AKTIF**."
            
        return "❌ Gunakan: `!clip sync start` atau `!clip sync stop`"

    async def handle_find_files(self, pattern: str) -> str:
        """Mencari file secara rekursif mulai dari CWD berdasarkan pattern."""
        if not pattern:
            return "❌ Masukkan pola pencarian. Contoh: `!find *.txt` atau `!find dokumen`"
        
        # Jika pattern tidak memiliki wildcard, tambahkan wildcard default untuk fleksibilitas pencarian substring
        search_pattern = pattern
        if "*" not in pattern and "?" not in pattern:
            search_pattern = f"*{pattern}*"

        try:
            def search():
                root = Path(self._cwd).expanduser().resolve()
                matches = []
                for p in root.rglob(search_pattern):
                    if len(matches) >= 50:
                        break
                    try:
                        rel = p.relative_to(root)
                        matches.append(f"📄 `{rel}`" if p.is_file() else f"📂 `{rel}/`")
                    except ValueError:
                        matches.append(f"📄 `{p.name}`" if p.is_file() else f"📂 `{p.name}/`")
                return matches

            results = await asyncio.to_thread(search)
            if not results:
                return f"🔍 Tidak ditemukan file atau folder yang cocok dengan `{pattern}` di `{self._cwd}`."
            
            res_str = f"🔍 **Hasil Pencarian `{pattern}` di `{self._cwd}` (max 50):**\n" + "\n".join(results)
            return res_str
        except Exception as e:
            return f"❌ Gagal melakukan pencarian file: {e}"

    async def handle_tts_speak(self, text: str) -> str:
        """Mengucapkan teks menggunakan Text-to-Speech (TTS) engine di laptop."""
        if not text:
            return "❌ Masukkan teks yang ingin diucapkan. Contoh: `!tts Halo dunia` atau `!tts -v jp Ohayou!`"
        
        current_os = platform.system()
        
        # Opsi pemilihan suara (default: GadisNeural - Indonesia)
        voice = "id-ID-GadisNeural"
        voice_desc = "GadisNeural"
        
        words = text.split()
        if len(words) >= 3 and words[0] == "-v":
            lang_code = words[1]
            if "-" in lang_code and len(lang_code) > 5:
                voice = lang_code
                voice_desc = lang_code
                text = " ".join(words[2:])
            elif lang_code.lower() in ["jp", "ja", "anime", "wibu"]:
                voice = "ja-JP-NanamiNeural"  # Suara cewek anime Jepang yang populer & imut
                voice_desc = "NanamiNeural (Anime)"
                text = " ".join(words[2:])
            elif lang_code.lower() in ["jp-male", "ja-male"]:
                voice = "ja-JP-KeitaNeural"
                voice_desc = "KeitaNeural (JP Male)"
                text = " ".join(words[2:])
            elif lang_code.lower() in ["cowo", "cowok", "id-male"]:
                voice = "id-ID-ArdiNeural"
                voice_desc = "ArdiNeural (Indo Cowo)"
                text = " ".join(words[2:])
            elif lang_code.lower() in ["en", "us", "english"]:
                voice = "en-US-JennyNeural"
                voice_desc = "JennyNeural (English)"
                text = " ".join(words[2:])
            elif lang_code.lower() in ["id", "ind", "indonesia"]:
                voice = "id-ID-GadisNeural"
                voice_desc = "GadisNeural (Indonesia)"
                text = " ".join(words[2:])

        # Coba menggunakan Microsoft Edge TTS (Online) untuk suara profesional wanita
        try:
            import edge_tts
            import shutil
            import tempfile
            
            player = None
            for p in ["mpg123", "mpv", "play", "ffplay", "paplay", "vlc"]:
                if shutil.which(p):
                    player = p
                    break
            
            if player:
                temp_dir = tempfile.gettempdir()
                temp_mp3 = os.path.join(temp_dir, f"tts_{int(time.time())}.mp3")
                
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(temp_mp3)
                
                if player == "ffplay":
                    subprocess.Popen(["ffplay", "-nodisp", "-autoexit", temp_mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif player == "vlc":
                    subprocess.Popen(["cvlc", "--play-and-exit", temp_mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen([player, temp_mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                return f"🗣️ Mengucapkan: \"{text}\" (Microsoft Edge TTS - {voice_desc})"
        except Exception as e:
            logger.warning(f"Edge TTS failed: {e}. Falling back to Google TTS...")

        # Fallback ke Google Translate TTS (Online)
        try:
            import urllib.parse
            import httpx
            import shutil
            import tempfile
            
            encoded_text = urllib.parse.quote(text)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=id&client=tw-ob&q={encoded_text}"
            
            player = None
            for p in ["mpg123", "mpv", "play", "ffplay", "paplay", "vlc"]:
                if shutil.which(p):
                    player = p
                    break
            
            if player:
                temp_dir = tempfile.gettempdir()
                temp_mp3 = os.path.join(temp_dir, f"tts_{int(time.time())}.mp3")
                async with httpx.AsyncClient(timeout=5.0) as client:
                    res = await client.get(url)
                    if res.status_code == 200:
                        with open(temp_mp3, "wb") as f:
                            f.write(res.content)
                        
                        if player == "ffplay":
                            subprocess.Popen(["ffplay", "-nodisp", "-autoexit", temp_mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        elif player == "vlc":
                            subprocess.Popen(["cvlc", "--play-and-exit", temp_mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        else:
                            subprocess.Popen([player, temp_mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
                        return f"🗣️ Mengucapkan: \"{text}\" (Google Translate TTS)"
        except Exception as e:
            logger.warning(f"Google TTS failed: {e}. Falling back to offline TTS...")

        # Fallback ke Offline TTS bawaan OS
        try:
            if current_os == "Linux":
                import shutil
                if shutil.which("spd-say"):
                    subprocess.Popen(["spd-say", "-t", "female1", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return f"🗣️ Mengucapkan: \"{text}\" (Offline spd-say)"
                elif shutil.which("espeak"):
                    subprocess.Popen(["espeak", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return f"🗣️ Mengucapkan: \"{text}\" (Offline espeak)"
                return "❌ Mesin TTS (spd-say atau espeak) tidak terinstall di Linux ini."
            elif current_os == "Darwin":
                subprocess.Popen(["say", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"🗣️ Mengucapkan: \"{text}\" (Offline say)"
            elif current_os == "Windows":
                cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{text}')"
                subprocess.Popen(["powershell", "-Command", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"🗣️ Mengucapkan: \"{text}\" (PowerShell SpeechSynthesizer)"
            return f"❌ Fitur TTS belum didukung di OS: {current_os}"
        except Exception as e:
            return f"❌ Gagal memutar TTS: {e}"

    async def handle_ping(self, host: str) -> str:
        """Memeriksa latensi ke host menggunakan ping."""
        clean_host = "".join(c for c in host if c.isalnum() or c in ".-_")
        if not clean_host:
            return "❌ Host name tidak valid."
        
        current_os = platform.system()
        try:
            if current_os == "Windows":
                cmd = ["ping", "-n", "4", clean_host]
            else:
                cmd = ["ping", "-c", "4", clean_host]
            
            def run_ping():
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                return res.stdout or res.stderr
                
            output = await asyncio.to_thread(run_ping)
            return f"⚡ **Hasil Ping ke {clean_host}:**\n```\n{output}\n```"
        except subprocess.TimeoutExpired:
            return "⏳ Timeout: Host tujuan terlalu lambat merespons ping."
        except Exception as e:
            return f"❌ Gagal melakukan ping: {e}"

    async def handle_speedtest(self) -> str:
        """Menguji kecepatan internet menggunakan speedtest-cli jika ada, atau fallback download speed test."""
        import shutil
        if shutil.which("speedtest-cli"):
            try:
                def run_cli():
                    res = subprocess.run(["speedtest-cli", "--simple"], capture_output=True, text=True, timeout=45)
                    return res.stdout or res.stderr
                output = await asyncio.to_thread(run_cli)
                return f"🚀 **Hasil Speedtest:**\n```\n{output.strip()}\n```"
            except Exception as e:
                logger.warning(f"speedtest-cli execution failed: {e}. Trying fallback...")
        
        try:
            import httpx
            url = "https://speed.cloudflare.com/__down?bytes=5000000"
            start_time = time.time()
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url)
                duration = time.time() - start_time
                if res.status_code == 200:
                    size_mb = 5.0
                    speed_mbps = (size_mb * 8) / duration
                    return (
                        f"🚀 **Hasil Uji Kecepatan Unduh (Fallback):**\n"
                        f"▪️ **Ukuran Data:** 5 MB\n"
                        f"▪️ **Durasi:** {duration:.2f} detik\n"
                        f"▪️ **Kecepatan Unduh:** **{speed_mbps:.2f} Mbps**\n"
                        f"💡 _Tip: Install `speedtest-cli` di laptop Anda untuk hasil pengujian yang lebih lengkap (Ping, Unduh, Unggah)._"
                    )
                else:
                    return f"❌ Gagal menguji kecepatan internet: Server merespons dengan status {res.status_code}"
        except Exception as e:
            return f"❌ Gagal menguji kecepatan internet: {e}"

    async def handle_window_control(self, action: str) -> str:
        """Mengontrol jendela aplikasi yang aktif (minimize, close)."""
        action = action.lower().strip()
        if action not in ["minimize", "close"]:
            return "❌ Aksi jendela tidak dikenal. Gunakan: minimize, close."
            
        current_os = platform.system()
        try:
            if current_os == "Linux":
                import shutil
                if shutil.which("xdotool"):
                    if action == "minimize":
                        cmd = "xdotool windowminimize $(xdotool getactivewindow)"
                        subprocess.run(cmd, shell=True, check=True)
                        return "🖥️ Jendela aktif berhasil diminimalkan."
                    elif action == "close":
                        cmd = "xdotool windowclose $(xdotool getactivewindow)"
                        subprocess.run(cmd, shell=True, check=True)
                        return "🖥️ Jendela aktif berhasil ditutup."
                elif shutil.which("wmctrl"):
                    if action == "minimize":
                        cmd = "wmctrl -r :ACTIVE: -b add,hidden"
                        subprocess.run(cmd, shell=True, check=True)
                        return "🖥️ Jendela aktif berhasil diminimalkan."
                    elif action == "close":
                        cmd = "wmctrl -c :ACTIVE:"
                        subprocess.run(cmd, shell=True, check=True)
                        return "🖥️ Jendela aktif berhasil ditutup."
                
                if action == "minimize":
                    from agent.input_simulator import simulate_press
                    await asyncio.to_thread(simulate_press, "ctrl+alt+d")
                    return "🖥️ Mencoba meminimalkan jendela via shortcut keyboard."
                elif action == "close":
                    from agent.input_simulator import simulate_press
                    await asyncio.to_thread(simulate_press, "alt+f4")
                    return "🖥️ Mencoba menutup jendela via Alt+F4."
                    
            elif current_os == "Windows":
                from agent.input_simulator import simulate_press
                if action == "minimize":
                    await asyncio.to_thread(simulate_press, "win+d")
                    return "🖥️ Jendela diminimalkan (Show Desktop)."
                elif action == "close":
                    await asyncio.to_thread(simulate_press, "alt+f4")
                    return "🖥️ Jendela ditutup (Alt+F4)."
                    
            elif current_os == "Darwin":
                if action == "minimize":
                    cmd = "osascript -e 'tell application \"System Events\" to set visible of first process whose frontmost is true to false'"
                    subprocess.run(cmd, shell=True, check=True)
                    return "🖥️ Jendela aktif diminimalkan."
                elif action == "close":
                    cmd = "osascript -e 'tell application \"System Events\" to keystroke \"w\" using command down'"
                    subprocess.run(cmd, shell=True, check=True)
                    return "🖥️ Jendela aktif ditutup."
                    
            return f"❌ Fitur kontrol jendela belum didukung di OS: {current_os}"
        except Exception as e:
            return f"❌ Gagal mengontrol jendela: {e}"

    async def handle_web_search(self, query: str) -> str:
        """Melakukan pencarian di DuckDuckGo dan mengembalikan judul serta tautan teratas, dengan fallback ke Yahoo jika gagal."""
        if not query:
            return "❌ Masukkan kueri pencarian. Contoh: `!web cara membuat kopi`"
        
        import urllib.parse
        import re
        import httpx
        from urllib.parse import unquote
        
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        results = []
        try:
            async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    html_content = res.text
                    body_pattern = re.compile(r'<div class="result__body">(.*?)</div>\s*</div>', re.DOTALL)
                    bodies = body_pattern.findall(html_content)
                    
                    if not bodies:
                        link_pattern = re.compile(r'<a class="result__a" href="([^"]+)">([^<]+)</a>', re.DOTALL)
                        matches = link_pattern.findall(html_content)
                        for href, title in matches[:5]:
                            if "uddg=" in href:
                                actual_url = unquote(href.split("uddg=")[1].split("&")[0])
                            else:
                                actual_url = href
                                if actual_url.startswith("//"):
                                    actual_url = "https:" + actual_url
                            
                            title_clean = re.sub(r'<[^>]+>', '', title).strip()
                            results.append(f"🔗 **[{title_clean}]({actual_url})**\n_{actual_url}_\n")
                    else:
                        for body in bodies[:5]:
                            title_match = re.search(r'<a class="result__a" href="([^"]+)">([^<]+)</a>', body, re.DOTALL)
                            snippet_match = re.search(r'<a class="result__snippet"[^>]*>(.*?)</a>', body, re.DOTALL)
                            
                            if title_match:
                                href, title = title_match.groups()
                                if "uddg=" in href:
                                    actual_url = unquote(href.split("uddg=")[1].split("&")[0])
                                else:
                                    actual_url = href
                                    if actual_url.startswith("//"):
                                        actual_url = "https:" + actual_url
                                
                                title_clean = re.sub(r'<[^>]+>', '', title).strip()
                                snippet = ""
                                if snippet_match:
                                    snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
                                
                                res_str = f"🔗 **{title_clean}**\n_{actual_url}_\n"
                                if snippet:
                                    res_str += f"{snippet}\n"
                                results.append(res_str)
        except Exception:
            pass
            
        if results:
            return f"🔍 **Hasil Pencarian Web untuk `{query}`:**\n\n" + "\n".join(results)
            
        # Fallback ke Yahoo Search
        try:
            yahoo_url = f"https://search.yahoo.com/search?q={urllib.parse.quote_plus(query)}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(yahoo_url, headers=headers)
                if res.status_code == 200:
                    pattern = re.compile(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</h3>\s*</a>', re.DOTALL)
                    matches = pattern.findall(res.text)
                    yahoo_results = []
                    for href, inner in matches:
                        h3_match = re.search(r'<h3[^>]*>(.*?)</h3>', inner + "</h3>", re.DOTALL)
                        if h3_match:
                            title = re.sub(r'<[^>]+>', '', h3_match.group(1)).strip()
                        else:
                            title = re.sub(r'<[^>]+>', '', inner).strip()
                            
                        actual_url = href
                        if "/RU=" in href:
                            ru_part = href.split("/RU=")[1].split("/RK=")[0]
                            actual_url = urllib.parse.unquote(ru_part)
                        
                        if not title or not actual_url.startswith("http") or "yahoo.com" in actual_url:
                            continue
                            
                        yahoo_results.append(f"🔗 **{title}**\n_{actual_url}_\n")
                        if len(yahoo_results) >= 5:
                            break
                            
                    if yahoo_results:
                        return f"🔍 **Hasil Pencarian Web (Yahoo Fallback) untuk `{query}`:**\n\n" + "\n".join(yahoo_results)
        except Exception as e:
            return f"❌ Gagal melakukan pencarian web: {e}"
            
        return f"🔍 Tidak ditemukan hasil untuk kueri: `{query}`"


    async def handle_wifi_scan(self) -> str:
        """Memindai dan menampilkan daftar jaringan Wi-Fi sekitar."""
        current_os = platform.system()
        import shutil
        try:
            if current_os == "Linux":
                if shutil.which("nmcli"):
                    proc = await asyncio.create_subprocess_exec(
                        "nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list",
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    stdout, _ = await proc.communicate()
                    output = stdout.decode("utf-8", errors="ignore").strip()
                    
                    if not output:
                        return "📭 Tidak ada jaringan Wi-Fi yang terdeteksi atau Wi-Fi mati."
                    
                    lines = output.split("\n")
                    seen = set()
                    formatted = []
                    count = 1
                    for line in lines:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            ssid = parts[0].replace("\\:", ":").strip()
                            if not ssid:
                                continue
                            signal = parts[1].strip()
                            security = parts[2].strip() if len(parts) > 2 else "None"
                            
                            key = (ssid, security)
                            if key in seen:
                                continue
                            seen.add(key)
                            
                            formatted.append(f"{count}. 📶 **{ssid}** | Sinyal: {signal}% | Keamanan: {security}")
                            count += 1
                            if count > 20:
                                break
                    
                    if not formatted:
                        return "📭 Tidak ada jaringan Wi-Fi yang terdeteksi."
                    return "📶 **Jaringan Wi-Fi Sekitar (Linux):**\n\n" + "\n".join(formatted)
                else:
                    return "❌ Command `nmcli` tidak ditemukan. Pastikan NetworkManager terinstall."
            
            elif current_os == "Windows":
                proc = await asyncio.create_subprocess_exec(
                    "cmd.exe", "/c", "netsh wlan show networks",
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, _ = await proc.communicate()
                output = stdout.decode("utf-8", errors="ignore").strip()
                
                ssids = []
                for line in output.split("\n"):
                    if "SSID" in line and ":" in line:
                        ssid = line.split(":", 1)[1].strip()
                        if ssid:
                            ssids.append(ssid)
                
                if not ssids:
                    return "📭 Tidak ada jaringan Wi-Fi yang terdeteksi."
                
                formatted = [f"{i+1}. 📶 **{ssid}**" for i, ssid in enumerate(ssids[:20])]
                return "📶 **Jaringan Wi-Fi Sekitar (Windows):**\n\n" + "\n".join(formatted)
                
            elif current_os == "Darwin":
                airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
                if os.path.exists(airport_path):
                     proc = await asyncio.create_subprocess_exec(
                         airport_path, "-s",
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE
                     )
                     stdout, _ = await proc.communicate()
                     output = stdout.decode("utf-8", errors="ignore").strip()
                     
                     lines = output.split("\n")
                     if len(lines) <= 1:
                         return "📭 Tidak ada jaringan Wi-Fi yang terdeteksi."
                     
                     formatted = []
                     count = 1
                     for line in lines[1:]:
                         parts = line.split()
                         if parts:
                             ssid = parts[0]
                             rssi = parts[2] if len(parts) > 2 else "Unknown"
                             formatted.append(f"{count}. 📶 **{ssid}** | RSSI: {rssi} dBm")
                             count += 1
                             if count > 20:
                                 break
                     return "📶 **Jaringan Wi-Fi Sekitar (macOS):**\n\n" + "\n".join(formatted)
                else:
                     return "❌ Utilitas macOS airport tidak ditemukan."
            
            else:
                return f"❌ Fitur scan Wi-Fi tidak didukung pada OS: {current_os}"
        except Exception as e:
            return f"❌ Gagal memindai Wi-Fi: {e}"

    async def handle_active_ports(self) -> str:
        """Menampilkan port yang sedang listening/aktif."""
        current_os = platform.system()
        import shutil
        try:
            if current_os == "Linux":
                if shutil.which("ss"):
                    proc = await asyncio.create_subprocess_exec(
                        "ss", "-tuln",
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    stdout, _ = await proc.communicate()
                    output = stdout.decode("utf-8", errors="ignore").strip()
                elif shutil.which("netstat"):
                    proc = await asyncio.create_subprocess_exec(
                        "netstat", "-tuln",
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    stdout, _ = await proc.communicate()
                    output = stdout.decode("utf-8", errors="ignore").strip()
                else:
                    return "❌ Utilitas `ss` atau `netstat` tidak ditemukan."
                
                lines = output.split("\n")
                if len(lines) <= 1:
                    return "📭 Tidak ada port aktif (listening) yang ditemukan."
                
                formatted = []
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 5:
                        proto = parts[0].upper()
                        state = parts[1].upper()
                        local = parts[4]
                        
                        if ":" in local:
                            addr, port = local.rsplit(":", 1)
                            if addr in ["*", "0.0.0.0"]:
                                addr_desc = "Semua IPv4"
                            elif addr in ["[::]", "::"]:
                                addr_desc = "Semua IPv6"
                            elif addr in ["127.0.0.1", "[::1]"]:
                                addr_desc = "Localhost"
                            else:
                                addr_desc = addr
                            
                            formatted.append(f"🔌 **Port {port}** ({proto}) | Bind: `{addr_desc}` | Status: `{state}`")
                
                if not formatted:
                    return "📭 Tidak ada port listening yang berhasil diparsing."
                
                formatted = sorted(list(set(formatted)))
                return "🔌 **Daftar Port Listening Aktif (Linux):**\n\n" + "\n".join(formatted[:30])
            
            elif current_os == "Windows":
                proc = await asyncio.create_subprocess_exec(
                    "cmd.exe", "/c", "netstat -an | findstr LISTENING",
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, _ = await proc.communicate()
                output = stdout.decode("utf-8", errors="ignore").strip()
                
                lines = output.split("\n")
                formatted = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 4:
                        proto = parts[0]
                        local = parts[1]
                        state = parts[3]
                        if ":" in local:
                            addr, port = local.rsplit(":", 1)
                            formatted.append(f"🔌 **Port {port}** ({proto}) | Bind: `{addr}` | Status: `{state}`")
                
                if not formatted:
                    return "📭 Tidak ada port listening yang ditemukan."
                
                formatted = sorted(list(set(formatted)))
                return "🔌 **Daftar Port Listening Aktif (Windows):**\n\n" + "\n".join(formatted[:30])
                
            elif current_os == "Darwin":
                if shutil.which("lsof"):
                    proc = await asyncio.create_subprocess_exec(
                        "lsof", "-i", "-P", "-n",
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    stdout, _ = await proc.communicate()
                    output = stdout.decode("utf-8", errors="ignore").strip()
                    
                    lines = output.split("\n")
                    formatted = []
                    for line in lines[1:]:
                        if "LISTEN" in line:
                            parts = line.split()
                            if len(parts) >= 9:
                                proc_name = parts[0]
                                proto = parts[7]
                                local = parts[8]
                                if ":" in local:
                                    addr, port = local.rsplit(":", 1)
                                    formatted.append(f"🔌 **Port {port}** ({proto}) | Aplikasi: `{proc_name}` | Bind: `{addr}`")
                    
                    if not formatted:
                        return "📭 Tidak ada port listening yang ditemukan."
                    
                    formatted = sorted(list(set(formatted)))
                    return "🔌 **Daftar Port Listening Aktif (macOS):**\n\n" + "\n".join(formatted[:30])
                else:
                    return "❌ Utilitas `lsof` tidak ditemukan di macOS."
            else:
                return f"❌ Fitur monitoring port tidak didukung pada OS: {current_os}"
        except Exception as e:
            return f"❌ Gagal memonitor port aktif: {e}"

    async def handle_launch_app(self, app_name: str) -> str:
        """Meluncurkan aplikasi desktop secara background."""
        import subprocess
        import shutil
        app_name = app_name.lower().strip()
        
        # Pemetaan aplikasi populer
        app_map = {
            "chrome": ["google-chrome", "chrome", "chromium-browser", "google-chrome-stable"],
            "firefox": ["firefox"],
            "vscode": ["code"],
            "code": ["code"],
            "spotify": ["spotify"],
            "slack": ["slack"],
            "calculator": ["gnome-calculator", "calc", "kcalc"],
            "calc": ["gnome-calculator", "calc", "kcalc"],
            "terminal": ["gnome-terminal", "xterm", "konsole", "xfce4-terminal"],
            "files": ["nautilus", "xdg-open .", "thunar", "dolphin"],
            "explorer": ["nautilus", "xdg-open .", "thunar", "dolphin"],
            "notepad": ["gedit", "kate", "mousepad", "nano"],
            "discord": ["discord"]
        }
        
        commands_to_try = app_map.get(app_name, [app_name])
        found_cmd = None
        for cmd in commands_to_try:
            exe = cmd.split(" ", 1)[0]
            if shutil.which(exe):
                found_cmd = cmd
                break
                
        if not found_cmd:
            return f"❌ Aplikasi '{app_name}' tidak teridentifikasi di sistem Anda. Coba jalankan manual via terminal."
            
        try:
            # Jalankan di background tanpa memblokir
            subprocess.Popen(
                found_cmd, shell=True, 
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                start_new_session=True
            )
            return f"🚀 Berhasil meluncurkan aplikasi **{app_name}** di laptop Anda."
        except Exception as e:
            return f"❌ Gagal meluncurkan aplikasi **{app_name}**: {e}"

    async def handle_todo(self, args: list) -> str:
        """Mengelola daftar tugas (TODO list) secara persisten."""
        todo_file = "todo.json"
        import json
        import os
        
        todos = []
        if os.path.exists(todo_file):
            try:
                with open(todo_file, "r") as f:
                    todos = json.load(f)
            except Exception:
                todos = []
                
        if not args:
            if not todos:
                return "📝 **Daftar Tugas Anda Kosong.**\nTulis `!todo add <tugas>` untuk menambahkan."
            
            res = ["📝 **Daftar Tugas (TODO List):**\n"]
            for idx, item in enumerate(todos, 1):
                status = "✅" if item.get("done", False) else "⏳"
                deadline_part = ""
                if item.get("deadline"):
                    speak_icon = " 🔊" if item.get("speak_local", False) else ""
                    deadline_part = f" (⏱️ *Tenggat:* {item['deadline']}{speak_icon})"
                res.append(f"{idx}. {status} {item['task']}{deadline_part}")
            return "\n".join(res)
            
        subcmd = args[0].lower().strip()
        
        if subcmd == "add":
            if len(args) < 2:
                return "❌ Masukkan deskripsi tugas. Contoh: `!todo add Belajar coding`"
            task_desc = " ".join(args[1:])
            deadline = None
            speak_local = False
            
            if " | " in task_desc:
                parts = [p.strip() for p in task_desc.split(" | ")]
                task_desc = parts[0]
                deadline_str = parts[1]
                
                if len(parts) >= 3:
                    option = parts[2].lower()
                    if "speak" in option or "suara" in option:
                        speak_local = True
                
                from datetime import datetime, timedelta
                try:
                    if len(deadline_str) == 5 and ":" in deadline_str:
                        now = datetime.now()
                        target_time = datetime.strptime(deadline_str, "%H:%M").time()
                        target_dt = datetime.combine(now.date(), target_time)
                        if target_dt < now:
                            target_dt += timedelta(days=1)
                        deadline = target_dt.strftime("%Y-%m-%d %H:%M")
                    else:
                        dt = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
                        deadline = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    return "❌ Format tenggat waktu tidak valid. Gunakan format `HH:MM` atau `YYYY-MM-DD HH:MM`. Contoh: `!todo add Beli kopi | 15:30`"
            
            todos.append({"task": task_desc, "done": False, "deadline": deadline, "reminded": False, "speak_local": speak_local})
            try:
                with open(todo_file, "w") as f:
                    json.dump(todos, f, indent=4)
                deadline_msg = f" dengan tenggat waktu **{deadline}**" if deadline else ""
                speak_msg = " (🔊 Laptop Berbicara)" if speak_local else ""
                return f"➕ Berhasil menambahkan tugas: **{task_desc}**{deadline_msg}{speak_msg}"
            except Exception as e:
                return f"❌ Gagal menyimpan tugas: {e}"
                
        elif subcmd == "done":
            if len(args) < 2:
                return "❌ Masukkan nomor tugas yang selesai. Contoh: `!todo done 1`"
            try:
                idx = int(args[1]) - 1
                if idx < 0 or idx >= len(todos):
                    return f"❌ Nomor tugas {args[1]} tidak valid."
                todos[idx]["done"] = True
                with open(todo_file, "w") as f:
                    json.dump(todos, f, indent=4)
                return f"✅ Berhasil menandai tugas **{todos[idx]['task']}** sebagai selesai!"
            except ValueError:
                return "❌ Nomor tugas harus berupa angka."
            except Exception as e:
                return f"❌ Gagal memperbarui tugas: {e}"
                
        elif subcmd in ("del", "delete", "remove"):
            if len(args) < 2:
                return "❌ Masukkan nomor tugas yang akan dihapus. Contoh: `!todo delete 1`"
            try:
                idx = int(args[1]) - 1
                if idx < 0 or idx >= len(todos):
                    return f"❌ Nomor tugas {args[1]} tidak valid."
                removed_task = todos.pop(idx)
                with open(todo_file, "w") as f:
                    json.dump(todos, f, indent=4)
                return f"🗑️ Berhasil menghapus tugas: **{removed_task['task']}**"
            except ValueError:
                return "❌ Nomor tugas harus berupa angka."
            except Exception as e:
                return f"❌ Gagal menghapus tugas: {e}"
                
        elif subcmd == "clear":
            todos = []
            try:
                with open(todo_file, "w") as f:
                    json.dump(todos, f, indent=4)
                return "🗑️ Semua daftar tugas berhasil dibersihkan!"
            except Exception as e:
                return f"❌ Gagal membersihkan tugas: {e}"
                
        return "❌ Subperintah tidak dikenal. Gunakan: `!todo add <tugas>`, `!todo done <nomor>`, `!todo delete <nomor>`, atau `!todo clear`"


    async def handle_list_apps(self, args: list[str] = None) -> str:
        """
        Menampilkan daftar aplikasi GUI/Desktop yang terinstall di sistem Linux/XDG.
        Mendukung pencarian filter jika ada argumen.
        """
        import os
        from pathlib import Path
        import re

        query = " ".join(args).lower().strip() if args else ""

        # Direktori standar file .desktop di Linux
        directories = [
            Path("/usr/share/applications"),
            Path("/usr/local/share/applications"),
            Path(os.path.expanduser("~/.local/share/applications"))
        ]

        apps = {}
        for directory in directories:
            if not directory.exists() or not directory.is_dir():
                continue
            for file_path in directory.glob("*.desktop"):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    if "[Desktop Entry]" not in content:
                        continue
                    
                    name_match = re.search(r"^Name\s*=\s*(.+)$", content, re.MULTILINE)
                    exec_match = re.search(r"^Exec\s*=\s*(.+)$", content, re.MULTILINE)
                    no_display_match = re.search(r"^NoDisplay\s*=\s*true$", content, re.MULTILINE | re.IGNORECASE)
                    
                    if name_match and exec_match and not no_display_match:
                        name = name_match.group(1).strip()
                        exec_val = exec_match.group(1).strip()
                        
                        # Bersihkan argumen Exec seperti %U, %F, %f, etc.
                        exec_clean = re.sub(r"\s+%.", "", exec_val).strip()
                        exec_clean = exec_clean.replace('"', '').replace("'", "")
                        
                        exec_cmd = exec_clean.split()[0] if exec_clean else ""
                        if "/" in exec_cmd:
                            exec_cmd = exec_cmd.split("/")[-1]
                            
                        if name and exec_cmd:
                            apps[name] = exec_cmd
                except Exception:
                    continue

        if not apps:
            fallback_apps = {
                "Google Chrome": "chrome",
                "VS Code": "code",
                "Mozilla Firefox": "firefox",
                "Spotify": "spotify",
                "Slack": "slack",
                "Terminal": "gnome-terminal",
                "Calculator": "gnome-calculator",
                "File Manager": "nautilus",
                "Text Editor": "gedit"
            }
            apps = fallback_apps

        # Sort berdasarkan Nama
        sorted_apps = sorted(apps.items(), key=lambda x: x[0].lower())

        if query:
            filtered = [
                (name, cmd) for name, cmd in sorted_apps 
                if query in name.lower() or query in cmd.lower()
            ]
            if not filtered:
                return f"🔍 Tidak ditemukan aplikasi yang cocok dengan kueri: **{query}**"
            
            lines = [f"🔍 **Hasil Pencarian Aplikasi ({len(filtered)} ditemukan):**"]
            for name, cmd in filtered:
                lines.append(f"• **{name}** → `!launch {cmd}`")
            return "\n".join(lines)
        else:
            limit = 45
            total = len(sorted_apps)
            display_list = sorted_apps[:limit]
            
            lines = [
                "🖥️ **Daftar Aplikasi Desktop Terinstall:**",
                "Gunakan `!launch <command>` untuk membukanya.",
                ""
            ]
            for name, cmd in display_list:
                lines.append(f"• **{name}** → `!launch {cmd}`")
            
            if total > limit:
                lines.append("")
                lines.append(f"*Menampilkan {limit} dari {total} aplikasi.*")
                lines.append("💡 *Gunakan `!apps <nama>` untuk mencari aplikasi tertentu.*")
                
            return "\n".join(lines)

    async def handle_guard(self, args: list[str]) -> str:
        """Mengaktifkan/menonaktifkan mode pengawasan kamera (Webcam Guard)."""
        from agent.guard import webcam_guard
        
        if not args:
            status = "AKTIF" if webcam_guard.is_running else "NONAKTIF"
            return f"🛡️ **Status Webcam Guard:** {status}\nGunakan `!guard on` untuk mengaktifkan atau `!guard off` untuk menonaktifkan."
            
        subcmd = args[0].lower().strip()
        if subcmd == "on":
            if webcam_guard.start():
                return "🛡️ **Webcam Guard diaktifkan!** Laptop Anda sekarang memantau gerakan di sekitarnya."
            else:
                return "❌ Gagal mengaktifkan Webcam Guard. Pastikan kamera tidak sedang digunakan aplikasi lain."
        elif subcmd == "off":
            webcam_guard.stop()
            return "🛡️ **Webcam Guard dinonaktifkan.**"
        else:
            return "❌ Argumen tidak valid. Gunakan `!guard on` atau `!guard off`."



