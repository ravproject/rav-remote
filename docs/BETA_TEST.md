# Daftar Fitur Beta — Manual Test Required

## A. Fitur Baru (UI & Interaction) — Perlu Dicek

| Fitur | Status | Catatan |
|---|---|---|
| **Reply Keyboard** (tombol cepat di bawah chat) | ❌ Belum | Cek muncul/tidak di HP & Desktop |
| **Bot Commands** (`/screenshot`, `/sysinfo`, dll) | ❌ Belum | Cek autocomplete pas ketik `/` |
| **Menu Utama** (`/menu` atau `!menu`) | ❌ Belum | Cek semua kategori, navigasi, back button |
| **Conversation Flow** (Type, Press, Get, dll) | ❌ Belum | Klik button → ketik jawaban → jalan? |
| **Confirm Dialog** (`!reboot`, `!lock`, etc) | ❌ Belum | Klik ✅/❌, cancel, timeout |
| **Help Sections** (button per section) | ❌ Belum | Cek semua section isi bener |
| **Help Table Format** (di dalem section) | ❌ Belum | Tampilan rapi? |
| **Screenshot Grid + AI** (`!screenshot grid describe`) | ❌ Belum | Cek hasil + caption AI |

## B. Fitur Phase 2 — AI & Automation (Beta)

| Perintah | Fungsi | Status |
|---|---|---|
| `!ai work [perintah]` | AI assistant produktivitas | ✅ Sudah |
| `!ai write [tipe] [topik]` | Buat draft dokumen/email via AI | ✅ Sudah |
| `!ai automate [deskripsi]` | Buat automation script via AI | ✅ Sudah |
| `!ai summarize [target]` | Ringkasan file/folder via AI | ✅ Sudah |
| `!ai research [topik] [depth]` | Riset topik via AI | ✅ Sudah |
| `!ai insight [daily\|weekly\|monthly]` | Analisis pola penggunaan laptop | ✅ Sudah |
| `!smart_clip [on\|off\|history]` | Smart clipboard | ✅ Sudah |
| `!macro [record\|play\|save\|list\|delete] [nama]` | Rekam/putar aksi keyboard mouse | ✅ Sudah |
| `!schedule add <perintah> <waktu>` | Jadwalkan perintah otomatis | ✅ Sudah |
| `!voice_cmd [on\|off]` | Voice command dari HP | ✅ SUdah |

## C. Fitur Phase 3 — File, Sync & Data (Beta)

| Perintah | Fungsi | Status |
|---|---|---|
| `!sync <folder> [service]` | Sinkronisasi folder ke cloud | ✅ Sudah |
| `!quick_upload` | Lihat folder upload untuk kirim file | ✅ Sudah |
| `!recent [files\|folders] [jumlah]` | Daftar fir terbarule/folder terbaru | ✅ Sudah |
| `!search_content <keyword> [folder]` | Cari teks di dalam file | ✅ Sudah |
| `!convert <file> <format>` | Konversi format file (pandoc/ffmpeg) | ✅ Sudah  |
| `!backup <folder> [quick\|full]` | Backup folder | ❌ Belum |
| `!organize <folder> [by type\|date]` | Organisir file otomatis | ❌ Belum |
| `!file_watcher [on\|off\|status] <folder>` | Pantau perubahan folder realtime | ❌ Belum |
| `!version [commit\|history\|revert\|status] <file>` | Versioning file lokal | ❌ Belum |
| `!clean [temp\|cache\|duplicates\|all]` | Bersihkan sampah disk | ❌ Belum |

## D. Fitur Phase 4 — System Enhancement (Beta)

| Perintah | Fungsi | Status |
|---|---|---|
| `!volume [app\|global] [level\|up\|down\|mute]` | Kontrol volume | ✅ Sudah |
| `!power [performance\|balanced\|saver]` | Ganti profil daya | ❌ Belum |
| `!multi_monitor [list\|switch\|arrange]` | Kelola monitor ganda | ❌ Belum |
| `!sleep [delay]` | Tidurkan laptop | ❌ Belum |
| `!wake <waktu>` | Jadwalkan bangunkan laptop | ❌ Belum |
| `!quick_app <nama>` | Buka aplikasi cepat | ❌ Belum |
| `!night_mode [on\|off]` | Dark mode + blue light filter | ❌ Belum |
| `!window [arrange\|snap\|minimize all\|close all]` | Atur semua jendela | ❌ Belum |
| `!hotkey [create\|list\|delete] <nama> <key>` | Buat hotkey global | ❌ Belum |
| `!launch_advanced <app> [args]` | Luncurkan aplikasi dengan parameter | ❌ Belum |

## E. Fitur Phase 5 — Advanced & Pro (Beta)

| Perintah | Fungsi | Status |
|---|---|---|
| `!time_track [start\|stop\|status\|report] [project]` | Lacak waktu kerja | ❌ Belum |
| `!session [save\|list\|restore\|delete] <name>` | Simpan/pulihkan session aplikasi | ❌ Belum |
| `!share_screen [fullscreen\|area]` | Screenshot layar | ❌ Belum |
| `!multi_device [register\|list\|delete\|send] <name>` | Kelola multi-perangkat | ❌ Belum |
| `!profile [create\|list\|apply\|delete] <name>` | Profile pengguna | ❌ Belum |
| `!dash` | Tampilkan dashboard sistem | ❌ Belum |
| `!activity_log [days] [--filter=aksi]` | Lihat log aktivitas | ❌ Belum |
| `!vpn [status\|connect\|disconnect] [name]` | Kontrol VPN | ❌ Belum |
| `!tunnel [create\|list\|start\|delete] <name>` | Tunnel SSH | ❌ Belum |
| `!ai_agent <task>` | AI Agent untuk tugas kompleks | ❌ Belum |

## Cara Testya

1. Kirim perintah ke bot Telegram
2. Catat hasilnya (sukses/gagal/error)
3. Update status di sini dari ❌ Belum → ✅ OK / ❌ Error

Format laporan:
```
Perintah: !screenshot grid describe
Hasil: ✅ Gambar terkirim dengan grid + caption AI
Tanggal: 23 Juni 2026
```
