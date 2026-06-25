# Blueprint Teknis: Remote Laptop Control via Mobile Messaging

> **Senior Software Architect & Security Engineer Blueprint**  
> Versi: 1.0 | Bahasa: Python 3.11+ / Node.js 20+  
> Lisensi: Personal Use Only — Gunakan hanya pada perangkat milik sendiri

---

## ⚠️ DISCLAIMER KEAMANAN

Sistem ini memberikan **kontrol penuh** atas laptop Anda dari jarak jauh.  
Pastikan:
- Hanya digunakan pada perangkat dan jaringan yang Anda miliki
- Tidak disebarkan ke pihak ketiga
- API Key dan token dijaga ketat
- Logging audit selalu aktif

---

## 1. ARSITEKTUR SISTEM

### 1.1 Komponen Utama

```
Mobile Client (HP)
    │
    │  [TLS 1.3 + E2E Encryption]
    ▼
Message Broker (Telegram API / WhatsApp Baileys / Termux SSH)
    │
    │  [Auth Layer: OTP + JWT + Rate Limiting]
    ▼
Command Router & Validator
    │
    ├──────────────────────────────────────┐
    ▼                                      ▼
AI Interpreter (NVIDIA NIM)          Explicit Command Parser
[Llama 3 / Nemotron]                 [Fallback / Default Mode]
    │                                      │
    └──────────────┬───────────────────────┘
                   ▼
         Laptop Agent (Python)
              │
    ┌─────────┼──────────────┐
    ▼         ▼              ▼
Command    Security       Audit
Executor   Sandbox        Logger
```

### 1.2 Alur Data (Data Flow)

```
1. User ketik "!screenshot" atau "Ambil foto layar" di HP
2. Pesan terenkripsi dikirim ke Telegram/WhatsApp Bot
3. Bot menerima via Webhook/Polling
4. Auth Layer validasi: token OTP + rate limit check
5. Command Router parse & sanitize input
   ├── Jika AI Mode ON → NIM API translate NL → command
   └── Jika AI Mode OFF/fallback → parse explicit command
6. Command dikirim ke Laptop Agent via encrypted channel
7. Agent eksekusi di sandbox yang terisolasi
8. Hasil (screenshot/output) dikirim balik ke HP
9. Semua aksi dicatat di audit log
```

### 1.3 Protokol Komunikasi

| Layer | Protokol | Library |
|-------|----------|---------|
| Transport | HTTPS/WSS | TLS 1.3 |
| Enkripsi Pesan | AES-256-GCM | `cryptography` (Python) |
| Auth | JWT + OTP | `python-jose`, `pyotp` |
| File Transfer | SFTP over SSH | `paramiko` |
| Bot-to-Agent | REST API lokal | `FastAPI` |

---

## 2. STRUKTUR FOLDER PROYEK

```
remote-laptop-control/
│
├── agent/                      # Laptop Agent (Python)
│   ├── __init__.py
│   ├── main.py                 # Entry point agent
│   ├── command_handler.py      # Handler perintah
│   ├── executor.py             # Eksekusi aman
│   ├── screenshot.py           # Module screenshot
│   ├── file_manager.py         # File transfer
│   └── system_monitor.py      # Monitor CPU/RAM
│
├── bot/                        # Bot Server
│   ├── telegram_bot.py         # Telegram handler
│   ├── whatsapp_bot.js         # WhatsApp (Baileys)
│   ├── auth.py                 # Autentikasi
│   ├── command_router.py       # Router & validator
│   └── rate_limiter.py         # Rate limiting
│
├── ai_module/                  # AI Interpreter (opsional)
│   ├── nim_client.py           # NVIDIA NIM API client
│   ├── fallback_parser.py      # Parser fallback
│   └── prompt_templates.py     # Prompt engineering
│
├── security/                   # Modul keamanan
│   ├── sandbox.py              # Sandboxing
│   ├── sanitizer.py            # Input sanitization
│   ├── audit_logger.py         # Audit logging
│   └── crypto.py               # Enkripsi/dekripsi
│
├── config/
│   ├── .env.example            # Template env vars
│   ├── config.yaml             # Konfigurasi utama
│   └── allowed_commands.yaml   # Whitelist perintah
│
├── logs/                       # Audit logs (git-ignored)
│   └── .gitkeep
│
├── docker/
│   ├── Dockerfile.agent        # Docker untuk agent
│   ├── Dockerfile.bot          # Docker untuk bot
│   └── docker-compose.yml      # Orchestration
│
├── tests/
│   ├── test_security.py
│   ├── test_commands.py
│   └── test_auth.py
│
├── requirements.txt            # Python deps
├── package.json                # Node.js deps (WhatsApp)
├── docs/BLUEPRINT.md           # Dokumen ini
└── README.md
```

---

## 3. KONFIGURASI & ENVIRONMENT VARIABLES

### 3.1 File `.env.example`

```bash
# ── BOT CREDENTIALS ──────────────────────────────────────
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
WHATSAPP_SESSION_PATH=./sessions/wa_session

# ── AUTH & SECURITY ──────────────────────────────────────
OTP_SECRET_KEY=your_base32_otp_secret_here         # generate: pyotp.random_base32()
JWT_SECRET_KEY=your_256bit_jwt_secret_here
ALLOWED_USER_IDS=123456789,987654321               # Telegram/WA user IDs
ENCRYPTION_KEY=your_32byte_aes_key_base64_here     # AES-256

# ── LAPTOP AGENT ─────────────────────────────────────────
AGENT_HOST=localhost
AGENT_PORT=8765
AGENT_API_KEY=your_internal_api_key_here           # Internal auth antara bot & agent

# ── NVIDIA NIM (OPSIONAL) ────────────────────────────────
NVIDIA_NIM_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxx       # Dari build.nvidia.com
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_MODEL=meta/llama-3.1-70b-instruct
AI_MODE_ENABLED=true                               # true/false

# ── RATE LIMITING ────────────────────────────────────────
MAX_COMMANDS_PER_MINUTE=10
MAX_FILE_SIZE_MB=50

# ── LOGGING ──────────────────────────────────────────────
LOG_LEVEL=INFO
LOG_FILE=./logs/audit.log
```

