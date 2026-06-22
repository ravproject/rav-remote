"""
Audit Logger — Catat semua aktivitas sistem
Format: JSON terstruktur (Terenkripsi At-Rest)
"""
import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger
import sys
from security.crypto import crypto


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

        # File audit log (Format terenkripsi per baris)
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
        Format: JSON satu baris per event (terenkripsi).
        """
        # Hash user_id untuk privasi di log
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:12]

        # Mask details for UNLOCK event to prevent password leakage
        safe_details = "[MASKED]" if event_type == "UNLOCK" else details[:200]

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_hash": user_hash,
            "event_type": event_type,
            "details": safe_details,
            "success": success,
        }

        SENSITIVE_EVENTS = ("SECURITY_ALERT", "AUTH_FAILURE", "TOKEN_REVOKED", "LOGIN_SUCCESS", "UNLOCK")

        try:
            if crypto is None:
                raise RuntimeError("CryptoManager not initialized")
            
            json_entry = json.dumps(entry, ensure_ascii=False)
            encrypted_entry = crypto.encrypt(json_entry)
            logger.info(encrypted_entry)
        except Exception as e:
            # Fail-Closed for sensitive events
            if event_type in SENSITIVE_EVENTS:
                logger.error(f"KRITIS: Enkripsi gagal untuk event sensitif '{event_type}'. Event TIDAK dicatat.")
                # We don't raise here to prevent crashing the whole app, 
                # but we strictly do NOT log the sensitive data in plaintext.
            else:
                # Fail-Open for non-sensitive events (e.g., SCREENSHOT, SYSINFO)
                logger.warning(f"Enkripsi fallback untuk event non-sensitif: {event_type}")
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

        try:
            if crypto is None:
                raise RuntimeError("CryptoManager not initialized")
            
            json_entry = json.dumps(entry, ensure_ascii=False)
            encrypted_entry = crypto.encrypt(json_entry)
            logger.critical(encrypted_entry)
        except Exception as e:
            # Security alerts are ALWAYS sensitive: Fail-Closed
            logger.error(f"KRITIS: Enkripsi gagal untuk SECURITY_ALERT. Alert TIDAK dicatat untuk mencegah kebocoran plaintext.")
