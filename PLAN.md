# Plan v2 — latest LineageOS (24.0, Android 17) fully working on the Meizu mBlu 21 (M416H)

[Bahasa Indonesia](docs/id/PLAN.md) (optional translation; this English text is the reference).

**Status:** APPROVED by Zhafron 2026-10-31 (cards 6c91d3fe + aa32fe5c). **Full autonomy in ZHA-4374, destructive: no. The phone is not touched at all until Zhafron opens a phone session himself**; focus: LineageOS 24.0 source build.
**Supersedes:** `/home/zhafron/re/mblu21/LINEAGEOS_PLAN.md` v1 (ZHA-4374, target LineageOS 21)
**Implementer:** Yanto (RE Specialist) in ZHA-4374 once this plan is approved

## 1. What changed from v1 (summary)

| # | v1 | v2 | Reason / evidence |
|---|---|---|---|
| 1 | Target LineageOS 21 (Android 14) | **LineageOS 24.0 (Android 17)**; fallback 23.2 (Android 16 QPR2) | 24.0 was officially released on 12 Oct 2026 ([changelog 32](https://lineageos.org/Changelog-32/)); 21 is already 3 versions behind. You asked for "latest". |
| 2 | Kernel: self-built from the Realme C53 5.15.178 source | **Stock kernel (Google's prebuilt GKI) for P0/P1**; source build deferred | See §3. Stock kernel = Google's official GKI, vendor modules use `modversions`; no Meizu source needed. |
| 3 | Start with the device tree | **Gate 0: test a LineageOS GSI first** on the stock vendor | One phone session maps which components work before days of investment. It also answers whether Android 17 runs on an Android 13 vendor. |
| 4 | Extract 3,962 blobs one by one | **Stock vendor/odm/vendor_dlkm as prebuilt images** first; individual blobs only for the system/system_ext/product pieces actually used | Fastest path to boot; blob work drops from ~4.5 GB to a few hundred MB. |
| 5 | "Android 14 vendor" | **Fact correction: vendor = Android 13** (`ro.vendor.build.version.release=13`, `ro.board.api_level=33`, VINTF `target-level="7"`); system = Android 14 | Read from `extracted/vendor/build.prop` and `vendor/etc/vintf/manifest.xml`. This is the main Android 17 risk (§7). |
| 6 | All repositories public, blobs as public release assets | All repositories public, **including the vendor blobs/prebuilts** (Zhafron's decision) | Blobs live in their own vendor repository with a disclaimer, so a takedown (if any) does not drag the device tree with it. |
| 7 | ROM build "local PC 3-8 hours" with no resource numbers | Resources measured: 16 cores, 28 GB RAM, 364 GB free disk → sync `--depth=1`, 32 GB swap, `-j12` | Android 17 needs ~300 GB for a full sync + out; 28 GB RAM is below the recommended 32 GB. |

## 2. Device facts (verified from the dump)

- SoC Unisoc UMS9230 (T606), board `ums9230_6h10`, UFS, A/B, dynamic partitions (`super` 5.56 GB), Treble, AVB locked (green).
- System Android 14 (U01005, patch 2025-04-05); **vendor Android 13** (board API 33, VINTF FCM level 7, VNDK 33).
- Boot chain header v4: `boot` (kernel only), `init_boot` (generic ramdisk), `vendor_boot` (vendor ramdisk + DTB, base DTB at offset 25,714,752), `dtbo` (9 overlays, active `dtbo_idx=7` = `ums9230-6h10`). `dtb_a` is empty.
- Stock kernel: `Linux version 5.15.149-android13-8-00008-gbe074b05e5af-ab12096863 (build-user@build-host)`, clang 14.0.7, 16 Jul 2024 → **Google's official GKI build** (ci.android.com), branch `android13-5.15`.
- Vendor modules (`vendor_dlkm`, 113 modules): `vermagic 5.15.149-android13-8-ge43a0339b137-ab333 ... modversions`. The version string differs from the kernel running on the phone, yet the modules load on the stock firmware → the loader uses the `modversions` CRCs, not the version string.
- A full backup exists: `C:\Users\Public\mblu21-backup\full_dump` (44 partitions, 6.07 GB) + the extracted tree in `~/re/mblu21/extracted`.
- Unlock: TomKing062 CVE-2022-38694 (`ums9230_universal_unlock_UFS`), wipes data.

## 3. Kernel decision (the biggest change)

**Path A, used for P0/P1:** stock `boot.img` (Google GKI) + stock `vendor_boot`, `dtbo`, `vendor_dlkm`, `system_dlkm` as prebuilts (`BOARD_PREBUILT_*`/`TARGET_PREBUILT_KERNEL`). No KMI risk, because this combination is exactly what runs on the phone today.

**Path B, kernel security patches, after P1 is stable:** replace `boot.img` with a newer Google GKI `android13-5.15` release (same KMI, module CRCs still match). Still no Meizu source. Verification: all 113 modules load (`lsmod` vs the `modules.load` list).

**Path C, source build for KernelSU, scheduled after P0+P1 pass (Zhafron's decision)**, or earlier only if a driver fix is needed: base is Google's `android13-5.15` common kernel + the GKI defconfig; the Realme C53 5.15.178 source serves only as a driver/DTS reference, not the base, because it carries oplus changes and a `CONFIG_LOCALVERSION` hack to chase vermagic. The Realme build running in ZHA-4374 is not on the critical path.

Official LineageOS 23.2/24.0 only accepts kernels with 1:1 eBPF backports; Google's GKI 5.15 meets that, a vendor-hacked kernel may not.

## 4. Definition of "fully working" (release gate)

Every row needs evidence (log/screenshot/number), not a claim.

| Priority | Component | Pass criterion |
|---|---|---|
| P0 | Boot | Setup wizard reached, 3 reboots without a bootloop |
| P0 | Display/touch | Brightness, multi-touch, rotation |
| P0 | Encryption | FBE active, data still readable after a reboot with PIN |
| P0 | USB/charging | ADB, MTP, charge level rising, correct percentage indicator |
| P0 | SELinux | **Enforcing** (permissive only during bring-up) |
| P1 | Wi-Fi | 2.4/5 GHz, reconnect after sleep |
| P1 | Bluetooth | Pair, A2DP, HID |
| P1 | Cellular | Telkomsel SIM in slot 1 and slot 2 (alternately): 4G data, SMS, incoming/outgoing calls |
| P1 | VoLTE | VoLTE call on Telkomsel (not a 3G/2G fallback) |
| P1 | Audio | Speaker, earpiece, mic (recording + call), headset |
| P1 | Camera | Rear + front: photo, 1080p video, flash |
| P1 | Sensors | Accelerometer, proximity during calls, light, (gyro if present) |
| P1 | Face unlock (supported on stock) | Enrollment completes, then unlock with the face from the lock screen, in enforcing mode |
| P1 | Fingerprint | Enroll + unlock |
| P1 | GPS | Outdoor fix < 60 seconds |
| P1 | Battery | Deep sleep: screen-off idle ≤ 1%/hour over 8 hours |
| P1 | Update | OTA from the LineageOS Updater or a documented sideload |
| P2 | FM/NFC, HDR, 60fps video, advanced camera modes | Status reported, not claimed |

"Fully working" = every P0 + P1 passes with evidence; P2 is reported as it is.

## 5. Work phases

### Phase 0: PC preparation, no phone (0.5 day + sync running in the background)
- 32 GB swap on the WSL ext4 (`/`, not `/mnt`), check that `.wslconfig` gives WSL ≥ 26 GB.
- `repo init -u https://github.com/LineageOS/android.git -b lineage-24.0 --git-lfs --depth=1` then `repo sync -c --no-tags -j8` (async, several hours). Disk target: source + out + ccache ≤ 300 GB of the 364 GB free.
- Local `android_device_meizu_mblu21` repository from the existing tree, using the `arriRgb31/device_realme_rmx3760` template (same UMS9230) for the Unisoc/sprd HAL parts.
- **Acceptance:** sync finishes without errors, `source build/envsetup.sh && breakfast mblu21` recognises the device.

### Phase 1: Gate 0, GSI test (DEFERRED; Zhafron: "don't touch the phone yet"). Allowed now: build the 24.0 arm64 GSI as a ready-to-test artifact. Only Zhafron opens a phone session.
- Build the generic LineageOS 24.0 arm64 GSI target from the same tree (or a community 24.0 GSI if one exists), plus a 23.2 GSI for comparison.
- Unlock the bootloader (CVE-2022-38694), flash `vbmeta` with verification disabled, flash the GSI to `system`, keep the stock vendor/kernel.
- Run the §4 matrix, keep `logcat`, `dmesg`, `lsmod`.
- **Decision from the results:** 24.0 boots and P0 passes → continue with 24.0. 24.0 fails on the Android 13 vendor but 23.2 runs → the target drops to 23.2 (you are told, with evidence). Both fail → blocker report, stop.
- Rollback: reflash the partitions from the backup via `spd_dump`/fastboot.

### Phase 2: Device tree + full ROM build (2-4 days, no phone; starts right after Phase 0, does not wait for Gate 0)
- `BoardConfig.mk`: partitions/super group from the dump, header v4, LZ4, EROFS, AVB; kernel + vendor/odm/vendor_dlkm/system_dlkm as prebuilts (§3 Path A).
- `device.mk`: overlays, `fstab.mblu21`, the stock vendor init rc files that touch system, the VINTF framework manifest.
- Individual blobs for system/system_ext/product are chosen from static analysis of the dump (init rc, VINTF, `dlopen`/`NEEDED` of the vendor HALs: IMS/telephony, camera, fingerprint) because Gate 0 is deferred; `extract-files.sh` is reproducible from the dump + SHA-256.
- SELinux permissive at first.
- `brunch mblu21` (userdebug).
- **Acceptance:** the build produces a ZIP + `boot`/`vendor_boot`/`init_boot`/`dtbo`/`vbmeta`; static validation: image size ≤ partition size, header v4, cmdline equal to stock.

### Phase 3: First boot + P0 (phone, 1-3 sessions)
- Flash the build, collect `logcat`/`pstore`, fix until every P0 passes.

### Phase 4: P1 stabilisation + SELinux enforcing (phone, 1-3 weeks)
- Work per component; each component is closed with evidence. Camera and VoLTE are the riskiest.
- Device sepolicy until enforcing with no denials in logcat while the matrix runs.

### Phase 5: Release (push and release are free; a build not yet tested on the phone must be a pre-release labelled `UNTESTED`)
- Tag `lineage-24.0-YYYYMMDD-UNOFFICIAL-mblu21`, release the ZIP + images + SHA-256 + release notes + status matrix.
- Release keys are kept in GitHub Secrets/locally, never in the repository.
- README: how to build + how to flash + how to roll back to stock.

## 6. Repository architecture

| Repository | Contents | Visibility (recommendation) |
|---|---|---|
| `android_device_meizu_mblu21` | device tree, sepolicy, overlays, fstab, extract script | Public (Apache-2.0) |
| `android_vendor_meizu_mblu21` | blobs + prebuilt vendor/odm/dlkm images (files >100 MiB as release assets + SHA-256) | Public (disclaimer: blobs belong to Meizu/Unisoc, for restoration) |
| `android_kernel_meizu_mblu21` | kernel path, root images (LKM and kernel), root tutorial, hardware evidence | Public (GPL-2.0, mandatory) |
| `lineage_build_mblu21` | local manifest, build script, this plan | Public |

Free GitHub Actions CI (4 vCPU, 16 GB, 14 GB SSD) only for lint/shellcheck/BoardConfig validation; the ROM is built on the local PC.

## 7. Risks & mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| The Android 17 framework rejects the Android 13 vendor (FCM 7/VNDK 33) | ROM does not boot / HALs missing | To be proven at Gate 0 before device tree work; 23.2 fallback |
| LineageOS 24.0 is only 3 weeks old | Upstream bugs | Pin to a sync date that passes; 23.2 fallback |
| Unisoc IMS/VoLTE needs system_ext APKs/blobs | VoLTE dead | Identify at Gate 0, extract the stock IMS blobs |
| Vendor camera HAL + camera app | Partial camera | Use the stock HAL; Aperture app; report the modes that do not work |
| 28 GB RAM for an Android 17 build | OOM during the build | 32 GB swap, `-j12`, ccache |
| Unlock wipes data / brick | Data lost | A full backup already exists; unlock only with your permission; rollback via BROM `spd_dump` |
| Blobs published | Vendor repository takedown | Vendor repository separate from the device tree; local mirror + SHA-256 in `lineage_build_mblu21` so the build can be restored |

## 8. Estimates

| Milestone | Estimate |
|---|---|
| Phase 0 (including sync) | 0.5-1 day |
| Gate 0 GSI | 1 phone session |
| First device tree build | 2-4 days |
| First boot P0 | 1-3 phone sessions |
| P0 + P1 + enforcing | 1-3 weeks; no deadline, worked on until everything passes (Zhafron's decision) |
| KernelSU (Path C) | after P0+P1 |

## 9. Zhafron's decisions (2026-10-31)

Card 6c91d3fe:
1. Target **LineageOS 24.0**.
2. Blob/vendor repository **public**.

Card aa32fe5c (full-autonomy ground rules):
3. Phone: **"don't touch the phone yet, the source hasn't even been worked on, focus on the source build of the latest LineageOS"** (translated quote): no adb/fastboot/unlock/flash/BROM. Physical steps and daily phone status: "later".
4. Test SIM: **Telkomsel** only.
5. Pushing public repositories and releases: **free**.
6. 24.0 fails on the Android 13 vendor → **drop to 23.2 automatically**, with evidence.
7. Deadline: **none**, work until every P0+P1 passes.
8. KernelSU: **yes, after P0+P1 pass**.

## 10. Full-autonomy limits

- Forbidden: touching the phone in any way; force-push/history rewrite; putting release keys/secrets in the repository.
- Free: sync, build, creating and pushing public repositories under `github.com/tickernelz`, releases (pre-release `UNTESTED` until there is evidence on the phone).
- Commits use Zhafron's identity (`~/.gitconfig`), without a `Co-Authored-By` trailer.
