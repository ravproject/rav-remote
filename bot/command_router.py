"""
Command Router
"""
from ai_module.nim_client import CommandInterpreter
from agent.command_handler import CommandHandler
from security.audit_logger import AuditLogger
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
            return "❓ Perintah tidak dikenali. Ketik `!help` untuk bantuan."

        try:
            if command_name == "screenshot":
                img_bytes = await self.handler.handle_screenshot()
                self.auditor.log_event(user_id, "SCREENSHOT", "")
                return img_bytes

            elif command_name == "sysinfo":
                info = await self.handler.handle_sysinfo()
                self.auditor.log_event(user_id, "SYSINFO", "")
                return info

            elif command_name == "list_files":
                path = args[0] if args else str(Path.home())
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

            elif command_name == "reboot":
                confirmed = len(args) > 0 and args[0] == "confirm"
                result = await self.handler.handle_reboot(confirmed)
                self.auditor.log_event(user_id, "REBOOT", f"confirmed={confirmed}")
                return result

            elif command_name == "run_script":
                if not args:
                    return "❌ Gunakan: !run <nama_script.py>"
                result = await self.handler.handle_run_script(args[0], user_id)
                self.auditor.log_event(user_id, "RUN_SCRIPT", args[0][:50])
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

*Perintah Tersedia:*
`!screenshot` — Screenshot layar
`!sysinfo` — Info CPU/RAM/Disk
`!ls <path>` — List isi folder
`!get <file>` — Kirim file ke HP
`!lock` — Kunci layar
`!reboot` — Restart (butuh konfirmasi)
`!run <script>` — Jalankan script aman
`!logout` — Keluar dari sesi
`!help` — Tampilkan bantuan ini

*Mode AI (jika aktif):*
Ketik perintah natural language seperti:
"Ambil screenshot layar sekarang"
"Tampilkan info sistem"
"Kunci laptopku"
"""
