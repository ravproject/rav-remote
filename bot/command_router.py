"""
Command Router
"""
from ai_module.nim_client import CommandInterpreter
from agent.command_handler import CommandHandler
from security.audit_logger import AuditLogger
from security.sanitizer import InputSanitizer
from pathlib import Path
import base64
from loguru import logger

class CommandRouter:
    def __init__(self):
        self.interpreter = CommandInterpreter()
        self.handler = CommandHandler()
        self.auditor = AuditLogger()

    async def route(self, message_text: str, user_id: str):
        command_name, args = await self.interpreter.interpret(message_text)

        if not command_name:
            if args and args[0].startswith("__NIM_CHAT__:"):
                return args[0].split(":", 1)[1]
            elif args and args[0].startswith("__NIM_BLOCKED__:"):
                return "⚠️ Akses Ditolak: " + args[0].split(":", 1)[1]
            elif args and args[0].startswith("__NIM_ERROR__:"):
                return "🤖 AI Error: " + args[0].split(":", 1)[1]
            # Cek custom alias sebelum mengembalikan unknown
            if message_text.startswith("!"):
                try:
                    from agent.custom_aliases import alias_manager
                    alias_name = message_text.split()[0][1:].lower()
                    alias_cmd = alias_manager.get(alias_name)
                    if alias_cmd:
                        logger.info(f"Alias resolved: {alias_name} -> {alias_cmd}")
                        return await self.route(alias_cmd, user_id)
                except Exception:
                    pass
            return "❓ Perintah tidak dikenali. Ketik `!help` untuk bantuan."

        # Whitelist validation
        is_valid, _ = InputSanitizer.validate_command_whitelist(f"!{command_name}")
        if not is_valid:
            return f"❌ Perintah `{command_name}` tidak ada dalam whitelist keamanan."

        try:
            if command_name == "screenshot":
                use_grid = len(args) > 0 and args[0].lower() == "grid"
                res = await self.handler.handle_screenshot(grid=use_grid)
                self.auditor.log_event(user_id, "SCREENSHOT", "grid" if use_grid else "")
                if isinstance(res, bytes):
                    return {"type": "photo", "data": res}
                return res # Return error message string

            elif command_name == "video":
                duration = 5
                if args and args[0].isdigit():
                    duration = min(int(args[0]), 30) # Max 30s for smoothness
                res = await self.handler.handle_video(duration)
                self.auditor.log_event(user_id, "VIDEO", f"duration={duration}")
                return res or "❌ Gagal merekam video."

            elif command_name == "webcam":
                res = await self.handler.handle_webcam()
                self.auditor.log_event(user_id, "WEBCAM", "")
                if isinstance(res, bytes):
                    return {"type": "photo", "data": res}
                return res or "❌ Gagal mengambil foto webcam (kamera digunakan atau tidak ada)."

            elif command_name == "webcamvid":
                duration = int(args[0]) if args and args[0].isdigit() else 5
                res = await self.handler.handle_webcam_video(duration)
                self.auditor.log_event(user_id, "WEBCAM_VIDEO", f"duration={duration}")
                if isinstance(res, bytes):
                    return {"type": "video", "data": res}
                return res or "❌ Gagal merekam video webcam."

            elif command_name == "sysinfo":
                info = await self.handler.handle_sysinfo()
                self.auditor.log_event(user_id, "SYSINFO", "")
                return info

            elif command_name == "cd":
                if not args:
                    return f"📂 Direktori saat ini: `{self.handler.get_cwd()}`"
                result = self.handler.set_cwd(args[0])
                self.auditor.log_event(user_id, "CD", args[0][:50])
                return result

            elif command_name == "list_files":
                path = args[0] if args else "."
                result = await self.handler.handle_list_files(path)
                self.auditor.log_event(user_id, "LIST_FILES", path[:50])
                return result

            elif command_name == "get_file":
                if not args:
                    return "❌ Gunakan: !get <filepath>"
                file_data = await self.handler.handle_get_file(args[0])
                if "error" in file_data:
                    return f"❌ {file_data['error']}"
                self.auditor.log_event(user_id, "GET_FILE", args[0][:50])
                return file_data

            elif command_name == "lock_screen":
                result = await self.handler.handle_lock_screen()
                self.auditor.log_event(user_id, "LOCK_SCREEN", "")
                return result

            elif command_name == "unlock":
                password = args[0] if args else None
                result = await self.handler.handle_unlock_screen(password)
                # Password will be masked in audit logger separately
                self.auditor.log_event(user_id, "UNLOCK", "")
                return result

            elif command_name == "reboot":
                confirmed = len(args) > 0 and args[0] == "confirm"
                result = await self.handler.handle_reboot(confirmed)
                self.auditor.log_event(user_id, "REBOOT", f"confirmed={confirmed}")
                return result

            elif command_name == "testai":
                result = await self.handler.handle_test_ai()
                return result

            elif command_name == "clip":
                if args and args[0] == "read":
                    result = await self.handler.handle_clip_read()
                elif args and args[0] == "write":
                    result = await self.handler.handle_clip_write(" ".join(args[1:]))
                elif args and args[0] == "sync":
                    result = await self.handler.handle_clip_sync(args[1:])
                else:
                    return "❌ Gunakan: !clip read, !clip write <teks>, atau !clip sync [start | stop]"
                self.auditor.log_event(user_id, "CLIPBOARD", " ".join(args)[:50])
                return result

            elif command_name == "open":
                if not args: return "❌ Gunakan: !open <url>"
                result = await self.handler.handle_open_url(args[0])
                self.auditor.log_event(user_id, "OPEN_URL", args[0][:50])
                return result

            elif command_name == "top":
                result = await self.handler.handle_top()
                self.auditor.log_event(user_id, "TOP", "")
                return result

            elif command_name == "kill":
                if not args or not args[0].isdigit(): return "❌ Gunakan: !kill <pid>"
                result = await self.handler.handle_kill(int(args[0]))
                self.auditor.log_event(user_id, "KILL", args[0])
                return result

            elif command_name in ["mute", "alarm"]:
                value = args[0] if args else None
                result = await self.handler.handle_audio_control(command_name, value)
                self.auditor.log_event(user_id, f"AUDIO_{command_name.upper()}", str(value))
                return result

            elif command_name in ["agy", "opencode"]:
                result = await self.handler.handle_ai_cli(command_name, args)
                self.auditor.log_event(user_id, f"AI_CLI_{command_name.upper()}", " ".join(args)[:50])
                return result

            elif command_name == "run_script":
                if not args:
                    return "❌ Gunakan: !run <nama_script.py>"
                result = await self.handler.handle_run_script(args[0], user_id)
                self.auditor.log_event(user_id, "RUN_SCRIPT", args[0][:50])
                return result

            elif command_name == "logout":
                # Note: Actual session cleanup is handled by slash command /logout 
                # in telegram_bot.py, but we provide a response for !logout here.
                return "👋 Silakan gunakan perintah `/logout` untuk keluar dari sesi secara aman."

            elif command_name == "listen":
                duration = 5
                if args and args[0].isdigit():
                    duration = min(int(args[0]), 30)
                res = await self.handler.handle_listen(duration)
                self.auditor.log_event(user_id, "LISTEN", f"duration={duration}")
                return res or "❌ Gagal merekam audio."

            elif command_name == "brightness":
                result = await self.handler.handle_brightness(args)
                self.auditor.log_event(user_id, "BRIGHTNESS", " ".join(args)[:50])
                return result

            elif command_name == "media":
                if not args:
                    return "❌ Gunakan: !media [play | pause | next | prev]"
                result = await self.handler.handle_media(args[0])
                self.auditor.log_event(user_id, "MEDIA", args[0][:50])
                return result

            elif command_name == "battery":
                result = await self.handler.handle_battery(args)
                self.auditor.log_event(user_id, "BATTERY", " ".join(args)[:50])
                return result

            elif command_name == "notif":
                result = await self.handler.handle_notif(" ".join(args))
                self.auditor.log_event(user_id, "NOTIF", " ".join(args)[:50])
                return result

            elif command_name == "process":
                result = await self.handler.handle_process(args)
                self.auditor.log_event(user_id, "PROCESS", " ".join(args)[:50])
                return result

            elif command_name == "click":
                if len(args) < 2:
                    return "❌ Gunakan: !click <x> <y>"
                try:
                    x, y = int(args[0]), int(args[1])
                except ValueError:
                    return "❌ Koordinat x dan y harus berupa angka."
                res = await self.handler.handle_click(x, y)
                self.auditor.log_event(user_id, "CLICK", f"x={x}, y={y}")
                return res

            elif command_name == "type":
                if not args:
                    return "❌ Gunakan: !type <teks>"
                text = " ".join(args)
                res = await self.handler.handle_type(text)
                self.auditor.log_event(user_id, "TYPE", text[:50])
                return res

            elif command_name == "press":
                if not args:
                    return "❌ Gunakan: !press <tombol>"
                key = args[0]
                res = await self.handler.handle_press(key)
                self.auditor.log_event(user_id, "PRESS", key)
                return res

            elif command_name == "active":
                res = await self.handler.handle_active_window()
                self.auditor.log_event(user_id, "ACTIVE_WINDOW", "")
                return res

            elif command_name == "find":
                pattern = " ".join(args) if args else ""
                res = await self.handler.handle_find_files(pattern)
                self.auditor.log_event(user_id, "FIND_FILES", pattern[:50])
                return res

            elif command_name == "tts":
                text = " ".join(args) if args else ""
                res = await self.handler.handle_tts_speak(text)
                self.auditor.log_event(user_id, "TTS_SPEAK", text[:50])
                return res

            elif command_name == "ping":
                host = args[0] if args else "8.8.8.8"
                res = await self.handler.handle_ping(host)
                self.auditor.log_event(user_id, "PING", host)
                return res

            elif command_name == "speedtest":
                res = await self.handler.handle_speedtest()
                self.auditor.log_event(user_id, "SPEEDTEST", "")
                return res

            elif command_name == "window_control":
                action = args[0] if args else "minimize"
                res = await self.handler.handle_window_control(action)
                self.auditor.log_event(user_id, "WINDOW_CONTROL", action)
                return res

            elif command_name == "web":
                query = " ".join(args) if args else ""
                res = await self.handler.handle_web_search(query)
                self.auditor.log_event(user_id, "WEB_SEARCH", query[:50])
                return res

            elif command_name == "wifi":
                res = await self.handler.handle_wifi_scan()
                self.auditor.log_event(user_id, "WIFI_SCAN", "")
                return res

            elif command_name == "ports":
                res = await self.handler.handle_active_ports()
                self.auditor.log_event(user_id, "ACTIVE_PORTS", "")
                return res

            elif command_name == "launch":
                if not args: return "❌ Gunakan: !launch <nama_aplikasi>"
                result = await self.handler.handle_launch_app(args[0])
                self.auditor.log_event(user_id, "LAUNCH_APP", args[0][:50])
                return result

            elif command_name == "todo":
                result = await self.handler.handle_todo(args)
                self.auditor.log_event(user_id, "TODO", " ".join(args)[:50])
                return result

            elif command_name == "apps":
                result = await self.handler.handle_list_apps(args)
                self.auditor.log_event(user_id, "LIST_APPS", " ".join(args)[:50])
                return result

            elif command_name == "guard":
                result = await self.handler.handle_guard(args)
                self.auditor.log_event(user_id, "WEBCAM_GUARD", " ".join(args)[:50])
                return result

            # ── PHASE 1: Core Productivity Features ──────────────────────────────

            elif command_name == "focus":
                result = await self.handler.handle_focus(args)
                self.auditor.log_event(user_id, "FOCUS", " ".join(args)[:50])
                return result

            elif command_name == "workspace":
                result = await self.handler.handle_workspace(args)
                self.auditor.log_event(user_id, "WORKSPACE", " ".join(args)[:50])
                return result

            elif command_name == "calendar":
                result = await self.handler.handle_calendar(args)
                self.auditor.log_event(user_id, "CALENDAR", " ".join(args)[:50])
                return result

            elif command_name == "quicknote":
                result = await self.handler.handle_quicknote(args)
                self.auditor.log_event(user_id, "QUICKNOTE", " ".join(args)[:50])
                return result

            elif command_name == "browser":
                result = await self.handler.handle_browser(args)
                self.auditor.log_event(user_id, "BROWSER", " ".join(args)[:50])
                return result

            elif command_name == "daily":
                result = await self.handler.handle_daily(args)
                self.auditor.log_event(user_id, "DAILY_REPORT", " ".join(args)[:50])
                return result

            elif command_name == "reminder":
                result = await self.handler.handle_reminder(args)
                self.auditor.log_event(user_id, "REMINDER", " ".join(args)[:50])
                return result

            elif command_name == "task":
                result = await self.handler.handle_task(args)
                self.auditor.log_event(user_id, "TASK", " ".join(args)[:50])
                return result

            elif command_name == "meeting":
                result = await self.handler.handle_meeting(args)
                self.auditor.log_event(user_id, "MEETING", " ".join(args)[:50])
                return result

            elif command_name == "custom":
                result = await self.handler.handle_custom(args)
                self.auditor.log_event(user_id, "CUSTOM_ALIAS", " ".join(args)[:50])
                return result

            # ── PHASE 2: AI & Automation Intelligence ──────────────────────────────

            elif command_name == "ai":
                if not args:
                    return "Gunakan: !ai [work|write|automate|summarize|research|insight] [args]"
                ai_sub = args[0].lower()
                if ai_sub == "work":
                    return await self.handler.handle_ai_work(args[1:])
                elif ai_sub == "write":
                    return await self.handler.handle_ai_write(args[1:])
                elif ai_sub == "automate":
                    return await self.handler.handle_ai_automate(args[1:])
                elif ai_sub == "summarize":
                    return await self.handler.handle_ai_summarize(args[1:])
                elif ai_sub == "research":
                    return await self.handler.handle_ai_research(args[1:])
                elif ai_sub == "insight":
                    return await self.handler.handle_ai_insight(args[1:])
                elif ai_sub == "agent":
                    return await self.handler.handle_ai_agent(args[1:])
                return "Subperintah AI tidak dikenal. Gunakan: work, write, automate, summarize, research, insight, agent"

            elif command_name == "smart_clip":
                result = await self.handler.handle_smart_clip(args)
                self.auditor.log_event(user_id, "SMART_CLIPBOARD", " ".join(args)[:50])
                return result

            elif command_name == "macro":
                result = await self.handler.handle_macro(args)
                self.auditor.log_event(user_id, "MACRO", " ".join(args)[:50])
                return result

            elif command_name == "schedule":
                result = await self.handler.handle_schedule(args)
                self.auditor.log_event(user_id, "SCHEDULE", " ".join(args)[:50])
                return result

            elif command_name == "voice_cmd":
                result = await self.handler.handle_voice_cmd(args)
                self.auditor.log_event(user_id, "VOICE_CMD", " ".join(args)[:50])
                return result

            # ── PHASE 3: File, Sync & Data Management ──────────────────────────────

            elif command_name == "sync":
                result = await self.handler.handle_sync(args)
                self.auditor.log_event(user_id, "SYNC", " ".join(args)[:50])
                return result

            elif command_name == "quick":
                result = await self.handler.handle_quick(args)
                self.auditor.log_event(user_id, "QUICK", " ".join(args)[:50])
                return result

            elif command_name == "quick_upload":
                result = await self.handler.handle_quick_upload(args)
                self.auditor.log_event(user_id, "QUICK_UPLOAD", " ".join(args)[:50])
                return result

            elif command_name == "recent":
                result = await self.handler.handle_recent(args)
                self.auditor.log_event(user_id, "RECENT", " ".join(args)[:50])
                return result

            elif command_name == "search_content":
                result = await self.handler.handle_search_content(args)
                self.auditor.log_event(user_id, "SEARCH_CONTENT", " ".join(args)[:50])
                return result

            elif command_name == "convert":
                result = await self.handler.handle_convert(args)
                self.auditor.log_event(user_id, "CONVERT", " ".join(args)[:50])
                return result

            elif command_name == "backup":
                result = await self.handler.handle_backup(args)
                self.auditor.log_event(user_id, "BACKUP", " ".join(args)[:50])
                return result

            elif command_name == "organize":
                result = await self.handler.handle_organize(args)
                self.auditor.log_event(user_id, "ORGANIZE", " ".join(args)[:50])
                return result

            elif command_name == "file_watcher":
                result = await self.handler.handle_file_watcher(args)
                self.auditor.log_event(user_id, "FILE_WATCHER", " ".join(args)[:50])
                return result

            elif command_name == "version":
                result = await self.handler.handle_version(args)
                self.auditor.log_event(user_id, "VERSION", " ".join(args)[:50])
                return result

            elif command_name == "clean":
                result = await self.handler.handle_clean(args)
                self.auditor.log_event(user_id, "CLEAN", " ".join(args)[:50])
                return result

            # ── PHASE 4: System Enhancement & Convenience ─────────────────────────

            elif command_name == "volume":
                result = await self.handler.handle_volume_app(args)
                self.auditor.log_event(user_id, "VOLUME", " ".join(args)[:50])
                return result

            elif command_name == "power":
                result = await self.handler.handle_power(args)
                self.auditor.log_event(user_id, "POWER", " ".join(args)[:50])
                return result

            elif command_name == "multi_monitor":
                result = await self.handler.handle_multi_monitor(args)
                self.auditor.log_event(user_id, "MULTI_MONITOR", " ".join(args)[:50])
                return result

            elif command_name == "sleep":
                result = await self.handler.handle_sleep(args)
                self.auditor.log_event(user_id, "SLEEP", " ".join(args)[:50])
                return result

            elif command_name == "wake":
                result = await self.handler.handle_wake(args)
                self.auditor.log_event(user_id, "WAKE", " ".join(args)[:50])
                return result

            elif command_name == "quick_app":
                result = await self.handler.handle_quick_app(args)
                self.auditor.log_event(user_id, "QUICK_APP", " ".join(args)[:50])
                return result

            elif command_name == "night_mode":
                result = await self.handler.handle_night_mode(args)
                self.auditor.log_event(user_id, "NIGHT_MODE", " ".join(args)[:50])
                return result

            elif command_name == "window":
                result = await self.handler.handle_window_arrange(args)
                self.auditor.log_event(user_id, "WINDOW", " ".join(args)[:50])
                return result

            elif command_name == "hotkey":
                result = await self.handler.handle_hotkey(args)
                self.auditor.log_event(user_id, "HOTKEY", " ".join(args)[:50])
                return result

            elif command_name == "launch":
                if args and args[0].lower() == "advanced":
                    result = await self.handler.handle_launch_advanced(args[1:])
                else:
                    result = await self.handler.handle_launch_app(args[0] if args else "")
                self.auditor.log_event(user_id, "LAUNCH", " ".join(args)[:50])
                return result

            # ── PHASE 5: Advanced & Pro Features ──────────────────────────────

            elif command_name == "time_track":
                result = await self.handler.handle_time_track(args)
                self.auditor.log_event(user_id, "TIME_TRACK", " ".join(args)[:50])
                return result

            elif command_name == "session":
                result = await self.handler.handle_session(args)
                self.auditor.log_event(user_id, "SESSION", " ".join(args)[:50])
                return result

            elif command_name == "share_screen":
                result = await self.handler.handle_share_screen(args)
                self.auditor.log_event(user_id, "SHARE_SCREEN", " ".join(args)[:50])
                return result

            elif command_name == "multi_device":
                result = await self.handler.handle_multi_device(args)
                self.auditor.log_event(user_id, "MULTI_DEVICE", " ".join(args)[:50])
                return result

            elif command_name == "multi":
                result = await self.handler.handle_multi(args)
                self.auditor.log_event(user_id, "MULTI", " ".join(args)[:50])
                return result

            elif command_name == "profile":
                result = await self.handler.handle_profile(args)
                self.auditor.log_event(user_id, "PROFILE", " ".join(args)[:50])
                return result

            elif command_name == "dash":
                result = await self.handler.handle_dash(args)
                self.auditor.log_event(user_id, "DASH", " ".join(args)[:50])
                return result

            elif command_name == "activity_log":
                result = await self.handler.handle_activity_log(args)
                self.auditor.log_event(user_id, "ACTIVITY_LOG", " ".join(args)[:50])
                return result

            elif command_name == "vpn":
                result = await self.handler.handle_vpn(args)
                self.auditor.log_event(user_id, "VPN", " ".join(args)[:50])
                return result

            elif command_name == "tunnel":
                result = await self.handler.handle_tunnel(args)
                self.auditor.log_event(user_id, "TUNNEL", " ".join(args)[:50])
                return result

            elif command_name == "ai_agent":
                result = await self.handler.handle_ai_agent(args)
                self.auditor.log_event(user_id, "AI_AGENT", " ".join(args)[:50])
                return result

            elif command_name == "help":
                return HELP_TEXT

            else:
                return "❓ Perintah tidak dikenal."

        except Exception as e:
            logger.error(f"Command execution error: {e}")
            self.auditor.log_event(user_id, "COMMAND_ERROR", str(e), success=False)
            raise