### 3.2 `config/allowed_commands.yaml` — Whitelist Perintah

```yaml
# Hanya perintah dalam daftar ini yang diizinkan
# TIDAK ADA wildcard atau shell expansion

safe_commands:
  screenshot:
    description: "Ambil screenshot layar"
    requires_confirmation: false
    sandbox_required: false

  system_info:
    description: "Info CPU, RAM, disk"
    requires_confirmation: false
    sandbox_required: false

  list_files:
    description: "List isi direktori (path terbatas)"
    requires_confirmation: false
    sandbox_required: false
    allowed_paths:
      - "~/Documents"
      - "~/Downloads"
      - "~/Desktop"

  get_file:
    description: "Kirim file ke user"
    requires_confirmation: true          # User harus konfirmasi
    sandbox_required: false
    max_size_mb: 50
    allowed_extensions: [pdf, txt, png, jpg, docx, xlsx]

  run_script:
    description: "Jalankan script Python/Bash"
    requires_confirmation: true
    sandbox_required: true               # WAJIB sandbox
    allowed_scripts_dir: "~/safe_scripts"

  reboot:
    description: "Restart laptop"
    requires_confirmation: true
    cooldown_minutes: 60                 # Minimal 1 jam antar reboot

  lock_screen:
    description: "Kunci layar laptop"
    requires_confirmation: false
    sandbox_required: false

  shutdown:
    description: "Matikan laptop"
    requires_confirmation: true
    double_confirm: true                 # Harus konfirmasi 2x

# Perintah yang SELALU diblokir (defense in depth)
blocked_patterns:
  - "rm -rf"
  - "mkfs"
  - "dd if="
  - "> /dev/sd"
  - "chmod 777"
  - "sudo su"
  - "passwd"
  - "curl.*|.*bash"
  - "wget.*|.*sh"
```

---

## 4. KODE SUMBER (SNIPPETS UTAMA)

### 4.1 `security/sanitizer.py` — Pencegahan Command Injection

```python
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

            allowed_dirs = [
                home / "Documents",
                home / "Downloads",
                home / "Desktop",
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
```

### 4.2 `bot/auth.py` — Autentikasi OTP + JWT

```python
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
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from functools import lru_cache
from loguru import logger


OTP_SECRET = os.environ["OTP_SECRET_KEY"]
JWT_SECRET = os.environ["JWT_SECRET_KEY"]
ALLOWED_USERS = set(
    os.environ.get("ALLOWED_USER_IDS", "").split(",")
)

# Token blacklist (untuk logout/revoke)
_revoked_tokens: set[str] = set()

# Rate limiting state
_user_command_times: dict[str, list[float]] = {}
MAX_PER_MINUTE = int(os.environ.get("MAX_COMMANDS_PER_MINUTE", "10"))


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
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=4),
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
        now = time.time()
        user_times = _user_command_times.get(user_id, [])

        # Hapus entry lebih dari 60 detik yang lalu
        user_times = [t for t in user_times if now - t < 60]

        if len(user_times) >= MAX_PER_MINUTE:
            logger.warning(f"Rate limit exceeded for user: {user_id}")
            return False

        user_times.append(now)
        _user_command_times[user_id] = user_times
        return True


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
```

### 4.3 `bot/telegram_bot.py` — Inisialisasi Bot Telegram

```python
"""
Telegram Bot Handler
Menggunakan python-telegram-bot v21 (async)
"""
import os
import asyncio
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
        "🔐 *Autentikasi Diperlukan*

"
        "Kirim OTP 6-digit dari Google Authenticator:
"
        "`/otp <kode_6_digit>`",
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
            "✅ *Login berhasil!* Sesi aktif 4 jam.

"
            "Perintah tersedia:
"
            "`!screenshot` — Screenshot layar
"
            "`!sysinfo` — Info sistem
"
            "`!ls <path>` — List file
"
            "`!get <file>` — Kirim file
"
            "`!lock` — Kunci layar
"
            "`!help` — Bantuan

"
            "🤖 Mode AI: Ketik perintah natural language",
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
                result = result[:3900] + "
...[truncated]"
            await update.message.reply_text(f"```
{result}
```", parse_mode="Markdown")

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
```

### 4.4 `bot/whatsapp_bot.js` — Inisialisasi WhatsApp via Baileys

```javascript
/**
 * WhatsApp Bot Handler menggunakan @whiskeysockets/baileys
 * Node.js 20+ required
 */
const {
  default: makeWASocket,
  DisconnectReason,
  useMultiFileAuthState,
  isJidGroup,
} = require("@whiskeysockets/baileys");
const { Boom } = require("@hapi/boom");
const axios = require("axios");
const pino = require("pino");
require("dotenv").config();

const ALLOWED_NUMBERS = (process.env.ALLOWED_USER_IDS || "").split(",");
const AGENT_URL = `http://${process.env.AGENT_HOST}:${process.env.AGENT_PORT}`;
const AGENT_API_KEY = process.env.AGENT_API_KEY;

// Sesi aktif: {phoneNumber: jwt_token}
const activeSessions = new Map();

