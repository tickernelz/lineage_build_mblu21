# Plan v2 — LineageOS terbaru (24.0, Android 17) fully working untuk Meizu mBlu 21 (M416H)

**Status:** DISETUJUI Zhafron 2026-10-31 (kartu 6c91d3fe + aa32fe5c). **Full otonom di ZHA-4374, destruktif: tidak. HP tidak disentuh sama sekali sampai Zhafron membuka sesi HP sendiri** — fokus: source build LineageOS 24.0.
**Menggantikan:** `/home/zhafron/re/mblu21/LINEAGEOS_PLAN.md` v1 (ZHA-4374, target LineageOS 21)
**Pelaksana:** Yanto (RE Specialist) di ZHA-4374 setelah plan ini disetujui

## 1. Apa yang berubah dari v1 (ringkas)

| # | v1 | v2 | Alasan / bukti |
|---|---|---|---|
| 1 | Target LineageOS 21 (Android 14) | **LineageOS 24.0 (Android 17)**; cadangan 23.2 (Android 16 QPR2) | 24.0 rilis resmi 12 Okt 2026 ([changelog 32](https://lineageos.org/Changelog-32/)); 21 sudah 3 versi di belakang. Kamu minta "terbaru". |
| 2 | Kernel: build sendiri dari source Realme C53 5.15.178 | **Kernel stok (prebuilt GKI Google) untuk P0/P1**; build source ditunda | Lihat §3. Kernel stok = GKI resmi Google, modul vendor pakai `modversions`; tidak butuh source Meizu. |
| 3 | Langsung bikin device tree | **Gerbang 0: tes GSI LineageOS dulu** di vendor stok | Satu sesi HP memberi peta komponen yang jalan/tidak sebelum investasi berhari-hari. Juga menjawab apakah Android 17 mau jalan di vendor Android 13. |
| 4 | Ekstrak 3.962 blob satu per satu | **Vendor/odm/vendor_dlkm stok sebagai prebuilt image** dulu; blob individual hanya untuk system/system_ext/product yang benar-benar dipakai | Jalur tercepat ke boot; blob work turun dari ~4,5 GB jadi beberapa ratus MB. |
| 5 | "Vendor Android 14" | **Koreksi fakta: vendor = Android 13** (`ro.vendor.build.version.release=13`, `ro.board.api_level=33`, VINTF `target-level="7"`); system = Android 14 | Dibaca dari `extracted/vendor/build.prop` dan `vendor/etc/vintf/manifest.xml`. Ini risiko utama Android 17 (§7). |
| 6 | Repo publik semua, blob sebagai release asset publik | Semua repo publik, **termasuk blob/prebuilt vendor** (keputusan Zhafron) | Blob dipisah ke repo vendor sendiri dengan disclaimer, supaya takedown (jika ada) tidak menyeret device tree. |
| 7 | ROM build "PC lokal 3-8 jam" tanpa angka resource | Resource diukur: 16 core, 28 GB RAM, 364 GB disk bebas → sync `--depth=1`, swap 32 GB, `-j12` | Android 17 butuh ~300 GB untuk sync penuh + out; 28 GB RAM di bawah anjuran 32 GB. |

## 2. Fakta perangkat (terverifikasi dari dump)

- SoC Unisoc UMS9230 (T606), board `ums9230_6h10`, UFS, A/B, dynamic partitions (`super` 5,56 GB), Treble, AVB terkunci (green).
- System Android 14 (U01005, patch 2025-04-05); **vendor Android 13** (board API 33, VINTF FCM level 7, VNDK 33).
- Boot chain header v4: `boot` (kernel saja), `init_boot` (ramdisk generik), `vendor_boot` (ramdisk vendor + DTB, base DTB di offset 25.714.752), `dtbo` (9 overlay, aktif `dtbo_idx=7` = `ums9230-6h10`). `dtb_a` kosong.
- Kernel stok: `Linux version 5.15.149-android13-8-00008-gbe074b05e5af-ab12096863 (build-user@build-host)`, clang 14.0.7, 16 Jul 2024 → **build GKI resmi Google** (ci.android.com), cabang `android13-5.15`.
- Modul vendor (`vendor_dlkm`, 113 modul): `vermagic 5.15.149-android13-8-ge43a0339b137-ab333 ... modversions`. String versi beda dari kernel yang jalan di HP, tapi modul tetap ter-load di firmware stok → loader memakai CRC `modversions`, bukan string versi.
- Backup lengkap ada: `C:\Users\Public\mblu21-backup\full_dump` (44 partisi, 6,07 GB) + hasil ekstrak di `~/re/mblu21/extracted`.
- Unlock: TomKing062 CVE-2022-38694 (`ums9230_universal_unlock_UFS`), menghapus data.

## 3. Keputusan kernel (perubahan terbesar)

**Jalur A — dipakai untuk P0/P1:** `boot.img` stok (GKI Google) + `vendor_boot`, `dtbo`, `vendor_dlkm`, `system_dlkm` stok sebagai prebuilt (`BOARD_PREBUILT_*`/`TARGET_PREBUILT_KERNEL`). Tidak ada risiko KMI karena kombinasi ini persis yang jalan di HP hari ini.

**Jalur B — patch keamanan kernel, setelah P1 stabil:** ganti `boot.img` dengan rilis GKI Google `android13-5.15` yang lebih baru (KMI sama, CRC modul tetap cocok). Tetap tanpa source Meizu. Verifikasi: semua 113 modul ter-load (`lsmod` vs daftar `modules.load`).

**Jalur C — build dari source untuk KernelSU, dijadwalkan setelah P0+P1 lulus (keputusan Zhafron)**, atau lebih awal hanya bila butuh driver fix: basis `android13-5.15` common Google + defconfig GKI; source Realme C53 5.15.178 dipakai sebagai referensi driver/DTS saja, bukan basis, karena berisi perubahan oplus dan hack `CONFIG_LOCALVERSION` untuk mengejar vermagic. Build Realme yang sedang jalan di ZHA-4374 tidak di jalur kritis.

LineageOS 23.2/24.0 resmi hanya menerima kernel dengan backport eBPF 1:1; GKI 5.15 Google memenuhi itu, kernel vendor-hack belum tentu.

## 4. Definisi "fully working" (gerbang rilis)

Setiap baris butuh bukti (log/screenshot/angka), bukan klaim.

| Prioritas | Komponen | Kriteria lulus |
|---|---|---|
| P0 | Boot | Setup wizard tercapai, 3x reboot tanpa bootloop |
| P0 | Display/touch | Brightness, multi-touch, rotasi |
| P0 | Enkripsi | FBE aktif, data tetap terbaca setelah reboot dengan PIN |
| P0 | USB/charging | ADB, MTP, charging naik, indikator persen benar |
| P0 | SELinux | **Enforcing** (permissive hanya saat bring-up) |
| P1 | Wi-Fi | 2.4/5 GHz, reconnect setelah sleep |
| P1 | Bluetooth | Pair, A2DP, HID |
| P1 | Seluler | SIM Telkomsel di slot 1 dan slot 2 (bergantian): data 4G, SMS, telepon masuk/keluar |
| P1 | VoLTE | Telepon VoLTE di Telkomsel (bukan fallback 3G/2G) |
| P1 | Audio | Speaker, earpiece, mic (rekam + telepon), headset |
| P1 | Kamera | Belakang + depan: foto, video 1080p, flash |
| P1 | Sensor | Accelerometer, proximity saat telepon, light, (gyro jika ada) |
| P1 | Fingerprint | Enroll + unlock |
| P1 | GPS | Fix di luar ruangan < 60 detik |
| P1 | Baterai | Deep sleep: layar mati idle ≤ 1%/jam selama 8 jam |
| P1 | Update | OTA dari Updater LineageOS atau sideload terdokumentasi |
| P2 | FM/NFC, HDR, 60fps video, mode kamera lanjutan | Status dilaporkan, bukan diklaim |

"Fully working" = semua P0 + P1 lulus dengan bukti; P2 dilaporkan apa adanya.

## 5. Fase kerja

### Fase 0 — Persiapan PC, tanpa HP (0,5 hari + sync berjalan di latar)
- Swap 32 GB di ext4 WSL (`/`, bukan `/mnt`), cek `.wslconfig` memberi ≥ 26 GB ke WSL.
- `repo init -u https://github.com/LineageOS/android.git -b lineage-24.0 --git-lfs --depth=1` lalu `repo sync -c --no-tags -j8` (async, beberapa jam). Target disk: source + out + ccache ≤ 300 GB dari 364 GB bebas.
- Repo lokal `android_device_meizu_mblu21` dari tree yang ada, basis template `arriRgb31/device_realme_rmx3760` (UMS9230 yang sama) untuk bagian HAL Unisoc/sprd.
- **Acceptance:** sync selesai tanpa error, `source build/envsetup.sh && breakfast mblu21` mengenali device.

### Fase 1 — Gerbang 0: tes GSI (DITUNDA — Zhafron: "jangan dulu sentuh sentuh hp"). Yang boleh sekarang: build GSI 24.0 arm64 sebagai artefak siap-uji. Sesi HP dibuka hanya oleh Zhafron.
- Build target GSI generik LineageOS 24.0 arm64 dari tree yang sama (atau GSI komunitas 24.0 bila sudah ada), plus GSI 23.2 sebagai pembanding.
- Unlock bootloader (CVE-2022-38694), flash `vbmeta` dengan verifikasi dimatikan, flash GSI ke `system`, vendor/kernel stok tetap.
- Jalankan matriks §4, simpan `logcat`, `dmesg`, `lsmod`.
- **Keputusan dari hasil:** 24.0 boot dan P0 lulus → lanjut 24.0. 24.0 gagal di vendor Android 13 tapi 23.2 jalan → target diturunkan ke 23.2 (kamu diberi tahu dengan bukti). Keduanya gagal → laporan blocker, berhenti.
- Rollback: flash ulang partisi dari backup via `spd_dump`/fastboot.

### Fase 2 — Device tree + build ROM penuh (2-4 hari, tanpa HP; jalan langsung setelah Fase 0, tidak menunggu Gerbang 0)
- `BoardConfig.mk`: partisi/super group dari dump, header v4, LZ4, EROFS, AVB; kernel + vendor/odm/vendor_dlkm/system_dlkm sebagai prebuilt (§3 Jalur A).
- `device.mk`: overlay, `fstab.mblu21`, init rc dari vendor stok yang menyentuh system, VINTF framework manifest.
- Blob individual untuk system/system_ext/product dipilih dari analisis statis dump (init rc, VINTF, `dlopen`/`NEEDED` dari HAL vendor: IMS/telephony, kamera, fingerprint) karena Gerbang 0 ditunda; `extract-files.sh` reproducible dari dump + SHA-256.
- SELinux permissive dulu.
- `brunch mblu21` (userdebug).
- **Acceptance:** build menghasilkan ZIP + `boot`/`vendor_boot`/`init_boot`/`dtbo`/`vbmeta`; validasi statis: ukuran image ≤ ukuran partisi, header v4, cmdline sama dengan stok.

### Fase 3 — First boot + P0 (HP, 1-3 sesi)
- Flash build, ambil `logcat`/`pstore`, perbaiki sampai semua P0 lulus.

### Fase 4 — Stabilisasi P1 + SELinux enforcing (HP, 1-3 minggu)
- Kerjakan per komponen; tiap komponen ditutup dengan bukti. Kamera dan VoLTE paling berisiko.
- Sepolicy device sampai enforcing tanpa denial di logcat saat matriks dijalankan.

### Fase 5 — Rilis (push dan rilis bebas; build yang belum diuji di HP wajib pre-release berlabel `UNTESTED`)
- Tag `lineage-24.0-YYYYMMDD-UNOFFICIAL-mblu21`, rilis ZIP + image + SHA-256 + catatan rilis + matriks status.
- Kunci rilis disimpan di GitHub Secrets/lokal, tidak pernah di repo.
- README: cara build + cara flash + cara rollback ke stok.

## 6. Arsitektur repo

| Repo | Isi | Visibilitas (rekomendasi) |
|---|---|---|
| `android_device_meizu_mblu21` | device tree, sepolicy, overlay, fstab, extract script | Publik (Apache-2.0) |
| `android_vendor_meizu_mblu21` | blob + prebuilt vendor/odm/dlkm image (file >100 MiB sebagai release asset + SHA-256) | Publik (disclaimer: blob milik Meizu/Unisoc, untuk restorasi) |
| `android_kernel_meizu_mblu21` | hanya bila Jalur C dipakai | Publik (GPL-2.0, wajib) |
| `lineage_build_mblu21` | local manifest, script build, plan ini | Publik |

CI GitHub Actions gratis (4 vCPU, 16 GB, 14 GB SSD) hanya untuk lint/shellcheck/validasi BoardConfig; ROM dibangun di PC lokal.

## 7. Risiko & mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Android 17 framework menolak vendor Android 13 (FCM 7/VNDK 33) | ROM tidak boot / HAL hilang | Dibuktikan di Gerbang 0 sebelum kerja device tree; cadangan 23.2 |
| LineageOS 24.0 baru 3 minggu | Bug upstream | Pin ke tanggal sync yang lulus; cadangan 23.2 |
| IMS/VoLTE Unisoc butuh APK/blob system_ext | VoLTE mati | Identifikasi di Gerbang 0, ekstrak blob IMS stok |
| Kamera HAL vendor + app kamera | Kamera parsial | Pakai HAL stok; app Aperture; laporkan mode yang tidak jalan |
| RAM 28 GB untuk build Android 17 | OOM saat build | Swap 32 GB, `-j12`, ccache |
| Unlock menghapus data / brick | Data hilang | Backup penuh sudah ada; unlock hanya dengan izinmu; rollback via BROM `spd_dump` |
| Blob dipublikasikan | Takedown repo vendor | Repo vendor terpisah dari device tree; mirror lokal + SHA-256 di `lineage_build_mblu21` agar build bisa dipulihkan |

## 8. Estimasi

| Milestone | Estimasi |
|---|---|
| Fase 0 (termasuk sync) | 0,5-1 hari |
| Gerbang 0 GSI | 1 sesi HP |
| Device tree build pertama | 2-4 hari |
| First boot P0 | 1-3 sesi HP |
| P0 + P1 + enforcing | 1-3 minggu; tanpa batas waktu — dikerjakan sampai semua lulus (keputusan Zhafron) |
| KernelSU (Jalur C) | setelah P0+P1 |

## 9. Keputusan Zhafron (2026-10-31)

Kartu 6c91d3fe:
1. Target **LineageOS 24.0**.
2. Repo blob/vendor **publik**.

Kartu aa32fe5c (aturan main full otonom):
3. HP: **"jangan dulu sentuh sentuh hp, kan source aja belum dikerjain, fokus ke source build lineageos terbaru"** — tidak ada adb/fastboot/unlock/flash/BROM. Langkah fisik dan status HP harian: "nanti dulu".
4. SIM tes: **Telkomsel** saja.
5. Push repo publik dan rilis: **bebas**.
6. 24.0 gagal di vendor Android 13 → **turun ke 23.2 otomatis** dengan bukti.
7. Batas waktu: **tidak ada**, kerja sampai semua P0+P1 lulus.
8. KernelSU: **ya, setelah P0+P1 lulus**.

## 10. Batas full otonom

- Dilarang: menyentuh HP dalam bentuk apa pun; force-push/history rewrite; menaruh kunci rilis/secret di repo.
- Bebas: sync, build, membuat dan push repo publik di `github.com/tickernelz`, rilis (pre-release `UNTESTED` sampai ada bukti di HP).
- Commit memakai identitas Zhafron (`~/.gitconfig`), tanpa trailer `Co-Authored-By`.
