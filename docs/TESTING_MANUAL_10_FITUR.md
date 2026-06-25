# Manual Testing Guide — 10 AI Advanced Features

> Kirim perintah via Telegram/WhatsApp bot ke laptop.  
> Semua command menggunakan prefix `!`

---

## Persiapan

```bash
# 1. Pastikan agent berjalan
source venv/bin/activate
python -m agent.main

# 2. Terminal terpisah — jalankan bot
python -m bot.telegram_bot

# 3. Chat ke bot Telegram, login dengan OTP
/start
/otp 123456   # ganti dengan kode dari Google Authenticator
```

---

## Fitur 1: Long-Term Memory (RAG)

### Test Case 1.1 — Simpan Memory

Kirim:

```
!ingat
```

**Prompt**: perintah tanpa argumen → tampilkan help.

Kirim:

```
!memory search "apa yang aku kerjakan tentang desain UI"
```

**Prompt**: belum ada data → "Tidak ada hasil yang relevan."

Sekarang isi memory secara otomatis via chat. Minta AI nyimpen: (via natural language mode)

```
Ingatkan bahwa aku sedang ngerjakan project dashboard analytics untuk klien
```

Atau langsung via command — nggak bisa karena `!memory` cuma search. Tapi kita punya MCP yang nyimpen otomatis. Lanjut ke MCP dulu.

### Test Case 1.2 — Memory Stats

Kirim:

```
!memory stats
```

**Expected**: `📊 *Memory Stats*\nTotal entries: 0\nTopics: ` (atau >0 kalau MCP sudah jalan).

---

## Fitur 3: MCP — Memory Context Provider

### Test Case 3.1 — Aktifkan MCP

Kirim:

```
!mcp on
```

**Expected**: `🟢 MCP Collector diaktifkan. Monitoring setiap 30 detik.`

Tunggu 30-60 detik. Buka beberapa aplikasi (browser, editor, file manager).

### Test Case 3.2 — Cek Status

Kirim:

```
!mcp status
```

**Expected**: `🟢 Aktif`

### Test Case 3.3 — Query Konteks

Kirim:

```
!mcp query apa yang sedang aku lakukan?
```

**Expected**: menampilkan daftar snapshot aktivitas (active window, recent files, dll) yang dikumpulkan MCP.

### Test Case 3.4 — Nonaktifkan

Kirim:

```
!mcp off
```

**Expected**: `🔴 MCP Collector dinonaktifkan.`

---

## Fitur 4: Personal Virtual Companion

### Test Case 4.1 — Sapaan

Kirim:

```
!companion halo, apa kabar?
```

**Expected**: Balasan hangat dari AI. Contoh: *"Halo! Aku baik-baik saja, terima kasih. Ada yang bisa aku bantu hari ini?"*

### Test Case 4.2 — Curhat

Kirim:

```
!companion hari ini aku capek banget, banyak deadline
```

**Expected**: AI memberikan empati + saran/motivasi. Contoh: *"Aku turut sedih mendengarnya... mungkin kamu bisa coba teknik Pomodoro? 25 menit fokus, 5 menit istirahat."*

### Test Case 4.3 — Tanpa Argumen

Kirim:

```
!companion
```

**Expected**: Help text: `💬 Gunakan: !companion <pesan>`

---

## Fitur 5: Advanced Problem Solver

### Test Case 5.1 — Masalah Programming

Kirim:

```
!solve error "ModuleNotFoundError: No module named 'chromadb'"
```

**Expected**: AI memberikan langkah solusi: cara install, cek venv, dll.

### Test Case 5.2 — Masalah General

Kirim:

```
!solve laptopku lemot banget, apa yang harus dilakukan?
```

**Expected**: Langkah-langkah: cek task manager, matikan startup apps, cek disk usage, dll.

### Test Case 5.3 — Tanpa Argumen

Kirim:

```
!solve
```

