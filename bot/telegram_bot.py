"""
Telegram Bot Handler
Menggunakan python-telegram-bot v21 (async)
"""
import os
import asyncio
import warnings
# Suppress python-telegram-bot shutdown warning (asyncio loop cancellation quirk on Python 3.12+)
warnings.filterwarnings("ignore", category=RuntimeWarning, message="coroutine 'Updater.stop' was never awaited")

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

import json

SESSIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "sessions", "tg_sessions.json")

def load_initial_sessions() -> dict[str, str]:
    if not os.path.exists(SESSIONS_FILE):
        return {}
    try:
        with open(SESSIONS_FILE, "r") as f:
            data = json.load(f)
        # Hanya muat sesi yang masih valid masa berlakunya
        valid = {}
        for uid, token in data.items():
            if AuthManager.verify_session_token(token):
                valid[uid] = token
        return valid
    except Exception as e:
        logger.error(f"Failed to load sessions: {e}")
        return {}

def save_current_sessions():
    try:
        os.makedirs(os.path.dirname(SESSIONS_FILE), exist_ok=True)
        with open(SESSIONS_FILE, "w") as f:
            json.dump(_user_sessions, f)
    except Exception as e:
        logger.error(f"Failed to save sessions: {e}")

# State sesi per user: {user_id: jwt_token}
_user_sessions: dict[str, str] = load_initial_sessions()
# State mode terminal per user: {user_id: bool}
_terminal_mode: dict[str, bool] = {}
# Background tasks for terminal polling: {user_id: Task}
_terminal_tasks: dict[str, asyncio.Task] = {}

AGENT_URL = f"http://{os.environ.get('AGENT_HOST', 'localhost')}:{os.environ.get('AGENT_PORT', '8765')}"
AGENT_API_KEY = os.environ["AGENT_API_KEY"]

import httpx
import tempfile
import speech_recognition as sr
from pydub import AudioSegment

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk upload file (Document/Photo)."""
    user_id = str(update.effective_user.id)
    token = _user_sessions.get(user_id)
    
    if not token or not AuthManager.verify_session_token(token):
        await update.message.reply_text("🔐 Belum login atau sesi expired.")
        return

    await update.message.reply_text("⏳ Mengunduh file dan mengirim ke laptop...")
    
    try:
        if update.message.document:
            file = await context.bot.get_file(update.message.document.file_id)
            filename = update.message.document.file_name
        elif update.message.photo:
            file = await context.bot.get_file(update.message.photo[-1].file_id)
            filename = f"photo_{update.message.message_id}.jpg"
        else:
            return

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            await file.download_to_drive(custom_path=tmp_file.name)
            
            headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient() as client:
                with open(tmp_file.name, "rb") as f:
                    files = {'file': (filename, f)}
                    data = {'user_id': user_id}
                    res = await client.post(f"{AGENT_URL}/file/upload", data=data, files=files, headers=headers)
                    
            if res.status_code == 200:
                msg = res.json().get("message", "Upload berhasil")
                await update.message.reply_text(msg)
                auditor.log_event(user_id, "FILE_UPLOAD", filename)
            else:
                await update.message.reply_text("❌ Gagal mengirim file ke laptop.")
                
        os.remove(tmp_file.name)
    except Exception as e:
        logger.error(f"Upload error: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat upload.")

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk Voice Note (STT)."""
    user_id = str(update.effective_user.id)
    token = _user_sessions.get(user_id)
    
    if not token or not AuthManager.verify_session_token(token):
        await update.message.reply_text("🔐 Belum login atau sesi expired.")
        return

    if not AuthManager.check_rate_limit(user_id):
        await update.message.reply_text("⚠️ Terlalu banyak perintah.")
        return

    await update.message.reply_text("🎙️ Memproses pesan suara...")
    
    try:
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_ogg:
            await voice_file.download_to_drive(custom_path=tmp_ogg.name)
            
        # Convert OGG to WAV for SpeechRecognition
        wav_path = tmp_ogg.name + ".wav"
        audio = AudioSegment.from_ogg(tmp_ogg.name)
        audio.export(wav_path, format="wav")
        
        # Transcribe
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="id-ID")
            
        await update.message.reply_text(f"🗣️ *Anda berkata:* {text}", parse_mode="Markdown")
        
        # Forward the transcribed text to the command router
        # Fake an update message text to reuse existing logic
        update.message.text = text
        await message_handler(update, context)
        
        os.remove(tmp_ogg.name)
        os.remove(wav_path)
        
    except sr.UnknownValueError:
        await update.message.reply_text("❌ Suara tidak terdengar jelas.")
    except Exception as e:
        logger.error(f"Voice error: {e}")
        await update.message.reply_text("❌ Gagal memproses pesan suara.")

