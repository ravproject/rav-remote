"""
Modul sanitasi input — GARIS PERTAHANAN PERTAMA
Menggunakan pendekatan "Parse-First" untuk keamanan maksimal.
"""
import re
import os
import yaml
import shlex
from pathlib import Path
from typing import Optional, List, Tuple
from loguru import logger

# Load whitelist dari config
def load_allowed_commands() -> dict:
    config_path = Path(__file__).parent.parent / "config" / "allowed_commands.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

ALLOWED_COMMANDS = load_allowed_commands()

class InputSanitizer:
    """
    Sanitizer berlapis:
    1. Normalisasi (Lowercase + Strip non-printable)
    2. Parsing (shlex.split untuk bypass quotes/escapes)
    3. Whitelist validation
    4. Blacklist pattern scanning pada setiap argumen
    """

    @staticmethod
    def _normalize(raw_input: str) -> str:
        """Normalisasi dasar sebelum parsing."""
        # Hapus karakter non-printable kecuali yang esensial
        normalized = "".join(c for c in raw_input if c.isprintable() or c in "\n\r\t").strip()
        return normalized

    @staticmethod
    def sanitize_command(raw_input: str) -> Optional[str]:
        """
        Main entry point untuk sanitasi command Telegram.
        Return None jika berbahaya atau tidak valid.
        """
        if not raw_input or len(raw_input) > 500:
            return None

        normalized = InputSanitizer._normalize(raw_input)

        try:
            # Parse-First: Pecah menjadi tokens seperti shell sesungguhnya
            tokens = shlex.split(normalized)
            if not tokens:
                return None
            
            # 1. Validasi Perintah Utama (Whitelist) jika menggunakan prefix '!'
            is_explicit = normalized.startswith("!")
            cmd_name = tokens[0].lstrip("!").lower()
            safe_cmds = ALLOWED_COMMANDS.get("safe_commands", {})
            
            if is_explicit and cmd_name not in safe_cmds:
                logger.warning(f"Command not in whitelist: {cmd_name}")
                return None

            # 2. Validasi Argumen & Natural Language (Blacklist)
            # Ambil pola blokir dari config
            blocked_patterns = ALLOWED_COMMANDS.get("blocked_patterns", [])
            compiled_patterns = [re.compile(p, re.IGNORECASE) for p in blocked_patterns]

            # Pola tambahan tingkat lanjut (Hardcoded sebagai safety net terakhir)
            ADVANCED_BLOCKED = [
                r'\$\(.*\)',           # Command substitution
                r'`.*`',               # Backticks
                r'<\(.*\)',            # Process substitution
                r'<<+EOF',             # Heredoc
                r'\\x[0-9a-fA-F]{2}',  # Hex encoding
                r'\\u[0-9a-fA-F]{4}',  # Unicode encoding
                r'/[?*]{3,}/',         # Globbing bypass (misal: /???/??t)
                r'\|',                 # Pipe
                r'&',                  # Background/AND
                r'>',                  # Redirect
                r';',                  # Semicolon separator
            ]
            compiled_patterns.extend([re.compile(p, re.IGNORECASE) for p in ADVANCED_BLOCKED])

            # Scan setiap token
            for token in tokens:
                for pattern in compiled_patterns:
                    if pattern.search(token):
                        logger.critical(
                            f"SECURITY ALERT: Blocked pattern '{pattern.pattern}' "
                            f"detected in token: '{token[:50]}'"
                        )
                        return None

            # Jika lolos semua, return input yang sudah "bersih" (tanpa quotes aneh)
            # Namun kita return original/normalized untuk eksekusi jika perlu, 
            # atau return tokens yang digabung kembali dengan aman.
            # Rekomendasi: return original tapi divalidasi.
            return normalized

        except ValueError as e:
            # shlex akan error jika ada quotes yang tidak tertutup (No closing quotation)
            logger.error(f"Parsing error (potential injection attempt): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected sanitization error: {e}")
            return None

    @staticmethod
    def validate_command_whitelist(command: str) -> Tuple[bool, str]:
        """Validasi cepat apakah perintah ada di whitelist."""
        normalized = InputSanitizer._normalize(command)
        parts = normalized.split()
        if not parts:
            return False, ""
        
        cmd_name = parts[0].lstrip("!")
        safe_cmds = ALLOWED_COMMANDS.get("safe_commands", {})
        
        return cmd_name in safe_cmds, cmd_name

    @staticmethod
    def sanitize_filepath(filepath: str) -> Optional[str]:
        """Validasi path file — izinkan semua path setelah di-resolve."""
        try:
            # Resolve path absolut (menghilangkan .. dan symlinks)
            target_path = Path(filepath).expanduser().resolve()
            return str(target_path)
        except Exception as e:
            logger.error(f"Path validation error for {filepath}: {e}")
            return None
