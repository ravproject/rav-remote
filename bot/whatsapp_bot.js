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

    // Auto-inject safety flags for AI CLIs in Terminal/Command mode
    let processedText = text;
    if (text.startsWith("gemini ") && !text.includes("--yolo")) {
      processedText = text.replace("gemini ", "gemini --yolo ");
    } else if (text.startsWith("opencode ") && !text.includes("--dangerously-skip-permissions")) {
      processedText = text.replace("opencode ", "opencode --dangerously-skip-permissions ");
    }

    // Forward ke agent
    const jid = msg.key.remoteJid;
    await sock.sendPresenceUpdate("composing", jid);
    const processingMsg = await sock.sendMessage(jid, { text: "⏳ *Agent* sedang memproses..." });

    try {
      const res = await axios.post(`${AGENT_URL}/command`, {
        command: processedText,
        user_id: sender,
      }, {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-API-Key": AGENT_API_KEY,
        },
        timeout: 60000,
      });

      // WhatsApp doesn't have an easy "delete for everyone" without keep-track of keys, 
      // but we can at least send the result.
      const { type, content } = res.data;

      if (type === "text") {
        await sock.sendMessage(jid, { text: `✅ *Hasil:*\n\n${content}` });
      } else if (type === "image") {
        const buffer = Buffer.from(content, "base64");
        await sock.sendMessage(jid, {
          image: buffer,
          caption: "📸 Screenshot Berhasil",
        });
      } else if (type === "video") {
        const buffer = Buffer.from(content.data, "base64");
        await sock.sendMessage(jid, {
          video: buffer,
          caption: "📹 Rekaman Layar Berhasil",
          mimetype: "video/mp4"
        });
      } else if (type === "document") {
        const buffer = Buffer.from(content.data, "base64");
        await sock.sendMessage(jid, {
          document: buffer,
          fileName: content.filename,
          mimetype: content.mimetype,
        });
      }
    } catch (err) {
      console.error("Agent error:", err.message);
      let errorMsg = "❌ *Koneksi Gagal:* Tidak dapat menghubungi Agent.";
      
      if (err.response) {
        if (err.response.status === 400) {
          errorMsg = `⚠️ *Permintaan Ditolak:*\n${err.response.data.detail || "Input tidak valid"}`;
        } else if (err.response.status === 401) {
          errorMsg = "❌ *Sesi Kadaluarsa:* Silakan login kembali dengan `/otp`";
        } else {
          errorMsg = `❌ *Error Agent (${err.response.status}):* Gagal memproses perintah.`;
        }
      } else if (err.code === 'ECONNABORTED') {
        errorMsg = "⏳ *Waktu Habis:* Agent terlalu lama merespons.";
      }
      
      await sock.sendMessage(jid, { text: errorMsg });
    } finally {
      await sock.sendPresenceUpdate("paused", jid);
    }
  });
}

connectWhatsApp();
