"""
Telegram Bot Handler
Menggunakan python-telegram-bot v21 (async)
"""
import os
import asyncio
import warnings
import json
import httpx
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv

# Suppress python-telegram-bot shutdown warning
warnings.filterwarnings("ignore", category=RuntimeWarning, message="coroutine 'Updater.stop' was never awaited")

load_dotenv()

from telegram import Update, constants
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ApplicationBuilder,
)
from loguru import logger
from .auth import AuthManager
from .command_router import CommandRouter
from security.audit_logger import AuditLogger
from .monitor_task import MonitorTask

from bot.agent_registry import registry

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
# Remove global AGENT_URL and AGENT_API_KEY variables

router = CommandRouter()
auditor = AuditLogger()

SESSIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "sessions", "tg_sessions.json")

def load_initial_sessions() -> dict[str, str]:
    if not os.path.exists(SESSIONS_FILE):
        return {}
    try:
        with open(SESSIONS_FILE, "r") as f:
            data = json.load(f)
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

_user_sessions: dict[str, str] = load_initial_sessions()
_user_active_agent: dict[str, str] = {}
_terminal_mode: dict[str, bool] = {}
_terminal_tasks: dict[str, asyncio.Task] = {}

async def heartbeat_poller(app: Application, monitor: MonitorTask):
    """Background task to poll heartbeats from all registered agents."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        while True:
            agents = registry.get_all()
            for agent_id, data in agents.items():
                try:
                    headers = {"X-API-Key": data['api_key']}
                    agent_url = f"http://{data['host']}:{data['port']}"
                    response = await client.get(f"{agent_url}/system/heartbeat", headers=headers)
                    if response.status_code == 200:
                        resp_data = response.json()
                        metrics = resp_data.get("metrics", {})
                        alerts = resp_data.get("alerts", [])
                        
                        await monitor.update_heartbeat(agent_id, metrics)
                        
                        for alert in alerts:
                            await monitor._broadcast_alert(f"⚠️ <b>Alert ({agent_id}):</b> {alert}")
                            
                    elif response.status_code == 401:
                        logger.error(f"Agent {agent_id} returned 401 Unauthorized for heartbeat. Check API keys.")
                            
                except Exception as e:
                    logger.debug(f"Heartbeat poller error for {agent_id} (Agent might be offline): {e}")
            
            await asyncio.sleep(60)

async def post_init(application: Application):
    """Dipanggil setelah bot siap, sebelum polling dimulai."""
    monitor = MonitorTask(application)
    asyncio.create_task(heartbeat_poller(application, monitor))
    asyncio.create_task(monitor.run_monitoring_loop())
    
    # Log konfirmasi sederhana tanpa JobQueue
    async def log_ready_delayed():
        await asyncio.sleep(2)
        logger.info("✅ Telegram Bot is now polling and ready to receive commands!")
    
    asyncio.create_task(log_ready_delayed())
    logger.info("Background monitoring tasks initialized.")

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            
        wav_path = tmp_ogg.name + ".wav"
        audio = AudioSegment.from_ogg(tmp_ogg.name)
        audio.export(wav_path, format="wav")
        
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="id-ID")
            
        await update.message.reply_text(f"🗣️ <b>Anda berkata:</b> {text}", parse_mode="HTML")
        
        update.message.text = text
        await message_handler(update, context)
        
        os.remove(tmp_ogg.name)
        os.remove(wav_path)
        
    except sr.UnknownValueError:
        await update.message.reply_text("❌ Suara tidak terdengar jelas.")
    except Exception as e:
        logger.error(f"Voice error: {e}")
        await update.message.reply_text("❌ Gagal memproses pesan suara.")

async def poll_terminal(user_id: str, context: ContextTypes.DEFAULT_TYPE, chat_id: int, agent_url: str, agent_api_key: str):
    token = _user_sessions.get(user_id)
    headers = {
        "X-API-Key": agent_api_key,
        "Authorization": f"Bearer {token}"
    }
    
    accumulated_output = ""
    
    while _terminal_mode.get(user_id):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{agent_url}/terminal/read/{user_id}", headers=headers, timeout=10)
                if response.status_code == 200:
                    output = response.json().get("output", "")
                    if output:
                        accumulated_output += output
                        if len(accumulated_output) > 2000 or "\n" in output:
                            text = f"<code>{accumulated_output[-4000:]}</code>"
                            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
                            accumulated_output = ""
                elif response.status_code == 401:
                    break
        except Exception as e:
            logger.error(f"Error polling terminal for {user_id}: {e}")
        
        await asyncio.sleep(1.5)
    
    if accumulated_output:
        await context.bot.send_message(chat_id=chat_id, text=f"<code>{accumulated_output}</code>", parse_mode="HTML")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    message_text = update.message.text.strip() if update.message.text else ""

    token = _user_sessions.get(user_id)
    if not token:
        await update.message.reply_text("🔐 Belum login. Gunakan /start untuk autentikasi.")
        return

    if not AuthManager.verify_session_token(token):
        del _user_sessions[user_id]
        save_current_sessions()
        await update.message.reply_text("⏰ Sesi expired. Silakan /start ulang.")
        return

    # Handle Multi-Agent Commands
    if message_text == "!status" or message_text == "!agents":
        agents = registry.get_all()
        if not agents:
            await update.message.reply_text("📉 Belum ada agent yang terdaftar.")
            return
        
        msg = "🖥️ <b>Daftar Agent:</b>\n"
        for aid in agents.keys():
            mark = "✅" if _user_active_agent.get(user_id) == aid else "▫️"
            msg += f"{mark} <code>{aid}</code>\n"
        msg += "\nGunakan <code>!select &lt;agent_id&gt;</code> untuk memilih target."
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    if message_text.startswith("!select "):
        target_agent = message_text.split(" ", 1)[1].strip()
        if registry.get_agent(target_agent):
            _user_active_agent[user_id] = target_agent
            await update.message.reply_text(f"🎯 Target diubah ke Agent: <b>{target_agent}</b>", parse_mode="HTML")
        else:
            await update.message.reply_text(f"❌ Agent '{target_agent}' tidak ditemukan.")
        return

    # Determine Active Agent
    active_agent_id = _user_active_agent.get(user_id)
    agents = registry.get_all()
    if not active_agent_id:
        if len(agents) == 1:
            active_agent_id = list(agents.keys())[0]
            _user_active_agent[user_id] = active_agent_id
            await update.message.reply_text(f"ℹ️ Auto-select Agent: <b>{active_agent_id}</b>", parse_mode="HTML")
        elif len(agents) > 1:
            await update.message.reply_text("⚠️ Anda memiliki lebih dari 1 Agent.\nGunakan <code>!select &lt;agent_id&gt;</code> terlebih dahulu.", parse_mode="HTML")
            return
        else:
            await update.message.reply_text("❌ Belum ada agent yang terdaftar pada sistem.")
            return

    agent_data = registry.get_agent(active_agent_id)
    if not agent_data:
        del _user_active_agent[user_id]
        await update.message.reply_text("❌ Agent yang dipilih sudah tidak tersedia di registry.")
        return
        
    AGENT_URL = f"http://{agent_data['host']}:{agent_data['port']}"
    AGENT_API_KEY = agent_data['api_key']

    if message_text in ["!term", "!exit"]:
        if message_text == "!term":
            if _terminal_mode.get(user_id):
                await update.message.reply_text("⚠️ Anda sudah berada dalam Mode Terminal.")
                return
            headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient() as client:
                try:
                    res = await client.post(f"{AGENT_URL}/terminal/start", json={"user_id": user_id}, headers=headers)
                    if res.status_code == 200:
                        _terminal_mode[user_id] = True
                        await update.message.reply_text(f"💻 <b>Mode Terminal Aktif ({active_agent_id})</b>", parse_mode="HTML")
                        # Pass AGENT_URL and AGENT_API_KEY directly since they are dynamically resolved
                        task = asyncio.create_task(poll_terminal(user_id, context, update.effective_chat.id, AGENT_URL, AGENT_API_KEY))
                        _terminal_tasks[user_id] = task
                    else:
                        await update.message.reply_text("❌ Gagal memulai terminal.")
                except Exception as e:
                    await update.message.reply_text(f"❌ Error: {e}")
        else:
            _terminal_mode[user_id] = False
            if user_id in _terminal_tasks:
                _terminal_tasks[user_id].cancel()
                del _terminal_tasks[user_id]
            headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient() as client:
                await client.post(f"{AGENT_URL}/terminal/stop", json={"user_id": user_id}, headers=headers)
            await update.message.reply_text("👋 Mode Terminal dinonaktifkan.")
        return

    if _terminal_mode.get(user_id):
        # Auto-inject safety flags for AI CLIs to prevent interactive blocking
        processed_text = message_text
        if message_text.startswith("gemini ") and "--yolo" not in message_text:
            processed_text = message_text.replace("gemini ", "gemini --yolo ", 1)
            logger.info(f"Auto-injected --yolo for gemini command from {user_id}")
        elif message_text.startswith("opencode ") and "--dangerously-skip-permissions" not in message_text:
            processed_text = message_text.replace("opencode ", "opencode --dangerously-skip-permissions ", 1)
            logger.info(f"Auto-injected --dangerously-skip-permissions for opencode command from {user_id}")

        headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
        
        # If terminal command is 'cd', update the global CWD in CommandHandler as well
        if message_text.startswith("cd "):
            target_dir = message_text[3:].strip()
            # We forward this to the agent's CWD state for dedicated commands
            async with httpx.AsyncClient() as client:
                await client.post(f"{AGENT_URL}/command", json={"command": f"!cd {target_dir}", "user_id": user_id}, headers=headers)

        async with httpx.AsyncClient() as client:
            try:
                await client.post(f"{AGENT_URL}/terminal/write", json={"user_id": user_id, "data": processed_text + "\n"}, headers=headers)
            except Exception as e:
                await update.message.reply_text(f"❌ Error writing to terminal: {e}")
        return

    if message_text.startswith("!schedule "):
        try:
            parts = message_text.split(" ", 3)
            if parts[1] == "in":
                time_str = parts[2]
                command_to_run = parts[3]
                
                # Parse time
                unit = time_str[-1]
                value = int(time_str[:-1])
                multiplier = {"s": 1, "m": 60, "h": 3600}.get(unit, 1)
                sleep_seconds = value * multiplier
                
                async def scheduled_task(delay, cmd):
                    await asyncio.sleep(delay)
                    # Fake update text and recurse
                    update.message.text = cmd
                    await message_handler(update, context)
                
                asyncio.create_task(scheduled_task(sleep_seconds, command_to_run))
                await update.message.reply_text(f"✅ Perintah `{command_to_run}` dijadwalkan berjalan dalam {time_str}.")
                return
        except Exception as e:
            await update.message.reply_text("❌ Format salah. Gunakan: `!schedule in 30m !lock`")
            return

    if not AuthManager.check_rate_limit(user_id):
        await update.message.reply_text("⚠️ Terlalu banyak perintah.")
        return

    processing_msg = await update.message.reply_text(f"⏳ <b>{active_agent_id}</b> sedang memproses...", parse_mode="HTML")
    
    # Send typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

    try:
        headers = {"X-API-Key": AGENT_API_KEY, "Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            res = await client.post(f"{AGENT_URL}/command", json={"command": message_text, "user_id": user_id}, headers=headers, timeout=60)

        # Delete processing message before sending result
        await processing_msg.delete()

        if res.status_code == 200:
            result = res.json()
            res_type = result.get("type")
            content = result.get("content")
            
            if res_type == "text":
                await update.message.reply_text(f"✅ <b>Hasil:</b>\n<code>{content}</code>", parse_mode="HTML")
            elif res_type == "image":
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.UPLOAD_PHOTO)
                import base64
                await update.message.reply_photo(base64.b64decode(content))
            elif res_type == "video":
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.UPLOAD_VIDEO)
                import base64
                if isinstance(content, dict):
                    await update.message.reply_video(base64.b64decode(content["data"]), filename=content.get("filename", "video.mp4"), caption="📹 Rekaman Layar Berhasil")
                else:
                    await update.message.reply_video(base64.b64decode(content), caption="📹 Live Stream Berhasil")
            elif res_type == "document":
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.UPLOAD_DOCUMENT)
                import base64
                doc_data = result.get("content", {})
                await update.message.reply_document(document=base64.b64decode(doc_data["data"]), filename=doc_data["filename"])
        elif res.status_code == 400:
            await update.message.reply_text(f"⚠️ <b>Permintaan Ditolak:</b>\n{res.json().get('detail')}", parse_mode="HTML")
        elif res.status_code == 401:
            await update.message.reply_text("❌ <b>Sesi Kadaluarsa:</b> Silakan login kembali dengan <code>/otp</code>", parse_mode="HTML")
        elif res.status_code == 404:
            await update.message.reply_text("❌ <b>Agent Tidak Merespons:</b> Endpoint tidak ditemukan.", parse_mode="HTML")
        else:
            await update.message.reply_text(f"❌ <b>Error Agent ({res.status_code}):</b> Gagal memproses perintah.", parse_mode="HTML")
            
    except httpx.TimeoutException:
        if 'processing_msg' in locals(): await processing_msg.delete()
        await update.message.reply_text("⏳ <b>Waktu Habis:</b> Agent terlalu lama merespons. Mungkin sedang memproses tugas berat.", parse_mode="HTML")
    except Exception as e:
        if 'processing_msg' in locals(): await processing_msg.delete()
        logger.error(f"Command error: {e}")
        await update.message.reply_text("❌ <b>Koneksi Gagal:</b> Tidak dapat menghubungi Agent. Pastikan Agent sedang online.", parse_mode="HTML")

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not AuthManager.is_user_allowed(user_id):
        await update.message.reply_text("❌ Akses ditolak.")
        return
    await update.message.reply_text("🔐 <b>Autentikasi Diperlukan</b>\n<code>/otp &lt;kode&gt;</code>", parse_mode="HTML")

async def otp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Gunakan: /otp 123456")
        return
    otp_code = context.args[0]
    if AuthManager.verify_otp(otp_code):
        token = AuthManager.generate_session_token(user_id)
        _user_sessions[user_id] = token
        save_current_sessions()
        await update.message.reply_text("✅ <b>Login berhasil!</b>", parse_mode="HTML")
    else:
        await update.message.reply_text("❌ OTP salah.")

async def logout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    token = _user_sessions.pop(user_id, None)
    save_current_sessions()
    if token:
        AuthManager.revoke_token(token)
    await update.message.reply_text("👋 Logout berhasil.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("otp", otp_handler))
    app.add_handler(CommandHandler("logout", logout_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, document_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))

    logger.info("Starting Telegram bot...")
    
    # Ensure event loop exists for Python 3.10+ (fixes RuntimeError in some environments)
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    app.run_polling(drop_pending_updates=True)