async def poll_terminal(user_id: str, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Background task to poll terminal output from agent."""
    token = _user_sessions.get(user_id)
    headers = {
        "X-API-Key": AGENT_API_KEY,
        "Authorization": f"Bearer {token}"
    }
    
    last_message_id = None
    accumulated_output = ""
    
    while _terminal_mode.get(user_id):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{AGENT_URL}/terminal/read/{user_id}", headers=headers, timeout=10)
                if response.status_code == 200:
                    output = response.json().get("output", "")
                    if output:
                        accumulated_output += output
                        # Telegram has a limit on message length and rate limits
                        if len(accumulated_output) > 2000 or "\n" in output:
                            text = f"```\n{accumulated_output[-4000:]}\n```"
                            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
                            accumulated_output = ""
                elif response.status_code == 401:
                    break
        except Exception as e:
            logger.error(f"Error polling terminal for {user_id}: {e}")
        
        await asyncio.sleep(1.5)
    
    # Send remaining output
    if accumulated_output:
        await context.bot.send_message(chat_id=chat_id, text=f"```\n{accumulated_output}\n```", parse_mode="Markdown")

async def terminal_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle !term and !exit manually in message_handler or via command."""
    user_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if text == "!term":
        if _terminal_mode.get(user_id):
            await update.message.reply_text("⚠️ Anda sudah berada dalam Mode Terminal.")
            return

        # Start terminal on agent
        token = _user_sessions.get(user_id)
        headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(f"{AGENT_URL}/terminal/start", json={"user_id": user_id}, headers=headers)
                if res.status_code == 200:
                    _terminal_mode[user_id] = True
                    await update.message.reply_text(
                        "💻 *Mode Terminal Aktif (Host Machine)*\n\n"
                        "⚠️ *PERINGATAN:* Anda memiliki akses penuh ke mesin host.\n"
                        "Ketik perintah apa pun untuk mengirim ke shell.\n"
                        "Ketik `!exit` untuk keluar.",
                        parse_mode="Markdown"
                    )
                    # Start polling task
                    task = asyncio.create_task(poll_terminal(user_id, context, chat_id))
                    _terminal_tasks[user_id] = task
                    auditor.log_event(user_id, "TERMINAL_START", "")
                else:
                    await update.message.reply_text("❌ Gagal memulai terminal. Cek auth.")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")

    elif text == "!exit":
        if not _terminal_mode.get(user_id):
            return
        
        _terminal_mode[user_id] = False
        if user_id in _terminal_tasks:
            _terminal_tasks[user_id].cancel()
            del _terminal_tasks[user_id]
        
        # Stop terminal on agent
        token = _user_sessions.get(user_id)
        headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            await client.post(f"{AGENT_URL}/terminal/stop", json={"user_id": user_id}, headers=headers)
        
        await update.message.reply_text("👋 Mode Terminal dinonaktifkan.")
        auditor.log_event(user_id, "TERMINAL_STOP", "")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk semua pesan teks — routing ke command executor atau terminal."""
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
        save_current_sessions()
        await update.message.reply_text(
            "⏰ Sesi expired. Silakan /start ulang."
        )
        return

    # Handle Mode Terminal commands
    if message_text in ["!term", "!exit"]:
        await terminal_command_handler(update, context)
        return

    # Jika sedang dalam mode terminal, forward ke agent terminal write
    if _terminal_mode.get(user_id):
        headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            try:
                # Add newline to simulate Enter
                await client.post(f"{AGENT_URL}/terminal/write", json={"user_id": user_id, "data": message_text + "\n"}, headers=headers)
            except Exception as e:
                await update.message.reply_text(f"❌ Error writing to terminal: {e}")
        return

    # Rate limiting (hanya untuk perintah normal)
    if not AuthManager.check_rate_limit(user_id):
        await update.message.reply_text(
            "⚠️ Terlalu banyak perintah. Tunggu 1 menit."
        )
        return

    # Proses perintah normal
    await update.message.reply_text("⏳ Memproses...")

    try:
        result = await router.route(message_text, user_id)
        auditor.log_event(user_id, "COMMAND_EXECUTED", message_text[:100])

        # Kirim hasil
        if isinstance(result, dict):
            if result.get("type") == "photo":
                await update.message.reply_photo(result["data"], caption="📸 Berhasil")
            elif result.get("type") == "video":
                await update.message.reply_video(result["data"], caption="📹 Live Stream")
            # For file downloads (!get)
            elif "filename" in result:
                 await update.message.reply_document(document=result["data"], filename=result["filename"])
            elif "error" in result:
                 await update.message.reply_text(f"❌ {result['error']}")
        elif isinstance(result, bytes): # Fallback for old screenshot logic if not fully migrated
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


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /start — request OTP."""
    user_id = str(update.effective_user.id)

    if not AuthManager.is_user_allowed(user_id):
        await update.message.reply_text(
            "❌ Akses ditolak. User ID Anda tidak ada di whitelist."
        )
        auditor.log_event(user_id, "UNAUTHORIZED_START", "")
        return

    # Cek apakah sudah ada sesi aktif yang valid
    token = _user_sessions.get(user_id)
    if token and AuthManager.verify_session_token(token):
        await update.message.reply_text(
            "✅ *Sesi Anda sudah aktif!*\n\nTidak perlu login/OTP ulang. Anda bisa langsung menggunakan perintah:\n\n"
            "`!screenshot` — Screenshot layar\n"
            "`!sysinfo` — Info sistem\n"
            "`!ls <path>` — List file\n"
            "`!get <file>` — Kirim file\n"
            "`!lock` — Kunci layar\n"
            "`!help` — Bantuan\n\n"
            "🤖 Atau ketik pesan biasa (contoh: 'ambil screenshot')",
            parse_mode="Markdown"
        )
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
        save_current_sessions()

        await update.message.reply_text(
            """✅ *Login berhasil!* Sesi aktif 4 jam.\n\nPerintah tersedia:\n`!screenshot` — Screenshot layar\n`!sysinfo` — Info sistem\n`!ls <path>` — List file\n`!get <file>` — Kirim file\n`!lock` — Kunci layar\n`!help` — Bantuan\n\n🤖 Mode AI: Ketik perintah natural language""",
            parse_mode="Markdown"
        )
        auditor.log_event(user_id, "LOGIN_SUCCESS", "OTP verified")
    else:
        await update.message.reply_text("❌ OTP salah atau expired. Coba lagi.")
        auditor.log_event(user_id, "LOGIN_FAILED", f"Invalid OTP attempt")


async def logout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /logout — revoke sesi."""
    user_id = str(update.effective_user.id)
    token = _user_sessions.pop(user_id, None)
    save_current_sessions()
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
    app.add_handler(
        MessageHandler(filters.Document.ALL | filters.PHOTO, document_handler)
    )
    app.add_handler(
        MessageHandler(filters.VOICE, voice_handler)
    )

    logger.info("Telegram bot initialized")
    return app

async def alert_poller(app: Application):
    """Background task to poll system alerts from the agent."""
    while True:
        try:
            # Only poll if there's at least one active session
            if _user_sessions:
                headers = {"X-API-Key": AGENT_API_KEY}
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{AGENT_URL}/system/alerts", headers=headers, timeout=5)
                    if response.status_code == 200:
                        alerts = response.json().get("alerts", [])
                        for alert in alerts:
                            # Broadcast to all logged-in users (usually just the owner)
                            for user_id in _user_sessions.keys():
                                try:
                                    await app.bot.send_message(chat_id=user_id, text=alert, parse_mode="Markdown")
                                except Exception as e:
                                    logger.error(f"Failed to send alert to {user_id}: {e}")
        except Exception as e:
            logger.debug(f"Alert poller error (Agent might be offline): {e}")
        
        await asyncio.sleep(60) # Poll every minute

if __name__ == "__main__":
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = create_telegram_app()
    
    # Start alert poller in background
    loop.create_task(alert_poller(app))
    
    logger.info("Starting Telegram bot (polling mode)...")
    app.run_polling(drop_pending_updates=True)