**Expected**: Help text: `🔧 Gunakan: !solve <problem>`

---

## Fitur 2: Self-Feature Generation

### Test Case 6.1 — Generate (Dry Run)

Kirim:

```
!create feature "auto screenshot setiap 5 menit dan kirim ke HP"
```

**Expected**: AI generate kode dan menampilkan rencana. Contoh output:

```
🧬 *Generate Fitur Baru: !screenshot_loop*

Deskripsi: Mengambil screenshot setiap 5 menit otomatis
Dependensi: tidak ada

⚠️ Akan memodifikasi: command_handler.py, command_router.py, ...

Ketik `!create confirm screenshot_loop` untuk melanjutkan,
atau `!create cancel` untuk membatalkan.
```

**Catatan**: Jangan confirm dulu karena akan memodifikasi file beneran. Backup dulu:

```bash
cp agent/command_handler.py agent/command_handler.py.backup
```

### Test Case 6.2 — List Fitur Kustom

Kirim:

```
!create list
```

**Expected**: Daftar fitur yang sudah di-generate (kosong kalau belum pernah).

### Test Case 6.3 — Tanpa Argumen

Kirim:

```
!create
```

**Expected**: Help text.

---

## Fitur 9: Knowledge Enrichment

### Test Case 7.1 — Belajar Topik Baru

Kirim:

```
!learn Python async programming best practices 2026
```

**Expected**: AI mencari artikel web, merangkum, dan menyimpan.

```
📚 *Knowledge Enriched: Python async programming best practices 2026*
✅ 3 artikel disimpan:
  • Async Python: The Complete Guide
  • Python Asyncio Best Practices
  • 10 Async/Await Patterns You Should Know

Total knowledge base: 3 articles
```

### Test Case 7.2 — List Topik

Kirim:

```
!learn list
```

**Expected**: Daftar topik yang sudah dipelajari.

### Test Case 7.3 — Tanpa Argumen

Kirim:

```
!learn
```

**Expected**: Help text.

---

## Fitur 6: Self-Evolution Engine

### Test Case 8.1 — Jalankan Evolusi

Kirim:

```
!self evolve
```

**Expected**: Menganalisis error log & performa.

```
🧬 *Self-Evolution Report*
✅ Tidak ada error hari ini.
⏱️ Performance baseline: normal
```

### Test Case 8.2 — History Evolusi

Kirim:

```
!self evolve history
```

**Expected**: Riwayat evolusi (kosong kalau belum pernah).

### Test Case 8.3 — Jadwalkan Otomatis

Kirim:

```
!self evolve auto
```

**Expected**: `🕛 Self-evolution dijadwalkan otomatis setiap tengah malam.`

---

## Fitur 7: Usage Optimization Advisor

### Test Case 9.1 — Saran Optimalisasi

Kirim:

```
!optimize me
```

**Expected**: Analisis penggunaan dan saran.

```
📊 *Usage Optimization Advice*
Belum ada data penggunaan. Mulai gunakan fitur RAV-REMOTE!
```

Atau (kalau sudah ada data):

```
📊 *Usage Optimization Advice*

⏰ Kamu paling aktif jam 9:00, 14:00, 20:00
💡 Saran: Set !focus otomatis jam 9:00 dengan !schedule

🔥 Fitur favorit (150 total command):
  • !screenshot — 45x (30%)
  • !sysinfo — 30x (20%)
  • !ls — 20x (13%)
```

---

## Fitur 8: Proactive Awareness

### Test Case 10.1 — Aktifkan

Kirim:

```
!proactive on
```

**Expected**: `🔔 Proactive mode diaktifkan.`

Tunggu 5 menit (atau set interval lebih cepat untuk test). Buka aplikasi berat atau biarkan idle.

Proactive alert akan terkirim otomatis via heartbeat ke bot, lalu ke HP. Contoh:

