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
        "!video": "video",
        "!webcam": "webcam",
        "!webcamvid": "webcamvid",
        "!camvid": "webcamvid",
        "!sysinfo": "sysinfo",
        "!info": "sysinfo",
        "!ls": "list_files",
        "!cd": "cd",
        "!get": "get_file",
        "!lock": "lock_screen",
        "!lock_screen": "lock_screen",
        "!kunci": "lock_screen",
        "!unlock": "unlock",
        "!buka": "unlock",
        "!reboot": "reboot",
        "!term": "term",
        "!terminal": "term",
        "!exit": "exit",
        "!opencode": "opencode",
        "!agy": "agy",
        "!run": "run_script",
        "!testai": "testai",
        "!test-ai": "testai",
        "!help": "help",
        "!logout": "logout",
        "!clip": "clip",
        "!open": "open",
        "!top": "top",
        "!kill": "kill",
        "!volume": "volume",
        "!mute": "mute",
        "!brightness": "brightness",
        "!media": "media",
        "!battery": "battery",
        "!notif": "notif",
        "!process": "process",
        "!clipboard": "clip",
        "!alarm": "alarm",
        "!schedule": "schedule",
        "!listen": "listen",
        "!audio": "listen",
        "!click": "click",
        "!type": "type",
        "!press": "press",
        "!active": "active",
        "!window": "active",
        "!read": "clip",
        "!write": "clip",
        "!find": "find",
        "!search": "find",
        "!tts": "tts",
        "!ping": "ping",
        "!speedtest": "speedtest",
        "!win": "window_control",
        "!winctl": "window_control",
        "!web": "web",
        "!google": "web",
        "!wifi": "wifi",
        "!ports": "ports",
        "!launch": "launch",
        "!todo": "todo",
        "!apps": "apps",
        "!guard": "guard",
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

        if cmd_key == "!read":
            return "clip", ["read"] + args
        if cmd_key == "!write":
            return "clip", ["write"] + args

        command_name = self.COMMAND_MAP.get(cmd_key)
        return command_name, args
