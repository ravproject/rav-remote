# Panduan: Mencegah AI Membangun Ulang Fitur yang Sama

## Tujuan

Dokumen ini menjadi acuan bagi AI (Antigravity/Agent) sebelum mengimplementasikan
atau "memperbaiki" sebuah fitur. Masalah yang ingin dihindari adalah:

- Fitur sudah pernah dibuat, namun belum sesuai ekspektasi user.
- Alih-alih memperbaiki fitur yang sudah ada, AI membuat implementasi baru
  dari nol (rebuild), sehingga muncul beberapa versi fitur yang fungsinya
  tumpang tindih tapi tidak identik (bukan duplikasi murni, tapi variasi
  implementasi yang berulang).
- Hasil akhirnya: codebase berisi banyak versi "percobaan" fitur yang sama,
  membingungkan, dan sulit di-maintain.

## Aturan Wajib Sebelum Membuat/Mengubah Fitur

### 1. Audit Dulu, Implementasi Belakangan

Sebelum menulis kode baru, AI **harus**:

1. Mencari apakah fitur dengan tujuan/fungsi serupa sudah ada di codebase
   (cek nama file, nama komponen, nama fungsi, route, endpoint, dsb).
2. Jika ditemukan, baca implementasi yang sudah ada secara menyeluruh.
3. Tentukan status fitur tersebut:
   - **Bekerja sesuai ekspektasi** → tidak perlu disentuh.
   - **Bekerja tapi belum sesuai ekspektasi** → lanjut ke langkah "Perbaikan",
     bukan "Pembuatan Baru".
   - **Tidak ditemukan sama sekali** → boleh membuat fitur baru.

### 2. Perbaikan, Bukan Penggantian

Jika fitur sudah ada tetapi belum memenuhi ekspektasi:

- AI **wajib memodifikasi implementasi yang ada** (edit in-place), bukan
  membuat file/komponen/fungsi baru dengan nama berbeda yang melakukan hal
  serupa.
- Jika perubahan terlalu besar sehingga struktur lama tidak relevan lagi,
  AI harus secara eksplisit:
  1. Menjelaskan kepada user mengapa refactor besar diperlukan.
  2. Menghapus atau menggabungkan implementasi lama sebagai bagian dari
     perubahan (bukan membiarkannya tetap ada berdampingan).
- Dilarang membuat varian seperti `FeatureV2`, `feature_new`, `featureFixed`,
  `featureFinal`, dsb sebagai cara menghindari refactor file lama.

### 3. Definisi "Bukan Fitur Duplikasi" yang Harus Dihindari

Selain duplikasi identik (copy-paste persis), AI juga harus menghindari
**duplikasi fungsional**, yaitu:

- Dua atau lebih implementasi yang **tujuannya sama** (misal: keduanya
  menangani "export data ke Excel") tetapi:
  - logikanya berbeda,
  - dipanggil dari tempat berbeda,
  - atau memiliki sedikit perbedaan parameter/output.

Ciri-ciri duplikasi fungsional yang harus dicegah:

| Indikasi | Contoh |
|---|---|
| Nama berbeda, perilaku mirip | `exportToExcel()` dan `downloadReportExcel()` |
| Komponen UI yang fungsinya tumpang tindih | `UserFormModal` dan `EditUserDialog` |
| Endpoint API dengan tujuan sama | `/api/users/update` dan `/api/user/edit` |
| Logic validasi yang ditulis ulang di tempat berbeda | validasi email di 3 file berbeda dengan aturan sedikit berbeda |

### 4. Checklist Sebelum Submit Perubahan

AI harus memastikan semua poin berikut sebelum menyelesaikan tugas:

- [ ] Sudah melakukan pencarian (search/grep) untuk fitur dengan tujuan serupa.
- [ ] Jika fitur lama ditemukan, perubahan dilakukan pada file/komponen yang sama.
- [ ] Tidak ada file/komponen/fungsi baru yang namanya hanya variasi dari yang lama
      (`*_v2`, `*New`, `*Fixed`, `*Final`, `*Copy`, dsb).
- [ ] Tidak ada dua jalur kode (route, fungsi, komponen) yang menghasilkan
      output/fungsi yang sama untuk kebutuhan yang sama.
- [ ] Jika ada implementasi lama yang sudah tidak terpakai akibat perubahan ini,
      implementasi tersebut dihapus, bukan dibiarkan tertinggal (dead code).

### 5. Jika AI Ragu

Jika AI tidak yakin apakah suatu fitur sudah ada atau apakah perubahan akan
menyebabkan duplikasi fungsional, AI **harus bertanya kepada user** terlebih
dahulu sebelum menulis kode, dengan menyebutkan:

- Fitur/komponen/fungsi apa yang ditemukan yang mirip.
- Apakah user ingin AI memperbaiki implementasi tersebut atau benar-benar
  membuat sesuatu yang baru dan berbeda.

### 6. Konvensi Penamaan untuk Mencegah Kebingungan

- Satu konsep/fitur = satu nama konsisten di seluruh codebase (file, fungsi,
  komponen, endpoint, variabel state).
- Jika nama sebuah fitur perlu diubah karena tidak representatif lagi, ubah
  **semua referensi** ke fitur tersebut, jangan buat nama baru sambil
  membiarkan nama lama tetap ada di tempat lain.

## Ringkasan

> Sebelum membuat sesuatu yang baru, cari dulu apakah sudah ada yang serupa.
> Jika ada dan belum sempurna, perbaiki yang ada — jangan bangun ulang.
> Jika harus dibangun ulang, hapus yang lama. Jangan biarkan dua implementasi
> dengan tujuan yang sama hidup berdampingan.
