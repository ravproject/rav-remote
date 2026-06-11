# Design System: RAV-REMOTE (Remote Laptop Control)

Dokumen ini mendefinisikan standar visual, interaksi, dan arsitektur untuk memastikan konsistensi, keamanan, dan pengalaman pengguna yang superior di seluruh platform (Telegram, WhatsApp, dan Terminal).

---

## 1. Identitas Brand & Filosofi

### 1.1 Nama & Kepribadian
*   **Nama Proyek:** `rav-remote`
*   **Tone of Voice:** Profesional, Siaga, dan Minimalis. Bot bertindak sebagai asisten teknis yang patuh dan sangat mementingkan keamanan.
*   **Bahasa:** Utama menggunakan Bahasa Indonesia (dengan istilah teknis tetap dalam Bahasa Inggris).

### 1.2 Bahasa Emoji (Visual Identity)
Karena bot tidak memiliki UI grafis tradisional, emoji digunakan sebagai indikator status visual:
*   🚀 : Memulai sistem / Booting.
*   🔐 : Autentikasi / Keamanan.
*   ✅ : Operasi Berhasil.
*   ❌ : Operasi Gagal / Error Kritis.
*   ⚠️ : Peringatan / Perlu Konfirmasi.
*   ⏳ : Sedang Memproses.
*   📸 : Output Gambar / Screenshot.
*   💻 : Informasi Sistem.
*   📂 : Manajemen File.

---

## 2. UI Components (Bot Messaging)

Semua pesan yang dikirim oleh bot harus mengikuti struktur Markdown yang konsisten:

### 2.1 Header Pesan
Setiap balasan utama harus dimulai dengan judul tebal dan emoji yang relevan.
> **Format:** `[EMOJI] *Judul Pesan*`

### 2.2 Status Indicators
Memberikan umpan balik instan tentang apa yang sedang dilakukan sistem.
*   *Processing:* `⏳ Memproses perintah...`
*   *Success:* `✅ Perintah [NAMA] berhasil dijalankan.`
*   *Failure:* `❌ Error: [PENJELASAN SINGKAT]`

### 2.3 Blok Kode & Data
Data teknis atau output terminal harus dibungkus dalam blok kode untuk keterbacaan.
> **Format:**
> ```
> [OUTPUT DATA]
> ```

### 2.4 Tombol Aksi (Khusus Telegram)
Gunakan *Inline Keyboard* untuk aksi yang membutuhkan konfirmasi seperti `Reboot` atau `Shutdown`.

---

## 3. Interaction Design (User Flow)

### 3.1 Flow Autentikasi (Zero-Trust)
1.  **Trigger:** User mengirim pesan apa pun.
2.  **Challenge:** Bot mengecek whitelist & sesi JWT. Jika tidak ada, kirim instruksi `/start`.
3.  **OTP:** User mengirim `/otp 123456`.
4.  **Verification:** Bot memvalidasi via Agent.
5.  **Access Granted:** Bot mengirim daftar perintah tersedia dan memulai sesi (4 jam).

### 3.2 Flow Perintah AI (Natural Language)
1.  **Input:** User mengirim teks bebas (misal: "Ambil foto layar").
2.  **Processing:** Bot menunjukkan indikator `⏳`.
3.  **Translation:** AI menerjemahkan ke perintah sistem `!screenshot`.
4.  **Execution:** Agent mengeksekusi dan mengirim hasil.
5.  **Feedback:** Bot menampilkan hasil (Gambar/Teks).

### 3.3 Flow Mode Terminal Persisten
1.  **Entry:** User mengirim `!term`. Bot memberikan peringatan risiko dan membuka PTY.
2.  **Interaction:** Semua pesan teks diteruskan langsung ke stdin PTY.
3.  **Streaming:** Bot melakukan polling output secara asinkron dan mengirimkannya kembali dalam blok kode.
4.  **Exit:** User mengirim `!exit`. Bot menutup proses PTY dan kembali ke mode perintah normal.

---

## 4. Arsitektur & Pola Desain (System Design)

### 4.1 Modularitas
Sistem dibagi menjadi modul-modul independen:
*   `agent/`: Eksekusi perintah di level OS.
*   `bot/`: Layer komunikasi dan logika pesan.
*   `security/`: Middleware untuk validasi dan perlindungan.
*   `ai_module/`: Interpreter untuk kecerdasan buatan.

### 4.2 Prinsip Keamanan (Security by Design)
*   **Sanitization First:** Tidak ada input user yang menyentuh shell sebelum melewati `security/sanitizer.py`.
*   **Sandbox Isolation:** Perintah yang bersifat eksekusi skrip (`!run`) wajib berjalan di dalam `Firejail` atau `Docker`.
*   **Least Privilege:** Agent berjalan sebagai user biasa, bukan root/admin.

---

## 5. Standar Kode & Pengembangan

### 5.1 Penamaan File
*   Python: `snake_case.py`
*   Node.js: `camelCase.js` atau `snake_case.js` (konsisten per folder).
*   Konfigurasi: `.yaml` atau `.json`.

### 5.2 Dokumentasi Inline
Setiap modul baru harus memiliki docstring di bagian atas yang menjelaskan fungsi dan dependensinya.

---

## 6. Roadmap Desain Masa Depan
*   **Web Dashboard:** UI berbasis React untuk memantau audit log secara visual.
*   **Multi-Agent Support:** Satu bot bisa mengontrol beberapa laptop sekaligus.
*   **Voice Command:** Integrasi pesan suara (voice note) menjadi perintah.
