"""
Telegram Bot Handler
Menggunakan python-telegram-bot v21 (async)
"""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from loguru import logger
from .auth import AuthManager, require_auth
from .command_router import CommandRouter
from security.audit_logger import AuditLogger

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
router = CommandRouter()
auditor = AuditLogger()

# State sesi per user: {user_id: jwt_token}
_user_sessions: dict[str, str] = {}


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /start — request OTP."""
    user_id = str(update.effective_user.id)

    if not AuthManager.is_user_allowed(user_id):
        await update.message.reply_text(
            "❌ Akses ditolak. User ID Anda tidak ada di whitelist."
        )
        auditor.log_event(user_id, "UNAUTHORIZED_START", "")
        return

    await update.message.reply_text(
        """🔐 *Autentikasi Diperlukan*\n\nKirim OTP 6-digit dari Google Authenticator:\n`/otp <kode_6_digit>`""",
        parse_mode="Markdown"
    )


async def otp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /otp <code> — verifikasi OTP dan buat sesi."""
    user_id = str(update.effective_user.id)

    if not context.args:
        await update.message.reply_text("Gunakan: /otp 123456")
        return

    otp_code = context.args[0]

    if not AuthManager.is_user_allowed(user_id):
        return

    if AuthManager.verify_otp(otp_code):
        token = AuthManager.generate_session_token(user_id)
        _user_sessions[user_id] = token

        await update.message.reply_text(
            """✅ *Login berhasil!* Sesi aktif 4 jam.\n\nPerintah tersedia:\n`!screenshot` — Screenshot layar\n`!sysinfo` — Info sistem\n`!ls <path>` — List file\n`!get <file>` — Kirim file\n`!lock` — Kunci layar\n`!help` — Bantuan\n\n🤖 Mode AI: Ketik perintah natural language""",
            parse_mode="Markdown"
        )
        auditor.log_event(user_id, "LOGIN_SUCCESS", "OTP verified")
    else:
        await update.message.reply_text("❌ OTP salah atau expired. Coba lagi.")
        auditor.log_event(user_id, "LOGIN_FAILED", f"Invalid OTP attempt")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk semua pesan teks — routing ke command executor."""
    user_id = str(update.effective_user.id)
    message_text = update.message.text

    # Cek sesi aktif
    token = _user_sessions.get(user_id)
    if not token:
        await update.message.reply_text(
            "🔐 Belum login. Gunakan /start untuk autentikasi."
        )
        return

    # Verifikasi sesi masih valid
    if not AuthManager.verify_session_token(token):
        del _user_sessions[user_id]
        await update.message.reply_text(
            "⏰ Sesi expired. Silakan /start ulang."
        )
        return

    # Rate limiting
    if not AuthManager.check_rate_limit(user_id):
        await update.message.reply_text(
            "⚠️ Terlalu banyak perintah. Tunggu 1 menit."
        )
        return

    # Proses perintah
    await update.message.reply_text("⏳ Memproses...")

    try:
        result = await router.route(message_text, user_id)
        auditor.log_event(user_id, "COMMAND_EXECUTED", message_text[:100])

        # Kirim hasil (text atau file)
        if isinstance(result, bytes):
            await update.message.reply_photo(result, caption="📸 Screenshot")
        elif isinstance(result, str):
            # Potong jika terlalu panjang
            if len(result) > 4000:
                result = result[:3900] + "\n...[truncated]"
            await update.message.reply_text(f"```\n{result}\n```", parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Command error for {user_id}: {e}")
        await update.message.reply_text("❌ Terjadi error. Cek log agent.")
        auditor.log_event(user_id, "COMMAND_ERROR", str(e))


async def logout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /logout — revoke sesi."""
    user_id = str(update.effective_user.id)
    token = _user_sessions.pop(user_id, None)
    if token:
        AuthManager.revoke_token(token)
    await update.message.reply_text("👋 Logout berhasil. Sesi dihapus.")
    auditor.log_event(user_id, "LOGOUT", "")


def create_telegram_app() -> Application:
    """Buat dan konfigurasi aplikasi Telegram bot."""
    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("otp", otp_handler))
    app.add_handler(CommandHandler("logout", logout_handler))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )

    logger.info("Telegram bot initialized")
    return app


if __name__ == "__main__":
    app = create_telegram_app()
    logger.info("Starting Telegram bot (polling mode)...")
    app.run_polling(drop_pending_updates=True)