async function connectWhatsApp() {
  const { state, saveCreds } = await useMultiFileAuthState(
    process.env.WHATSAPP_SESSION_PATH || "./sessions/wa_session"
  );

  const sock = makeWASocket({
    logger: pino({ level: "warn" }),
    auth: state,
    printQRInTerminal: true,  // Scan QR untuk login pertama
    getMessage: async () => undefined,
  });

  // Simpan credentials saat update
  sock.ev.on("creds.update", saveCreds);

  // Handle koneksi/diskoneksi
  sock.ev.on("connection.update", ({ connection, lastDisconnect }) => {
    if (connection === "close") {
      const shouldReconnect =
        new Boom(lastDisconnect?.error)?.output?.statusCode !==
        DisconnectReason.loggedOut;

      console.log("Connection closed. Reconnecting:", shouldReconnect);
      if (shouldReconnect) connectWhatsApp();
    } else if (connection === "open") {
      console.log("✅ WhatsApp connected!");
    }
  });

  // Handle pesan masuk
  sock.ev.on("messages.upsert", async ({ messages }) => {
    const msg = messages[0];

    // Hanya proses pesan baru, bukan dari grup
    if (!msg.message || isJidGroup(msg.key.remoteJid)) return;

    const sender = msg.key.remoteJid.replace("@s.whatsapp.net", "");
    const text =
      msg.message.conversation ||
      msg.message.extendedTextMessage?.text ||
      "";

    if (!text) return;

    // Cek whitelist nomor
    if (!ALLOWED_NUMBERS.includes(sender)) {
      console.warn(`Unauthorized WA access from: ${sender}`);
      await sock.sendMessage(msg.key.remoteJid, {
        text: "❌ Akses ditolak.",
      });
      return;
    }

    // Handle OTP login
    if (text.startsWith("/otp ")) {
      const otpCode = text.split(" ")[1];
      try {
        const res = await axios.post(`${AGENT_URL}/auth/verify-otp`, {
          user_id: sender,
          otp: otpCode,
        }, {
          headers: { "X-API-Key": AGENT_API_KEY }
        });

        if (res.data.token) {
          activeSessions.set(sender, res.data.token);
          await sock.sendMessage(msg.key.remoteJid, {
            text: "✅ Login berhasil! Kirim perintah untuk mulai.",
          });
        }
      } catch {
        await sock.sendMessage(msg.key.remoteJid, {
          text: "❌ OTP salah atau expired.",
        });
      }
      return;
    }

    // Cek sesi aktif
    const token = activeSessions.get(sender);
    if (!token) {
      await sock.sendMessage(msg.key.remoteJid, {
        text: "🔐 Belum login. Kirim `/otp <kode>` dari Google Authenticator.",
      });
      return;
    }

    // Forward ke agent
    try {
      const res = await axios.post(`${AGENT_URL}/command`, {
        command: text,
        user_id: sender,
      }, {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-API-Key": AGENT_API_KEY,
        },
        timeout: 30000,
      });

      const { type, content } = res.data;

      if (type === "text") {
        await sock.sendMessage(msg.key.remoteJid, { text: content });
      } else if (type === "image") {
        // content adalah base64 gambar
        const buffer = Buffer.from(content, "base64");
        await sock.sendMessage(msg.key.remoteJid, {
          image: buffer,
          caption: "📸 Screenshot",
        });
      } else if (type === "document") {
        const buffer = Buffer.from(content.data, "base64");
        await sock.sendMessage(msg.key.remoteJid, {
          document: buffer,
          fileName: content.filename,
          mimetype: content.mimetype,
        });
      }
    } catch (err) {
      console.error("Agent error:", err.message);
      await sock.sendMessage(msg.key.remoteJid, {
        text: `❌ Error: ${err.message}`,
      });
    }
  });
}

connectWhatsApp();
```

### 4.5 `agent/command_handler.py` — Handler Perintah Dasar

```python
"""
Command Handler — Eksekusi perintah yang sudah divalidasi
Setiap handler WAJIB melalui sanitizer sebelum eksekusi
"""
import os
import subprocess
import platform
import psutil
import shutil
from pathlib import Path
from PIL import ImageGrab  # atau mss untuk multi-monitor
import mss
import mss.tools
from loguru import logger
from security.sanitizer import InputSanitizer
from security.sandbox import SandboxExecutor


class CommandHandler:

    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.sandbox = SandboxExecutor()

    async def handle_screenshot(self) -> bytes:
        """Ambil screenshot dan return sebagai bytes PNG."""
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Monitor utama
            screenshot = sct.grab(monitor)
            png_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)

        logger.info("Screenshot captured")
        return png_bytes

    async def handle_sysinfo(self) -> str:
        """Ambil informasi sistem."""
        cpu_percent = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        uptime_seconds = (
            psutil.boot_time()
        )

        info = (
            f"💻 *System Info*
"
            f"OS: {platform.system()} {platform.release()}
"
            f"CPU: {cpu_percent}%
"
            f"RAM: {ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB ({ram.percent}%)
"
            f"Disk: {disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB ({disk.percent}%)
"
            f"Python: {platform.python_version()}"
        )
        return info

    async def handle_list_files(self, path: str) -> str:
        """List isi direktori — dengan validasi path."""
        safe_path = self.sanitizer.sanitize_filepath(path)
        if not safe_path:
            return "❌ Path tidak diizinkan atau tidak valid."

        target = Path(safe_path)
        if not target.exists() or not target.is_dir():
            return "❌ Direktori tidak ditemukan."

        entries = []
        for item in sorted(target.iterdir()):
            if item.is_dir():
                entries.append(f"📁 {item.name}/")
            else:
                size = item.stat().st_size
                size_str = f"{size // 1024}KB" if size > 1024 else f"{size}B"
                entries.append(f"📄 {item.name} ({size_str})")

        return f"📂 `{safe_path}`:
" + "
".join(entries[:50])  # Max 50 entries

    async def handle_get_file(self, filepath: str) -> dict:
        """Kirim file ke user — dengan validasi ekstensi dan ukuran."""
        safe_path = self.sanitizer.sanitize_filepath(filepath)
        if not safe_path:
            return {"error": "Path tidak diizinkan."}

        target = Path(safe_path)
        if not target.exists() or not target.is_file():
            return {"error": "File tidak ditemukan."}

        # Cek ekstensi
        allowed_ext = {".pdf", ".txt", ".png", ".jpg", ".jpeg", ".docx", ".xlsx", ".log"}
        if target.suffix.lower() not in allowed_ext:
            return {"error": f"Ekstensi {target.suffix} tidak diizinkan."}

        # Cek ukuran (max 50MB)
        max_size = int(os.environ.get("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024
        if target.stat().st_size > max_size:
            return {"error": "File terlalu besar (max 50MB)."}

        with open(target, "rb") as f:
            return {
                "filename": target.name,
                "data": f.read(),
                "mimetype": _guess_mimetype(target.suffix),
            }

    async def handle_run_script(self, script_name: str, user_id: str) -> str:
        """
        Jalankan script dari direktori aman — WAJIB di sandbox.
        Hanya file .py dan .sh dari ~/safe_scripts yang diizinkan.
        """
        safe_dir = Path.home() / "safe_scripts"
        script_path = (safe_dir / script_name).resolve()

        # Pastikan script ada di dalam safe_dir
        try:
            script_path.relative_to(safe_dir)
        except ValueError:
            return "❌ Path traversal terdeteksi."

        if not script_path.exists():
            return f"❌ Script '{script_name}' tidak ditemukan di ~/safe_scripts."

        if script_path.suffix not in {".py", ".sh"}:
            return "❌ Hanya script .py dan .sh yang diizinkan."

        # Eksekusi dalam sandbox
        result = await self.sandbox.run_in_sandbox(str(script_path), user_id)
        return result

    async def handle_lock_screen(self) -> str:
        """Kunci layar laptop."""
        system = platform.system()
        if system == "Linux":
            # Coba beberapa window manager
            for cmd in ["loginctl lock-session", "xdg-screensaver lock", "gnome-screensaver-command -l"]:
                try:
                    subprocess.run(cmd.split(), timeout=5, check=True)
                    return "🔒 Layar dikunci."
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
        elif system == "Darwin":  # macOS
            subprocess.run(["pmset", "displaysleepnow"])
            return "🔒 Layar dikunci."
        elif system == "Windows":
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return "🔒 Layar dikunci."

        return "❌ Gagal mengunci layar."

    async def handle_reboot(self, confirmed: bool = False) -> str:
        """Restart laptop — butuh konfirmasi."""
        if not confirmed:
            return (
                "⚠️ Yakin ingin restart?
"
                "Balas: `!reboot confirm`"
            )
        system = platform.system()
        if system == "Linux":
            subprocess.Popen(["sudo", "reboot"])
        elif system == "Darwin":
            subprocess.Popen(["sudo", "reboot"])
        elif system == "Windows":
            subprocess.Popen(["shutdown", "/r", "/t", "10"])
        return "🔄 Laptop akan restart dalam 10 detik..."


def _guess_mimetype(suffix: str) -> str:
    mimetypes = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".log": "text/plain",
    }
    return mimetypes.get(suffix.lower(), "application/octet-stream")
```

### 4.6 `ai_module/nim_client.py` — NVIDIA NIM dengan Fallback Logic

```python
"""
NVIDIA NIM AI Interpreter
Menerjemahkan natural language → perintah sistem yang valid dan aman
Memiliki fallback logic jika API tidak tersedia
"""
import os
import re
import json
import asyncio
import httpx
from typing import Optional
from loguru import logger

NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
NIM_BASE_URL = os.environ.get(
    "NVIDIA_NIM_BASE_URL",
    "https://integrate.api.nvidia.com/v1"
)
NIM_MODEL = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct")
AI_ENABLED = os.environ.get("AI_MODE_ENABLED", "true").lower() == "true"

# Timeout untuk API call
API_TIMEOUT = 15.0

# System prompt yang ketat untuk NIM — batasi output hanya ke perintah valid
SYSTEM_PROMPT = """Kamu adalah interpreter perintah untuk sistem remote laptop control.
Tugasmu HANYA menerjemahkan permintaan user ke salah satu perintah berikut:

PERINTAH VALID:
- !screenshot
- !sysinfo
- !ls <path>
- !get <filepath>
- !lock
- !reboot
- !run <script_name>

ATURAN KETAT:
1. Jawab HANYA dengan satu perintah dari daftar di atas, tidak lebih
2. JANGAN pernah menambahkan argumen berbahaya seperti rm, dd, sudo, dll
3. Jika permintaan tidak bisa dipetakan ke perintah valid, jawab: UNKNOWN
4. Jika permintaan berpotensi berbahaya, jawab: BLOCKED
5. Format output: JSON {"command": "...", "reason": "..."}

Contoh:
User: "Ambil foto layar dong"
Output: {"command": "!screenshot", "reason": "Mengambil screenshot layar"}

User: "Hapus semua file"
Output: {"command": "BLOCKED", "reason": "Perintah destruktif tidak diizinkan"}
"""


class NIMClient:

    def __init__(self):
        self.enabled = AI_ENABLED and bool(NIM_API_KEY)
        if not NIM_API_KEY and AI_ENABLED:
            logger.warning("AI mode enabled tapi NVIDIA_NIM_API_KEY tidak di-set. Fallback ke explicit mode.")

    async def translate_to_command(self, natural_input: str) -> Optional[str]:
        """
        Terjemahkan natural language ke perintah sistem.
        Return None jika harus fallback ke explicit parser.
        """
        if not self.enabled:
            return None  # Signal untuk fallback

        # Cek apakah input sudah berupa explicit command
        if natural_input.startswith("!"):
            return None  # Langsung ke explicit parser

        try:
            return await self._call_nim_api(natural_input)
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning(f"NIM API timeout/connection error: {e}. Falling back to explicit mode.")
            return None
        except Exception as e:
            logger.error(f"NIM API unexpected error: {e}. Falling back to explicit mode.")
            return None

    async def _call_nim_api(self, user_input: str) -> Optional[str]:
        """Panggil NVIDIA NIM API."""
        headers = {
            "Authorization": f"Bearer {NIM_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": NIM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input[:500]},  # Batasi input
            ],
            "max_tokens": 100,
            "temperature": 0.1,  # Rendah untuk konsistensi
        }

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.post(
                f"{NIM_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        raw_output = data["choices"][0]["message"]["content"].strip()
        logger.debug(f"NIM raw output: {raw_output}")

        # Parse JSON response
        try:
            parsed = json.loads(raw_output)
            command = parsed.get("command", "UNKNOWN")
            reason = parsed.get("reason", "")

            if command in ("UNKNOWN", "BLOCKED"):
                logger.info(f"NIM blocked/unknown: {reason}")
                return f"__NIM_{command}__:{reason}"

            # Validasi command yang dihasilkan AI tetap aman
            if not self._validate_ai_output(command):
                logger.warning(f"NIM output failed validation: {command}")
                return None

            logger.info(f"NIM translated '{user_input[:50]}' → '{command}'")
            return command

        except json.JSONDecodeError:
            logger.warning(f"NIM returned non-JSON: {raw_output}")
            return None

    def _validate_ai_output(self, command: str) -> bool:
        """
        VALIDASI KEDUA pada output AI.
        Meskipun AI sudah diberi prompt ketat, selalu validasi lagi.
        """
        valid_commands = {
            "!screenshot", "!sysinfo", "!lock", "!reboot"
        }

        # Perintah dengan argumen
        valid_prefixes = ("!ls ", "!get ", "!run ")

        if command in valid_commands:
            return True

        if any(command.startswith(p) for p in valid_prefixes):
            # Cek argumen tidak mengandung karakter berbahaya
            arg = command.split(" ", 1)[1] if " " in command else ""
            dangerous_chars = set(";&|`$\x00")
            return not any(c in arg for c in dangerous_chars)

        return False


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


class CommandInterpreter:
    """
    Orchestrator utama: coba NIM dulu, fallback ke explicit parser.
    """

    def __init__(self):
        self.nim = NIMClient()
        self.fallback = FallbackParser()

    async def interpret(self, user_input: str) -> tuple[Optional[str], list[str]]:
        """
        Interpretasikan input user.
        Return (command_name, args)
        """
        # Coba AI translation dulu
        ai_result = await self.nim.translate_to_command(user_input)

        if ai_result is not None:
            # AI berhasil translate
            if ai_result.startswith("__NIM_"):
                # AI memblokir atau tidak mengenali
                return None, []
            # Parse hasil AI seperti explicit command
            return self.fallback.parse(ai_result)

        # Fallback ke explicit parser
        logger.debug(f"Using fallback parser for: {user_input}")
        return self.fallback.parse(user_input)
```

### 4.7 `security/sandbox.py` — Sandboxing dengan Docker/firejail

```python
"""
Sandbox Executor — Isolasi eksekusi script berbahaya
Menggunakan firejail (Linux) atau Docker container
"""
import os
import asyncio
import subprocess
import platform
import tempfile
from pathlib import Path
from loguru import logger

SANDBOX_TIMEOUT = 30  # detik
USE_DOCKER = os.environ.get("SANDBOX_USE_DOCKER", "false").lower() == "true"


class SandboxExecutor:

    def __init__(self):
        self.system = platform.system()
        self.has_firejail = self._check_firejail()
        self.has_docker = self._check_docker()

    def _check_firejail(self) -> bool:
        try:
            subprocess.run(["firejail", "--version"], capture_output=True, timeout=3)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_docker(self) -> bool:
        try:
            subprocess.run(["docker", "info"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def run_in_sandbox(self, script_path: str, user_id: str) -> str:
        """
        Jalankan script dalam sandbox yang terisolasi.
        Pilih metode sandbox terbaik yang tersedia.
        """
        logger.info(f"Sandbox exec: {script_path} by {user_id}")

        if USE_DOCKER and self.has_docker:
            return await self._run_docker(script_path)
        elif self.has_firejail and self.system == "Linux":
            return await self._run_firejail(script_path)
        else:
            return await self._run_restricted(script_path)

    async def _run_firejail(self, script_path: str) -> str:
        """
        Eksekusi dengan firejail — isolasi filesystem, network, proses.
        """
        path = Path(script_path)
        cmd = [
            "firejail",
            "--quiet",
            "--noprofile",
            "--private",           # Filesystem sementara
            "--net=none",          # Tanpa akses internet
            "--noroot",            # Tidak bisa jadi root
            "--rlimit-cpu=10",     # Max 10 detik CPU
            "--rlimit-as=268435456",  # Max 256MB RAM
            "python3" if path.suffix == ".py" else "bash",
            script_path,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=SANDBOX_TIMEOUT
            )

            if proc.returncode != 0:
                return f"Script error:
{stderr.decode()[:500]}"

            return stdout.decode()[:2000]  # Batasi output

        except asyncio.TimeoutError:
            proc.kill()
            return "❌ Timeout: script melebihi 30 detik."

    async def _run_docker(self, script_path: str) -> str:
        """
        Eksekusi dalam Docker container yang sangat terbatas.
        """
        path = Path(script_path)
        runtime = "python:3.11-slim" if path.suffix == ".py" else "bash:5"
        exec_cmd = f"python /script{path.suffix}" if path.suffix == ".py" else f"bash /script{path.suffix}"

        cmd = [
            "docker", "run",
            "--rm",                          # Hapus container setelah selesai
            "--network", "none",             # Tanpa internet
            "--memory", "256m",              # Max 256MB RAM
            "--cpus", "0.5",                 # Max 0.5 CPU
            "--read-only",                   # Filesystem read-only
            "--security-opt", "no-new-privileges",
            "--user", "nobody",              # Jalankan sebagai nobody
            "-v", f"{script_path}:/script{path.suffix}:ro",  # Mount script read-only
            "--timeout", str(SANDBOX_TIMEOUT),
            runtime,
            *exec_cmd.split(),
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=SANDBOX_TIMEOUT + 5
            )

            if proc.returncode != 0:
                return f"Docker exec error:
{stderr.decode()[:500]}"

            return stdout.decode()[:2000]

        except asyncio.TimeoutError:
            return "❌ Timeout: Docker container dihentikan."

    async def _run_restricted(self, script_path: str) -> str:
        """
        Fallback: eksekusi dengan resource limits minimal.
        Gunakan jika firejail dan Docker tidak tersedia.
        """
        path = Path(script_path)
        cmd = (
            ["python3", script_path]
            if path.suffix == ".py"
            else ["bash", script_path]
        )

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={
                    "PATH": "/usr/local/bin:/usr/bin:/bin",
                    "HOME": str(Path.home()),
                    "PYTHONPATH": "",  # Bersihkan PYTHONPATH
                }
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=SANDBOX_TIMEOUT
            )

            if proc.returncode != 0:
                return f"Error:
{stderr.decode()[:500]}"

            return stdout.decode()[:2000]

        except asyncio.TimeoutError:
            proc.kill()
            return "❌ Timeout: script dihentikan setelah 30 detik."
```

### 4.8 `security/audit_logger.py` — Logging Audit

```python
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
```

### 4.9 `agent/main.py` — FastAPI Agent Server

```python
"""
Laptop Agent — FastAPI server yang menerima perintah dari bot
Jalankan di laptop yang ingin dikontrol
"""
import os
import base64
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from loguru import logger
from .command_handler import CommandHandler
from bot.command_router import CommandRouter
from security.audit_logger import AuditLogger
from security.sanitizer import InputSanitizer
from ai_module.nim_client import CommandInterpreter

AGENT_API_KEY = os.environ["AGENT_API_KEY"]
api_key_header = APIKeyHeader(name="X-API-Key")

handler = CommandHandler()
router = CommandRouter()
auditor = AuditLogger()
sanitizer = InputSanitizer()
interpreter = CommandInterpreter()


class CommandRequest(BaseModel):
    command: str
    user_id: str


class OTPRequest(BaseModel):
    user_id: str
    otp: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Laptop Agent started")
    yield
    logger.info("Laptop Agent shutdown")


app = FastAPI(
    title="Remote Laptop Agent",
    docs_url=None,   # Sembunyikan docs di produksi
    redoc_url=None,
    lifespan=lifespan,
)


async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != AGENT_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


@app.post("/auth/verify-otp")
async def verify_otp(request: OTPRequest, _=Depends(verify_api_key)):
    from bot.auth import AuthManager
    if AuthManager.verify_otp(request.otp):
        token = AuthManager.generate_session_token(request.user_id)
        return {"token": token}
    raise HTTPException(status_code=401, detail="Invalid OTP")


@app.post("/command")
async def execute_command(
    request: CommandRequest,
    authorization: str = Header(...),
    _=Depends(verify_api_key),
):
    """Endpoint utama untuk eksekusi perintah."""
    from bot.auth import AuthManager

    # Verifikasi JWT dari bot
    token = authorization.replace("Bearer ", "")
    verified_user = AuthManager.verify_session_token(token)
    if not verified_user or verified_user != request.user_id:
        raise HTTPException(status_code=401, detail="Invalid session")

    # Sanitasi input
    clean_input = sanitizer.sanitize_command(request.command)
    if not clean_input:
        auditor.log_security_alert(request.user_id, "INJECTION_ATTEMPT", request.command)
        raise HTTPException(status_code=400, detail="Input tidak valid atau berbahaya")

    # Interpretasi perintah (AI atau fallback)
    command_name, args = await interpreter.interpret(clean_input)

    if not command_name:
        return {"type": "text", "content": "❓ Perintah tidak dikenali. Ketik `!help` untuk bantuan."}

    # Eksekusi berdasarkan command
    try:
        if command_name == "screenshot":
            img_bytes = await handler.handle_screenshot()
            auditor.log_event(request.user_id, "SCREENSHOT", "")
            return {"type": "image", "content": base64.b64encode(img_bytes).decode()}

        elif command_name == "sysinfo":
            info = await handler.handle_sysinfo()
            auditor.log_event(request.user_id, "SYSINFO", "")
            return {"type": "text", "content": info}

        elif command_name == "list_files":
            path = args[0] if args else str(Path.home())
            result = await handler.handle_list_files(path)
            auditor.log_event(request.user_id, "LIST_FILES", path[:50])
            return {"type": "text", "content": result}

        elif command_name == "get_file":
            if not args:
                return {"type": "text", "content": "❌ Gunakan: !get <filepath>"}
            file_data = await handler.handle_get_file(args[0])
            if "error" in file_data:
                return {"type": "text", "content": f"❌ {file_data['error']}"}
            auditor.log_event(request.user_id, "GET_FILE", args[0][:50])
            return {
                "type": "document",
                "content": {
                    "data": base64.b64encode(file_data["data"]).decode(),
                    "filename": file_data["filename"],
                    "mimetype": file_data["mimetype"],
                }
            }

        elif command_name == "lock_screen":
            result = await handler.handle_lock_screen()
            auditor.log_event(request.user_id, "LOCK_SCREEN", "")
            return {"type": "text", "content": result}

        elif command_name == "reboot":
            confirmed = len(args) > 0 and args[0] == "confirm"
            result = await handler.handle_reboot(confirmed)
            auditor.log_event(request.user_id, "REBOOT", f"confirmed={confirmed}")
            return {"type": "text", "content": result}

        elif command_name == "run_script":
            if not args:
                return {"type": "text", "content": "❌ Gunakan: !run <nama_script.py>"}
            result = await handler.handle_run_script(args[0], request.user_id)
            auditor.log_event(request.user_id, "RUN_SCRIPT", args[0][:50])
            return {"type": "text", "content": result}

        elif command_name == "help":
            return {"type": "text", "content": HELP_TEXT}

        else:
            return {"type": "text", "content": "❓ Perintah tidak dikenal."}

    except Exception as e:
        logger.error(f"Command execution error: {e}")
        auditor.log_event(request.user_id, "COMMAND_ERROR", str(e), success=False)
        raise HTTPException(status_code=500, detail="Internal agent error")


HELP_TEXT = """
🤖 *Remote Laptop Control — Help*

*Perintah Tersedia:*
`!screenshot` — Screenshot layar
`!sysinfo` — Info CPU/RAM/Disk
`!ls <path>` — List isi folder
`!get <file>` — Kirim file ke HP
`!lock` — Kunci layar
`!reboot` — Restart (butuh konfirmasi)
`!run <script>` — Jalankan script aman
`!logout` — Keluar dari sesi
`!help` — Tampilkan bantuan ini

*Mode AI (jika aktif):*
Ketik perintah natural language seperti:
"Ambil screenshot layar sekarang"
"Tampilkan info sistem"
"Kunci laptopku"
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",  # HANYA localhost — jangan 0.0.0.0
        port=int(os.environ.get("AGENT_PORT", "8765")),
        ssl_keyfile=os.environ.get("SSL_KEYFILE"),
        ssl_certfile=os.environ.get("SSL_CERTFILE"),
    )
```

---

## 5. DOCKER DEPLOYMENT

### `docker/docker-compose.yml`

```yaml
version: "3.9"

services:
  laptop-agent:
    build:
      context: ..
      dockerfile: docker/Dockerfile.agent
    container_name: laptop-agent
    restart: unless-stopped
    network_mode: host          # Akses localhost hanya
    environment:
      - AGENT_HOST=localhost
      - AGENT_PORT=8765
    env_file:
      - ../.env
    volumes:
      - ../logs:/app/logs       # Persist logs
      - ~/.ssh:/root/.ssh:ro    # SSH keys (read-only)
      - ~/safe_scripts:/home/user/safe_scripts:ro
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL                     # Hapus semua Linux capabilities
    cap_add:
      - DAC_OVERRIDE            # Hanya yang diperlukan
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m

  telegram-bot:
    build:
      context: ..
      dockerfile: docker/Dockerfile.bot
    container_name: telegram-bot
    restart: unless-stopped
    depends_on:
      - laptop-agent
    env_file:
      - ../.env
    volumes:
      - ../logs:/app/logs
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
```

### `docker/Dockerfile.agent`

```dockerfile
FROM python:3.11-slim

# Non-root user untuk keamanan
RUN useradd -m -u 1000 -s /bin/bash agentuser

WORKDIR /app

# Install deps sistem minimal
RUN apt-get update && apt-get install -y --no-install-recommends 
    scrot 
    firejail 
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=agentuser:agentuser . .

USER agentuser

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s 
    CMD curl -f http://localhost:8765/health || exit 1

CMD ["python", "-m", "uvicorn", "agent.main:app", 
     "--host", "127.0.0.1", "--port", "8765"]
```

---

## 6. REQUIREMENTS

### `requirements.txt` (Python)

```
# Bot & Framework
python-telegram-bot==21.5
fastapi==0.111.0
uvicorn[standard]==0.30.1
httpx==0.27.0
pydantic==2.7.0
websockets==12.0

# Autentikasi
pyotp==2.9.0
python-jose[cryptography]==3.3.0
passlib==1.7.4

# Keamanan & Kriptografi
cryptography==42.0.8
python-dotenv==1.0.1

# Agent tools
Pillow==10.3.0
mss==9.0.2                 # Screenshot cross-platform
psutil==5.9.8              # System monitoring
paramiko==3.4.0            # SSH/SFTP
PyYAML==6.0.1

# Logging
loguru==0.7.2

# Rate limiting
slowapi==0.1.9
```

### `package.json` (Node.js — WhatsApp)

```json
{
  "name": "wa-remote-bot",
  "version": "1.0.0",
  "type": "commonjs",
  "scripts": {
    "start": "node bot/whatsapp_bot.js",
    "dev": "nodemon bot/whatsapp_bot.js"
  },
  "dependencies": {
    "@whiskeysockets/baileys": "^6.7.0",
    "@hapi/boom": "^10.0.1",
    "axios": "^1.7.2",
    "dotenv": "^16.4.5",
    "pino": "^9.2.0",
    "qrcode-terminal": "^0.12.0"
  }
}
```

---

## 7. PANDUAN INSTALASI STEP-BY-STEP

### 7.1 Persiapan (Semua Platform)

```bash
# 1. Clone/buat folder proyek
mkdir remote-laptop-control && cd remote-laptop-control

# 2. Buat virtual environment Python
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. Install dependencies Python
pip install -r requirements.txt

# 4. Install dependencies Node.js (untuk WhatsApp)
npm install

# 5. Salin template env
cp config/.env.example .env
```

### 7.2 Konfigurasi Kredensial

```bash
# Generate OTP Secret untuk Google Authenticator
python3 -c "import pyotp; print(pyotp.random_base32())"
# → Salin ke OTP_SECRET_KEY di .env
# → Scan QR atau masukkan manual ke Google Authenticator

# Generate JWT Secret
python3 -c "import secrets; print(secrets.token_hex(32))"
# → Salin ke JWT_SECRET_KEY di .env

# Generate Internal API Key (bot ↔ agent)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# → Salin ke AGENT_API_KEY di .env

# Dapatkan Telegram Bot Token:
# 1. Buka @BotFather di Telegram
# 2. /newbot → ikuti instruksi
# 3. Salin token ke TELEGRAM_BOT_TOKEN

# Dapatkan Telegram User ID Anda:
# Buka @userinfobot → /start → salin ID ke ALLOWED_USER_IDS

# NVIDIA NIM API Key (opsional):
# 1. Daftar di https://build.nvidia.com
# 2. Generate API key
# 3. Salin ke NVIDIA_NIM_API_KEY di .env
```

### 7.3 Setup Google Authenticator

```bash
# Generate QR code untuk Google Authenticator
python3 -c "
import pyotp, qrcode, os
from dotenv import load_dotenv

load_dotenv()
secret = os.environ['OTP_SECRET_KEY']
totp = pyotp.TOTP(secret)
uri = totp.provisioning_uri(name='MyLaptop', issuer_name='RemoteControl')
print('Scan URI ini di Google Authenticator:')
print(uri)
print()
print('Atau masukkan secret manual:', secret)
"
```

### 7.4 Menjalankan Agent di Laptop

```bash
# Linux — pasang firejail untuk sandboxing
sudo apt install firejail  # Ubuntu/Debian
# atau
sudo pacman -S firejail    # Arch

# Jalankan agent
source venv/bin/activate
python -m agent.main

# Verifikasi berjalan
curl http://localhost:8765/health
```

### 7.5 Menjalankan Bot Telegram

```bash
# Di terminal terpisah
source venv/bin/activate
python -m bot.telegram_bot
```

### 7.6 Menjalankan Bot WhatsApp

```bash
# Di terminal terpisah
node bot/whatsapp_bot.js
# Scan QR code yang muncul dengan WhatsApp HP Anda
```

### 7.7 Cara Akses via Termux (SSH langsung)

```bash
# Di Termux HP Android:
pkg install openssh

# Generate SSH key
ssh-keygen -t ed25519 -f ~/.ssh/laptop_key

# Salin public key ke laptop
# Di laptop:
cat >> ~/.ssh/authorized_keys

# Sambung ke laptop
ssh -i ~/.ssh/laptop_key -p 22 username@laptop-ip

# Atau via ngrok untuk akses dari mana saja
# Di laptop:
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo apt-key add -
sudo apt install ngrok
ngrok tcp 22
# Salin address ngrok ke Termux untuk SSH
```

### 7.8 Menjalankan dengan Docker (Rekomendasi Produksi)

```bash
# Build images
docker compose -f docker/docker-compose.yml build

# Jalankan semua services
docker compose -f docker/docker-compose.yml up -d

# Lihat logs
docker compose -f docker/docker-compose.yml logs -f

# Stop
docker compose -f docker/docker-compose.yml down
```

---

## 8. PROTOKOL KEAMANAN (RANGKUMAN)

### Threat Model & Mitigasi

| Ancaman | Mitigasi |
|---------|----------|
| Unauthorized access | User ID whitelist + OTP + JWT |
| Command injection | Regex sanitizer + karakter blacklist |
| Path traversal | `Path.resolve()` + allowed_paths whitelist |
| Brute force OTP | Rate limiting (10 req/mnt) + TOTP time window kecil |
| Token theft | JWT expiry 4 jam + token blacklist (logout) |
| Malicious script | Sandbox: firejail/Docker + resource limits |
| Data exfiltration | Batasi ekstensi file + max ukuran 50MB |
| Man-in-the-middle | TLS 1.3 + HMAC signature verification |
| Log tampering | Log rotation + optional remote syslog |
| AI prompt injection | Double validation pada output NIM API |

### Checklist Keamanan Sebelum Deploy

```
☐ .env tidak masuk ke Git (.gitignore)
☐ ALLOWED_USER_IDS diisi dengan benar
☐ Agent hanya listen di localhost (127.0.0.1)
☐ Firewall aktif — hanya port yang diperlukan terbuka
☐ SSL/TLS aktif (gunakan Let's Encrypt jika expose ke internet)
☐ Google Authenticator sudah terkonfigurasi
☐ Audit logging aktif dan log disimpan aman
☐ allowed_commands.yaml sudah direview
