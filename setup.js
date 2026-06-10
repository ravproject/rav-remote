#!/usr/bin/env node
/**
 * Setup interaktif untuk rav-remote (Versi 1.0.2)
 * Memperbaiki masalah path saat dijalankan via npx
 */

const readline = require('readline');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const crypto = require('crypto');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const question = (query) => new Promise(resolve => rl.question(query, resolve));

// Fungsi untuk menyalin folder secara rekursif
function copyRecursiveSync(src, dest) {
    const exists = fs.existsSync(src);
    const stats = exists && fs.statSync(src);
    const isDirectory = exists && stats.isDirectory();
    if (isDirectory) {
        if (!fs.existsSync(dest)) fs.mkdirSync(dest);
        fs.readdirSync(src).forEach((childItemName) => {
            copyRecursiveSync(path.join(src, childItemName), path.join(dest, childItemName));
        });
    } else {
        // Jangan salin setup.js sendiri ke folder tujuan agar tidak duplikat
        if (path.basename(src) !== 'setup.js' && path.basename(src) !== 'package-lock.json') {
            fs.copyFileSync(src, dest);
        }
    }
}

async function main() {
    console.log("===========================================");
    console.log("🚀 Selamat datang di Installer rav-remote! 🚀");
    console.log("===========================================\n");

    const targetFolder = await question("Masukkan nama folder untuk instalasi (tekan Enter untuk folder saat ini): ") || ".";
    const absoluteTargetDir = path.resolve(process.cwd(), targetFolder);

    if (!fs.existsSync(absoluteTargetDir)) {
        fs.mkdirSync(absoluteTargetDir, { recursive: true });
    }

    console.log(`\n⏳ Menyiapkan file aplikasi di: ${absoluteTargetDir}...`);
    
    // Lokasi file sumber (di mana setup.js berada dalam paket npm)
    const sourceDir = __dirname;
    
    // Daftar folder/file yang harus disalin
    const itemsToCopy = [
        'agent', 'bot', 'ai_module', 'security', 'config', 'docker', 'tests',
        'requirements.txt', 'package.json', 'README.md', 'BLUEPRINT.md', 
        'ENV_SETUP_GUIDE.md', 'telegram_credentials.md'
    ];

    itemsToCopy.forEach(item => {
        const srcPath = path.join(sourceDir, item);
        const destPath = path.join(absoluteTargetDir, item);
        if (fs.existsSync(srcPath)) {
            copyRecursiveSync(srcPath, destPath);
        }
    });

    console.log("✅ File aplikasi berhasil disalin!");

    // 1. Tanya kredensial ke user
    console.log("\n--- Konfigurasi Kredensial ---");
    const botToken = await question("1. Masukkan Telegram Bot Token Anda: ");
    const userIds = await question("2. Masukkan ID Telegram Anda: ");
    const enableAiInput = await question("3. Aktifkan mode AI NVIDIA NIM? (y/n): ");
    const enableAi = enableAiInput.toLowerCase() === 'y';
    
    let nimApiKey = "";
    if (enableAi) {
        nimApiKey = await question("   Masukkan NVIDIA NIM API Key Anda: ");
    }

    console.log("\n⏳ Menghasilkan kunci rahasia otomatis...");

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

    const envContent = `TELEGRAM_BOT_TOKEN=${botToken}
WHATSAPP_SESSION_PATH=./sessions/wa_session
OTP_SECRET_KEY=${otpSecret}
JWT_SECRET_KEY=${jwtSecret}
ALLOWED_USER_IDS=${userIds}
ENCRYPTION_KEY=${encryptionKey}
AGENT_HOST=localhost
AGENT_PORT=8765
AGENT_API_KEY=${agentApiKey}
NVIDIA_NIM_API_KEY=${nimApiKey}
AI_MODE_ENABLED=${enableAi ? 'true' : 'false'}
MAX_COMMANDS_PER_MINUTE=10
MAX_FILE_SIZE_MB=50
LOG_LEVEL=INFO
LOG_FILE=./logs/audit.log
`;

    fs.writeFileSync(path.join(absoluteTargetDir, '.env'), envContent);
    console.log("✅ File .env berhasil dibuat!");

    // 4. Install Python dependencies
    console.log("\n⏳ Sedang menginstal dependensi Python (ini mungkin memakan waktu)...");
    process.chdir(absoluteTargetDir);
    try {
        execSync('python3 -m venv venv', { stdio: 'inherit' });
        const pipCmd = process.platform === 'win32' ? 'venv\\Scripts\\pip' : 'venv/bin/pip';
        execSync(`${pipCmd} install -r requirements.txt`, { stdio: 'inherit' });
        console.log("✅ Dependensi Python berhasil diinstal!");
    } catch (error) {
        console.error("❌ Gagal menginstal dependensi Python otomatis. Silakan jalankan 'pip install -r requirements.txt' secara manual nanti.");
    }

    console.log("\n===========================================");
    console.log("🎉 rav-remote BERHASIL DIINSTAL! 🎉");
    console.log("===========================================\n");
    console.log(`Lokasi Instalasi: ${absoluteTargetDir}`);
    console.log(`Kunci OTP Anda  : \x1b[32m${otpSecret}\x1b[0m (Masukkan ke Google Authenticator)`);
    console.log("\nCara menjalankan:");
    console.log(` 1. cd ${targetFolder === '.' ? 'folder_ini' : targetFolder}`);
    console.log(" 2. Terminal 1: source venv/bin/activate && python -m agent.main");
    console.log(" 3. Terminal 2: source venv/bin/activate && python -m bot.telegram_bot\n");
    
    rl.close();
}

main();
