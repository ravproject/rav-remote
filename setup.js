#!/usr/bin/env node
/**
 * Setup interaktif untuk rav-remote
 * Script ini akan dijalankan otomatis saat user mengetik `npx rav-remote`
 */

const readline = require('readline');
const fs = require('fs');
const { execSync } = require('child_process');
const crypto = require('crypto');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const question = (query) => new Promise(resolve => rl.question(query, resolve));

async function main() {
    console.log("===========================================");
    console.log("🚀 Selamat datang di Setup rav-remote! 🚀");
    console.log("===========================================\n");
    console.log("Mari kita atur konfigurasi sistem Anda.\n");

    // 1. Tanya kredensial ke user
    const botToken = await question("1. Masukkan Telegram Bot Token Anda: ");
    const userIds = await question("2. Masukkan ID Telegram Anda (pisahkan dengan koma jika lebih dari satu pengguna): ");
    
    const enableAiInput = await question("3. Apakah Anda ingin mengaktifkan mode AI pintar dari NVIDIA NIM? (y/n): ");
    const enableAi = enableAiInput.toLowerCase() === 'y';
    
    let nimApiKey = "";
    if (enableAi) {
        nimApiKey = await question("   Masukkan NVIDIA NIM API Key Anda: ");
    }

    console.log("\n⏳ Sedang membuat kunci rahasia otomatis (OTP, Enkripsi, Token)...");

    // 2. Generate secret keys secara otomatis
    // Base32 generator khusus untuk Google Authenticator (pyotp kompatibel)
    const generateBase32 = () => {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
        let result = '';
        for (let i = 0; i < 16; i++) result += chars.charAt(Math.floor(Math.random() * chars.length));
        return result;
    };

    const otpSecret = generateBase32();
    const jwtSecret = crypto.randomBytes(32).toString('hex');
    const agentApiKey = crypto.randomBytes(32).toString('base64url');
    const encryptionKey = crypto.randomBytes(32).toString('base64url');

    // 3. Tulis semuanya ke file .env
    const envContent = `# ── BOT CREDENTIALS ──────────────────────────────────────
TELEGRAM_BOT_TOKEN=${botToken}
WHATSAPP_SESSION_PATH=./sessions/wa_session

# ── AUTH & SECURITY ──────────────────────────────────────
OTP_SECRET_KEY=${otpSecret}
JWT_SECRET_KEY=${jwtSecret}
ALLOWED_USER_IDS=${userIds}
ENCRYPTION_KEY=${encryptionKey}

# ── LAPTOP AGENT ─────────────────────────────────────────
AGENT_HOST=localhost
AGENT_PORT=8765
AGENT_API_KEY=${agentApiKey}

# ── NVIDIA NIM (OPSIONAL) ────────────────────────────────
NVIDIA_NIM_API_KEY=${nimApiKey}
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_MODEL=meta/llama-3.1-70b-instruct
AI_MODE_ENABLED=${enableAi ? 'true' : 'false'}

# ── RATE LIMITING ────────────────────────────────────────
MAX_COMMANDS_PER_MINUTE=10
MAX_FILE_SIZE_MB=50

# ── LOGGING ──────────────────────────────────────────────
LOG_LEVEL=INFO
LOG_FILE=./logs/audit.log
`;

    fs.writeFileSync('.env', envContent);
    console.log("✅ File .env berhasil dibuat!");

    // 4. Otomatis install Python dependencies
    console.log("\n⏳ Sedang menyiapkan Python Virtual Environment dan menginstal dependensi...");
    try {
        execSync('python3 -m venv venv', { stdio: 'inherit' });
        execSync('source venv/bin/activate && pip install -r requirements.txt', { shell: '/bin/bash', stdio: 'inherit' });
        console.log("✅ Dependensi Python berhasil diinstal!");
    } catch (error) {
        console.error("❌ Gagal menginstal dependensi Python. Pastikan Python 3 dan pip sudah terpasang di komputer ini.");
    }

    // 5. Pesan sukses & instruksi OTP
    console.log("\n===========================================");
    console.log("🎉 Setup rav-remote SELESAI! 🎉");
    console.log("===========================================\n");
    console.log("PENTING: Kunci rahasia Google Authenticator Anda adalah:");
    console.log(`\x1b[32m${otpSecret}\x1b[0m`);
    console.log("Silakan masukkan kunci di atas ke aplikasi Google Authenticator di HP Anda sekarang.\n");
    
    console.log("Untuk menjalankan sistem, buka DUA terminal di folder ini dan jalankan perintah berikut:");
    console.log(" Terminal 1 (Agen): source venv/bin/activate && python -m agent.main");
    console.log(" Terminal 2 (Bot) : source venv/bin/activate && python -m bot.telegram_bot\n");
    
    rl.close();
}

main();
