"""
Audit Logger — Catat semua aktivitas sistem
Format: JSON terstruktur untuk kemudahan analisis
"""
import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger
import sys


LOG_FILE = Path(os.environ.get("LOG_FILE", "./logs/audit.log"))
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


class AuditLogger:

    def __init__(self):
        # Konfigurasi loguru untuk structured logging
        logger.remove()  # Hapus default handler

        # Console output (untuk debugging)
        logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level=os.environ.get("LOG_LEVEL", "INFO"),
            colorize=True,
        )

        # File audit log (JSON format)
        logger.add(
            str(LOG_FILE),
            format="{message}",
            level="DEBUG",
            rotation="10 MB",       # Rotate tiap 10MB
            retention="30 days",    # Simpan 30 hari
            compression="gz",       # Kompresi log lama
            serialize=False,        # Kita handle JSON sendiri
        )

    def log_event(
        self,
        user_id: str,
        event_type: str,
        details: str,
        success: bool = True,
    ):
        """
        Catat event ke audit log.
        Format: JSON satu baris per event.
        """
        # Hash user_id untuk privasi di log
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:12]

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_hash": user_hash,    # Hash, bukan ID asli
            "event_type": event_type,
            "details": details[:200],  # Batasi panjang
            "success": success,
        }

        logger.info(json.dumps(entry, ensure_ascii=False))

    def log_security_alert(self, user_id: str, threat_type: str, raw_input: str):
        """Log khusus untuk ancaman keamanan — level CRITICAL."""
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:12]

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_hash": user_hash,
            "event_type": "SECURITY_ALERT",
            "threat_type": threat_type,
            "raw_input_hash": hashlib.sha256(raw_input.encode()).hexdigest(),
            "success": False,
        }

        logger.critical(json.dumps(entry, ensure_ascii=False))
