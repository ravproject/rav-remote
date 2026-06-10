"""
Fallback parser for explicit commands.
"""
from typing import Optional

class FallbackParser:
    """
    Parser explicit command — digunakan saat AI tidak tersedia
    atau user menggunakan perintah ! secara langsung.
    """

    COMMAND_MAP = {
        "!screenshot": "screenshot",
        "!ss": "screenshot",
        "!sysinfo": "sysinfo",
        "!info": "sysinfo",
        "!ls": "list_files",
        "!get": "get_file",
        "!lock": "lock_screen",
        "!kunci": "lock_screen",
        "!reboot": "reboot",
        "!run": "run_script",
        "!help": "help",
        "!logout": "logout",
    }

    def parse(self, text: str) -> tuple[Optional[str], list[str]]:
        """
        Parse explicit command.
        Return (command_name, args) atau (None, []) jika tidak valid.
        """
        parts = text.strip().split()
        if not parts:
            return None, []

        cmd_key = parts[0].lower()
        args = parts[1:]

        command_name = self.COMMAND_MAP.get(cmd_key)
        return command_name, args
