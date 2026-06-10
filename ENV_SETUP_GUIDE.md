# Panduan Pengisian File `.env`

File `.env` digunakan untuk menyimpan pengaturan rahasia dan konfigurasi penting agar sistem Anda dapat berjalan dengan aman. **JANGAN PERNAH** membagikan isi file ini kepada siapa pun.

Berikut adalah penjelasan lengkap dan cara mengisi setiap bagian di file `.env`.

---

## 1. Kredensial Bot (Bot Credentials)

Bagian ini digunakan untuk menghubungkan sistem Anda dengan bot Telegram atau WhatsApp.

*   `TELEGRAM_BOT_TOKEN`: Ini adalah "kunci akses" bot Telegram Anda.
    *   **Cara mendapatkan:** Buka Telegram, cari **@BotFather**, ketik `/newbot`, ikuti langkahnya, dan Anda akan diberikan token panjang (contoh: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`).
*   `WHATSAPP_SESSION_PATH`: Lokasi penyimpanan sesi login WhatsApp Anda.
    *   **Isi:** Biarkan saja isinya `.` `/sessions/wa_session` (sudah benar).

---

## 2. Autentikasi & Keamanan (Auth & Security)

Ini adalah bagian terpenting untuk memastikan hanya Anda yang bisa mengontrol laptop Anda. Kita perlu membuat beberapa "kunci rahasia" acak.

*   `OTP_SECRET_KEY`: Kunci rahasia untuk aplikasi Google Authenticator Anda.
    *   **Cara Membuat:**
        1. Buka terminal/command prompt.
        2. Pastikan Anda berada di folder proyek dan virtual environment aktif (`source venv/bin/activate`).
        3. Jalankan perintah ini: `python3 -c "import pyotp; print(pyotp.random_base32())"`
        4. Salin hasil huruf/angka acak yang muncul dan tempelkan ke variabel ini.
        5. **Penting:** Masukkan juga kunci ini ke aplikasi Google Authenticator di HP Anda.
*   `JWT_SECRET_KEY`: Kunci rahasia sistem untuk menjaga Anda tetap login.
    *   **Cara Membuat:**
        1. Jalankan perintah ini di terminal: `python3 -c "import secrets; print(secrets.token_hex(32))"`
        2. Salin hasilnya dan tempelkan.
*   `ALLOWED_USER_IDS`: ID unik Telegram Anda. Hanya ID yang terdaftar di sini yang boleh memberi perintah.
    *   **Cara mendapatkan:** Buka Telegram, cari bot **@userinfobot**, klik `Start`, dan salin angka ID yang diberikan (contoh: `123456789`). Jika Anda ingin menambahkan beberapa orang, pisahkan dengan koma (contoh: `123456789,987654321`).
*   `ENCRYPTION_KEY`: Kunci untuk mengenkripsi data.
    *   **Cara Membuat:**
        1. Jalankan perintah ini: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
        2. Salin hasilnya dan tempelkan.

---

## 3. Agen Laptop (Laptop Agent)

Pengaturan untuk program agen yang berjalan di laptop Anda.

*   `AGENT_HOST`: Alamat agen berjalan.
    *   **Isi:** Biarkan saja `localhost` (agar hanya bisa diakses dari laptop itu sendiri).
*   `AGENT_PORT`: Port tempat agen berjalan.
    *   **Isi:** Biarkan saja `8765`.
*   `AGENT_API_KEY`: Kata sandi internal agar Bot dan Agen bisa saling berbicara dengan aman.
    *   **Cara Membuat:**
        1. Jalankan perintah ini: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
        2. Salin hasilnya dan tempelkan.

---

## 4. NVIDIA NIM (Opsional - Untuk Fitur AI)

Jika Anda ingin memerintah laptop dengan bahasa sehari-hari (misal: "tolong matikan laptop"), Anda butuh ini. Jika tidak, biarkan saja.

*   `NVIDIA_NIM_API_KEY`: Kunci akses AI dari NVIDIA.
    *   **Cara mendapatkan:** Daftar di [build.nvidia.com](https://build.nvidia.com), buat API Key, dan tempelkan di sini (dimulai dengan `nvapi-`).
*   `NVIDIA_NIM_BASE_URL`: URL layanan NVIDIA.
    *   **Isi:** Biarkan saja `https://integrate.api.nvidia.com/v1`.
*   `NVIDIA_NIM_MODEL`: Model AI yang digunakan.
    *   **Isi:** Biarkan saja `meta/llama-3.1-70b-instruct`.
*   `AI_MODE_ENABLED`: Mematikan atau menghidupkan fitur AI.
    *   **Isi:** `true` (hidup) atau `false` (mati). Jika Anda tidak punya API Key NVIDIA, isi dengan `false`.

---

## 5. Batasan Penggunaan (Rate Limiting)

Untuk mencegah sistem *hang* jika Anda (atau orang jahat) mengirim pesan terlalu banyak.

*   `MAX_COMMANDS_PER_MINUTE`: Maksimal perintah per menit.
    *   **Isi:** Biarkan `10` (artinya maksimal 10 perintah dalam 1 menit).
*   `MAX_FILE_SIZE_MB`: Maksimal ukuran file yang bisa diunduh dari laptop ke HP.
    *   **Isi:** Biarkan `50` (artinya maksimal 50 MB).

---

## 6. Pencatatan (Logging)

Pengaturan untuk mencatat semua aktivitas yang terjadi.

*   `LOG_LEVEL`: Tingkat detail catatan.
    *   **Isi:** Biarkan `INFO` (bisa diubah ke `DEBUG` jika ada masalah/error).
*   `LOG_FILE`: Lokasi penyimpanan file catatan aktivitas (Audit Log).
    *   **Isi:** Biarkan `./logs/audit.log`.
