"""
Sistem autentikasi berlapis:
1. Whitelist User ID (Telegram/WhatsApp)
2. OTP via TOTP (Google Authenticator compatible)
3. JWT Token dengan expiry
4. Rate limiting per user
"""
import os
import time
import pyotp
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from functools import lru_cache
from loguru import logger
from .rate_limiter import check_rate_limit


OTP_SECRET = os.environ["OTP_SECRET_KEY"]
JWT_SECRET = os.environ["JWT_SECRET_KEY"]
ALLOWED_USERS = set(
    os.environ.get("ALLOWED_USER_IDS", "").split(",")
)

# Token blacklist (untuk logout/revoke)
_revoked_tokens: set[str] = set()

class AuthManager:

    @staticmethod
    def is_user_allowed(user_id: str) -> bool:
        """Cek apakah user ID ada di whitelist."""
        allowed = str(user_id) in ALLOWED_USERS
        if not allowed:
            logger.warning(f"Unauthorized access attempt from user_id: {user_id}")
        return allowed

    @staticmethod
    def verify_otp(otp_input: str) -> bool:
        """
        Verifikasi TOTP code (compatible dengan Google Authenticator).
        Window=1 berarti toleransi ±30 detik.
        """
        totp = pyotp.TOTP(OTP_SECRET)
        valid = totp.verify(otp_input, valid_window=1)
        if not valid:
            logger.warning(f"Invalid OTP attempt: {otp_input[:6]}")
        return valid

    @staticmethod
    def generate_session_token(user_id: str) -> str:
        """
        Generate JWT token setelah OTP berhasil.
        Berlaku 4 jam.
        """
        payload = {
            "sub": str(user_id),
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=4),
            "jti": hashlib.sha256(
                f"{user_id}{time.time()}".encode()
            ).hexdigest()[:16],
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        logger.info(f"Session token issued for user: {user_id}")
        return token

    @staticmethod
    def verify_session_token(token: str) -> Optional[str]:
        """
        Verifikasi JWT token.
        Return user_id jika valid, None jika tidak.
        """
        if token in _revoked_tokens:
            return None
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            return payload.get("sub")
        except JWTError as e:
            logger.warning(f"Invalid JWT: {e}")
            return None

    @staticmethod
    def revoke_token(token: str):
        """Revoke token (logout)."""
        _revoked_tokens.add(token)
        logger.info("Session token revoked")

    @staticmethod
    def check_rate_limit(user_id: str) -> bool:
        """
        Rate limiting: max N perintah per menit per user.
        Return True jika masih dalam batas.
        """
        return check_rate_limit(user_id)


def require_auth(handler_func):
    """
    Decorator untuk handler yang butuh autentikasi.
    Cek whitelist + rate limit sebelum eksekusi.
    """
    async def wrapper(user_id: str, token: str, *args, **kwargs):
        # 1. Cek whitelist
        if not AuthManager.is_user_allowed(user_id):
            return "❌ Akses ditolak. User tidak diizinkan."

        # 2. Verifikasi JWT session
        verified_user = AuthManager.verify_session_token(token)
        if not verified_user or verified_user != user_id:
            return "❌ Sesi tidak valid atau expired. Silakan login ulang dengan OTP."

        # 3. Rate limiting
        if not AuthManager.check_rate_limit(user_id):
            return "⚠️ Terlalu banyak perintah. Tunggu sebentar."

        return await handler_func(user_id, token, *args, **kwargs)

    return wrapper
