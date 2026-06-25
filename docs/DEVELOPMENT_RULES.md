# Aturan Pengembangan & Stabilitas Fitur (Development Guidelines)

> [!IMPORTANT]
> **ATURAN EMAS UTAMA:** Jangan pernah menyentuh, mengubah, memodifikasi, atau menghapus fitur, perintah, alias, atau kode yang sudah ada kecuali diinstruksikan secara eksplisit oleh USER. Semua fitur baru wajib ditambahkan secara terpisah (independen) tanpa mengganggu fungsionalitas yang lama.

---

## 🛡️ Panduan Menjaga Stabilitas Fitur

### 1. Daftar Perintah Aman (Whitelist) — `config/allowed_commands.yaml`
- **Dilarang keras** menghapus perintah yang sudah ada di bawah `safe_commands`.
- Saat menambahkan fitur baru, daftarkan sebagai entry baru tanpa mengubah konfigurasi/deskripsi entry yang sudah ada.

### 2. Router Perintah — `bot/command_router.py`
- Blok penanganan perintah (`elif command_name == "..."`) yang sudah ada tidak boleh dimodifikasi logikanya.
- Tambahkan cabang `elif` baru untuk fitur baru di bagian paling bawah sebelum blok fallback/logout.

### 3. Pintasan / Shortcut — `ai_module/fallback_parser.py`
- Jangan mengubah pemetaan `COMMAND_MAP` yang sudah terdaftar (seperti `!read`, `!write`, `!agy`, `!screenshot`, dll.).
- Tambahkan shortcut baru hanya jika diminta.

### 4. Sanitasi Keamanan — `security/sanitizer.py`
- Pertahankan tingkat izin file saat ini (semua direktori diizinkan setelah resolusi path absolut). Jangan membatasi akses folder yang sudah dibuka secara bebas.
- Jangan merusak regex scanning safety net untuk perlindungan injeksi shell.

### 5. Pengujian (Unit & E2E Tests)
- Semua test case yang sudah ada di `tests/test_commands.py` dan `tests/test_e2e.py` harus tetap lulus (passing) 100%.
- Buat test case terpisah untuk fitur baru agar pengujian tidak tumpang tindih.

---

## 🛠️ Prosedur Penambahan Fitur Baru
1. **Analisis Dampak:** Pastikan fitur baru menggunakan nama perintah unik yang belum terdaftar.
2. **Implementasi Terisolasi:** Tulis fungsi baru di modul `agent/` atau modul baru khusus jika kompleks.
3. **Pendaftaran & Routing:** Tambahkan ke whitelist dan sambungkan di router dengan cabang `elif` mandiri.
4. **Verifikasi Regresi:** Jalankan `./venv/bin/python3 -m unittest discover tests` untuk memastikan tidak ada regresi pada fitur yang sudah ada.