```
📝 Detected working on: 'Laporan Keuangan.xlsx - Excel', need help summarizing?
```

### Test Case 10.2 — Status

Kirim:

```
!proactive status
```

**Expected**: `🔔 Aktif`

### Test Case 10.3 — Nonaktifkan

Kirim:

```
!proactive off
```

**Expected**: `🔕 Proactive mode dinonaktifkan.`

---

## Fitur 10: Autonomous Agent Mode

### Test Case 11.1 — Agent Sederhana

Kirim:

```
!agent cek informasi sistem laptop sekarang
```

**Expected**: AI membuat plan dan mengeksekusi.

```
🤖 *Autonomous Agent Report*
Goal: cek informasi sistem laptop sekarang
Status: ✅ Completed
Steps: 2

📌 *Step 1:* Mengecek informasi sistem
  !sysinfo
  💻 System Info: CPU: 23% RAM: 6144MB/16384MB...
📌 *Step 2:* Mengecek status baterai
  !battery
  🔋 Battery: 85% (charging)
```

### Test Case 11.2 — Agent Kompleks

Kirim:

```
!agent siapkan daily report dan screenshot aktivitas hari ini
```

**Expected**: Multi-step plan: `!daily` + `!screenshot` + mungkin `!ai summarize`.

### Test Case 11.3 — Hentikan Agent

Kirim:

```
!agent stop
```

**Expected**: `⏹️ Agent dihentikan.`

---

## Test Case Komprehensif (End-to-End)

### Skenario: "Daily Intelligence Workflow"

```
# 1. Aktifkan MCP untuk monitoring
!mcp on

# 2. Tanya companion
!companion selamat pagi, hari ini aku ada meeting dan coding

# 3. Solve masalah yang muncul
!solve error python memory leak how to debug

# 4. Belajar topik baru
!learn tips presentasi yang efektif

# 5. Minta agent menyiapkan ringkasan
!agent buat ringkasan aktivitas hari ini dari daily report

# 6. Cek saran optimalisasi
!optimize me

# 7. Cek memory apa yang tersimpan
!memory stats
!memory search "meeting"

# 8. Jalankan self-evolution (sebelum tidur)
!self evolve
```

---

## Quick Reference Card

| Perintah | Fungsi | Test Via |
|----------|--------|----------|
| `!memory search <q>` | Cari memory RAG | Telegram/WA |
| `!memory stats` | Statistik memory | Telegram/WA |
| `!mcp on/off` | Monitoring aktivitas | Telegram/WA |
| `!mcp query <q>` | Tanya konteks realtime | Telegram/WA |
| `!companion <msg>` | Ngobrol dengan AI | Telegram/WA |
| `!solve <problem>` | Solusi masalah | Telegram/WA |
| `!create feature <desc>` | Generate fitur baru | Telegram/WA |
| `!learn <topic>` | Simpan pengetahuan | Telegram/WA |
| `!self evolve` | Evolusi diri | Telegram/WA |
| `!optimize me` | Saran optimalisasi | Telegram/WA |
| `!proactive on/off` | Notifikasi proaktif | Telegram/WA |
| `!agent <goal>` | Agent otonom | Telegram/WA |

---

## Troubleshooting

| Problem | Solusi |
|---------|--------|
| `!companion` timeout | Cek NVIDIA_NIM_API_KEY di .env |
| `!solve` "Web search unavailable" | Cek koneksi internet & scraper module |
| `!learn` tidak menemukan artikel | Coba topik yang lebih spesifik |
| `!mcp` error saat start | Pastikan active_window module bisa diimport |
| `!create feature` JSON error | Coba deskripsi yang lebih detail |
| `!memory` ChromaDB error | Hapus `~/.config/rav-remote/memory/chroma/` lalu coba lagi |
| Bot nggak respon | Cek log: `tail -f logs/audit.log` |
| Embedding model lama loading | Hanya sekali saat startup (cache ONNX) |
