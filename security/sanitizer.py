"""
Modul sanitasi input — GARIS PERTAHANAN PERTAMA
Mencegah command injection, path traversal, shell metacharacters
"""
import re
import os
import yaml
from pathlib import Path
from typing import Optional
from loguru import logger


# Karakter berbahaya yang TIDAK BOLEH ada dalam input
DANGEROUS_PATTERNS = [
    r'[;&|`$]',                    # Shell metacharacters
    r'\.\.\/',                     # Path traversal (../)
    r'[\x00-\x1f\x7f]',           # Control characters
    r'(rm\s+-rf|mkfs|dd\s+if=)',   # Destructive commands
    r'(\|\s*bash|\|\s*sh)',        # Pipe to shell
    r'(curl|wget).*\|',            # Remote code execution
    r'>\s*/dev/',                  # Device overwrite
    r'(sudo\s+su|passwd\s+root)',  # Privilege escalation
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]

# Load whitelist dari config
def load_allowed_commands() -> dict:
    config_path = Path(__file__).parent.parent / "config" / "allowed_commands.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

ALLOWED_COMMANDS = load_allowed_commands()


class InputSanitizer:
    """
    Sanitizer berlapis untuk semua input dari user.
    Gunakan SELALU sebelum memproses perintah apapun.
    """

    @staticmethod
    def sanitize_command(raw_input: str) -> Optional[str]:
        """
        Bersihkan dan validasi input command.
        Return None jika input berbahaya.
        """
        if not raw_input or len(raw_input) > 500:
            logger.warning(f"Input rejected: empty or too long")
            return None

        # Strip whitespace
        cleaned = raw_input.strip()

        # Cek dangerous patterns
        for pattern in COMPILED_PATTERNS:
            if pattern.search(cleaned):
                logger.critical(
                    f"SECURITY ALERT: Dangerous pattern '{pattern.pattern}' "
                    f"detected in input: '{cleaned[:100]}'"
                )
                return None

        return cleaned

    @staticmethod
    def validate_command_whitelist(command: str) -> tuple[bool, str]:
        """
        Pastikan command ada di whitelist.
        Return (is_valid, command_name)
        """
        parts = command.split()
        if not parts:
            return False, ""

        cmd_name = parts[0].lstrip("!")
        safe_cmds = ALLOWED_COMMANDS.get("safe_commands", {})

        if cmd_name not in safe_cmds:
            logger.warning(f"Command not in whitelist: {cmd_name}")
            return False, cmd_name

        return True, cmd_name

    @staticmethod
    def sanitize_filepath(filepath: str) -> Optional[str]:
        """
        Validasi path file — cegah path traversal.
        Hanya izinkan path di dalam allowed_paths.
        """
        try:
            # Resolve path absolut tanpa ..
            resolved = Path(filepath).resolve()
            home = Path.home()
            cwd = Path.cwd()

            allowed_dirs = [
                home / "Documents",
                home / "Downloads",
                home / "Desktop",
                cwd,
                home,  # Izinkan seluruh direktori home pengguna
            ]

            # Pastikan path ada di dalam direktori yang diizinkan
            for allowed in allowed_dirs:
                try:
                    resolved.relative_to(allowed)
                    return str(resolved)
                except ValueError:
                    continue

            logger.warning(f"Path traversal attempt: {filepath} -> {resolved}")
            return None

        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return None