HELP_TEXT = """
🤖 *Remote Laptop Control — Help*

*1. Media & Deteksi Layar:*
`!screenshot [grid]` — Screenshot layar (opsi grid koordinat)
`!video [detik]` — Rekam layar (max 30s)
`!webcam` — Foto webcam
`!webcamvid [detik]` — Rekam video webcam
`!active` — Deteksi jendela aplikasi aktif

*2. Simulasi Input:*
`!click [x] [y]` — Simulasi klik mouse kiri
`!type [teks]` — Simulasi ketik teks keyboard
`!press [tombol]` — Simulasi tekan tombol keyboard

*3. Navigasi & File:*
`!cd [path]` — Pindah direktori kerja (Ingatan persisten)
`!ls [path]` — List file di folder aktif
`!find [pattern]` — Cari file secara rekursif
`!get [filepath]` — Download/kirim file ke HP
`!read` — Baca clipboard laptop
`!write [teks]` — Tulis teks ke clipboard laptop
`!clip sync [start|stop]` — Sinkronisasi otomatis clipboard laptop ke HP
`!term` — Mode Terminal Interaktif

*4. AI & Otomasi:*
`!opencode run "<query>"` — Menjalankan AI Coding Agent untuk membuat folder/file/CRUD otomatis
`!agy "<query>"` — Perintah AI Antigravity CLI untuk tugas sistem tingkat lanjut
`!testai` — Menguji konektivitas integrasi AI ke API NVIDIA NIM

*5. Sistem & Kontrol:*
`!sysinfo` — Info CPU, RAM, Disk, Baterai
`!battery` — Status detail dan kesehatan baterai laptop
`!brightness [0-100]` — Mengatur/membaca kecerahan layar laptop
`!media [play|pause|next|prev]` — Mengontrol pemutar musik/video aktif
`!notif [teks]` — Memunculkan popup desktop notification di layar laptop
`!tts [teks]` — Membunyikan suara Text-to-Speech di laptop
`!ping [host]` — Cek latensi laptop ke host (default: 8.8.8.8)
`!speedtest` — Uji kecepatan internet laptop
`!win [minimize|close]` — Minimalkan atau tutup jendela aplikasi aktif
`!web [query]` — Pencarian web Google/DuckDuckGo
`!wifi` — Memindai jaringan Wi-Fi sekitar
`!ports` — Menampilkan daftar port listening aktif
`!process [list|kill <pid/nama>]` — Melihat daftar proses atau menutup paksa aplikasi
`!launch [nama_aplikasi]` — Meluncurkan aplikasi desktop secara remote (misal: chrome, vscode, spotify)
`!apps [query]` — Menampilkan atau mencari daftar aplikasi GUI/desktop terinstall
`!todo [add/done/delete/clear] [tugas | tenggat | speak]` — Mengelola daftar tugas (opsi `speak` untuk bersuara di laptop)
`!guard [on|off]` — Aktifkan mode pengawasan gerakan laptop lewat webcam
`!lock` — Kunci layar laptop
`!unlock` — Buka kunci layar laptop
`!reboot` — Restart laptop (butuh konfirmasi)
`!run [script]` — Jalankan script secara aman
`!listen [detik]` — Rekam suara sekitar (max 30s)
`!logout` — Keluar sesi aktif
`!help` — Tampilkan bantuan ini

*6. Produktivitas (Fitur Baru):*
`!focus [on|off] [menit]` — Mode fokus dengan Pomodoro timer + blokir situs
`!workspace [save|load|list|delete] [nama]` — Simpan/muat seluruh sesi kerja
`!calendar [today|next|list|join]` — Integrasi Google Calendar
`!quicknote [judul] [isi]` — Catatan markdown cepat
`!browser [new|search|scroll|refresh|close] [args]` — Kontrol browser dari HP
`!daily [yesterday]` — Laporan aktivitas laptop 24 jam
`!reminder [add|list|delete] [teks] [waktu]` — Pengingat dengan notifikasi
`!task [add|list|done|delete] [tugas]` — Manajemen tugas terpusat
`!meeting mode [on|off] [nama]` — Persiapan meeting otomatis
`!custom alias [nama] [perintah]` — Buat alias perintah custom sendiri

*7. AI & Automation (Fitur Phase 2):*
`!ai work [perintah]` — AI assistant produktivitas
`!ai write [tipe] [topik]` — Buat draft dokumen/email via AI
`!ai automate [deskripsi]` — Buat automation script via AI
`!ai summarize [target]` — Ringkasan file/folder via AI
`!ai research [topik] [depth]` — Riset topik via AI, simpan ke folder Research
`!ai insight [daily|weekly|monthly]` — Analisis pola penggunaan laptop
`!smart clipboard [on|off|history]` — Smart clipboard dengan deteksi tipe data
`!macro [record|play|save|list|delete] [nama]` — Rekam/putar aksi keyboard mouse
`!schedule add <perintah> <waktu>` — Jadwalkan perintah otomatis
`!voice cmd [on|off]` — Aktifkan voice command dari HP

*8. File, Sync & Data Management (Fitur Phase 3):*
`!sync <folder> [service]` — Sinkronisasi folder ke cloud (local/gdrive)
`!quick upload` — Lihat folder upload untuk kirim file dari HP
`!recent [files|folders] [jumlah]` — Daftar file/folder terbaru
`!search content <keyword> [folder]` — Cari teks di dalam file
`!convert <file> <format>` — Konversi format file (pandoc/ffmpeg)
`!backup <folder> [quick|full]` — Backup folder ke penyimpanan aman
`!organize <folder> [by type|date]` — Organisir file otomatis ke subfolder
`!file watcher [on|off|status] <folder>` — Pantau perubahan folder realtime
`!version [commit|history|revert|status] <file>` — Versioning file lokal
`!clean [temp|cache|duplicates|all]` — Bersihkan sampah disk

*9. System Enhancement (Fitur Phase 4):*
`!volume [app|global] [level|up|down|mute]` — Kontrol volume global/per-app
`!power [performance|balanced|saver]` — Ganti profil daya laptop
`!multi monitor [list|switch|arrange] [args]` — Kelola monitor ganda
`!sleep [delay]` — Tidurkan laptop (contoh: !sleep 5m)
`!wake <waktu>` — Jadwalkan bangunkan laptop (contoh: !wake 07:30)
`!quick app <nama>` — Buka aplikasi cepat (alias !launch)
`!battery health` — Cek kesehatan baterai detail
`!night mode [on|off]` — Dark mode + blue light filter
`!window [arrange|snap|minimize all|close all]` — Atur semua jendela
`!hotkey [create|list|delete] <nama> <key>` — Buat hotkey global
`!launch advanced <app> [args]` — Luncurkan aplikasi dengan parameter

*10. Advanced & Pro (Fitur Phase 5):*
`!time track [start|stop|status|report] [project]` — Lacak waktu kerja
`!session [save|list|restore|delete] <name>` — Simpan/pulihkan session aplikasi
`!share screen [fullscreen|area]` — Screenshot layar
`!multi device [register|list|delete|send] <name> [ip/command]` — Kelola multi-perangkat
`!profile [create|list|apply|delete] <name>` — Profile pengguna (apps, power, tema)
`!dash` — Tampilkan dashboard sistem
`!activity log [days] [--filter=aksi]` — Lihat log aktivitas
`!vpn [status|connect|disconnect] [name]` — Kontrol VPN
`!tunnel [create|list|start|delete] <name> <remote> <port>` — Tunnel SSH
`!ai agent <task>` — AI Agent untuk tugas kompleks

*Mode AI (jika aktif):*
Ketik perintah natural language langsung untuk diterjemahkan oleh AI. Contoh:
- "Ambil screenshot layar sekarang"
- "Tampilkan info sistem"
- "Masuk ke mode terminal"
- "Kunci laptopku"
"""

