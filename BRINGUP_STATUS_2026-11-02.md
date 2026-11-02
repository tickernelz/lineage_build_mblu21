# Bring-up status: 2026-11-02 hardware session

**Result: the 24.0 build does not boot on the phone. Root cause narrowed to AVB, not to the device tree.**

## What was proven on the phone (M416H, UMS9230)

| Step | Result |
|---|---|
| Bootloader unlock (CVE-2022-38694, download mode) | unlocked; `ro.boot.flash.locked=0`, `verifiedbootstate=orange` |
| Userdata after unlock | **not wiped**: 2.9 GB in use, 255 packages, FBE still active, `device_provisioned=1` |
| Full ROM write (7 partitions incl. `super` 5.56 GB) | all "Write Part Done" |
| Boot of the written ROM | **stuck at the Meizu logo**, no recovery, no adb |
| Stock restore (boot/init_boot/vendor_boot/dtbo/vbmeta/misc/super) | repeated, phone boots Android 14 again every time |
| Stock recovery boot | works (USB `1782:d001`, adb `recovery`) |

## Root cause of the bootloop

The bootloader refuses **every** `vbmeta` it did not get from Meizu:

- `vbmeta` flags 3, algorithm NONE (the fastboot `--disable-verification` form) → stuck at logo.
- `vbmeta` flags 3, **signed** RSA4096 with the AOSP test key (`2597c218…`), no chain descriptors → stuck at logo.
- Stock Meizu `vbmeta` (flags 0) → boots.

With a stock `vbmeta` present, an unsigned/foreign `vendor_boot` (SHRP) is rejected as well, so custom recovery does not load either. The device keeps its Meizu public key requirement even with `LOCK FLAG IS: UNLOCK`.

Consequence: a ROM signed with test keys cannot boot on this phone while `vbmeta` is verified against the Meizu key.

## What did not work, for the record

- `fastboot flash` and `fastboot boot`: accepted ("Sending … OKAY") then fail at Writing / never run. Fastboot here is read-only (`getvar`, `reboot`).
- `spd_dump` download mode is the only write path; each run drops the USB link, so every write needs a fresh Volume-Up + plug-in window.
- Forcing recovery through the `misc` BCB (`boot-recovery`) did not bring the phone into recovery; `console-ramoops` from the failed boot could therefore not be collected.

## Next viable path

GSI only: keep `boot`, `init_boot`, `vendor_boot`, `dtbo` and `vbmeta` stock (so AVB passes), and replace only `system` inside `super` with a LineageOS GSI. This is gate 0 of PLAN.md. It needs a phone session and will require formatting userdata.

## Why GSI is also unlikely to work (checked 2026-11-02)

The first-stage `fstab.ums9230_6h10` inside the **stock** vendor_boot ramdisk asks for GSI keys:

```
system /system erofs ro wait,avb=vbmeta_system,logical,first_stage_mount,\
avb_keys=/avb/q-gsi.avbpubkey:/avb/r-gsi.avbpubkey:/avb/s-gsi.avbpubkey,slotselect
```

But those key files are **not on the device**: nothing matching `*.avbpubkey` or `/avb/*-gsi*` exists in the stock `vendor_boot` ramdisk (873 entries, no `avb/`), in `super`, or in the extracted `vendor`. The fstab entry is inherited boilerplate from a GSI-ready vendor, and `fs_mgr` fails closed when a listed key file is missing.

So a GSI written to `system` would be verified against the vendor key from `vbmeta_system` (sha1 `abf3065f…`), not a Google GSI key — with the same result as the full ROM: rejected.

## Cheapest possible AVB probe (prepared, not yet run)

Flip one reserved byte in the stock `init_boot` header (offset `0x20`, `00`→`ff`), write it to `init_boot_a`, boot. Everything else stays stock.

- Phone boots normally → AVB for `init_boot` is not enforced, and rooting with SukiSU Ultra (LKM, which patches `init_boot`) becomes viable.
- Phone stops at the logo → AVB is enforced for `init_boot` too, so root and every other custom image stay blocked without a Meizu key.

The image is staged at `~/mblu21-flash/init_boot_tampered.img`; the stock original is `init_boot_a.bin` in the dump for immediate restore.

## Root achieved (same session, after the AVB findings)

Two working root paths were proven on the phone; `init_boot` is **not** AVB-verified, while `boot` and `vendor_boot` are.

| Path | Image written | Result |
|---|---|---|
| KernelSU-Next 3.4.2 | `init_boot-kernelsu-next-lkm.img` (`3ed94999…`, patched by official `ksud` in CI) | boots; `su -c id` = uid 0, ctx `u:r:ksu:s0` |
| SukiSU-Ultra 4.3.0 | `init_boot` patched on-device by official `ksud 4.3.0` with `lkm-aarch64-android13-5.15_kernelsu.ko` (`c8251322…`) → `cd060b9e…` | boots; `su -c id` = uid 0, ctx `u:r:ksu:s0`; `ksud 4.3.0 (uapi 6)`; manager `com.sukisu.ultra`; SELinux still **Enforcing** |

`boot`, `dtbo`, `vbmeta` stayed stock Meizu throughout. Restoring stock `init_boot` removes root at any time.

Correction to the ZHA-4389 note: SukiSU-Ultra v4.3.0 **does** ship an Android `ksud`, so `ksud boot-patch -b init_boot.img -m <lkm>.ko --kmi android13-5.15 --partition init_boot` works without the manager app; the manager only installs the userspace component.

Still blocked: OrangeFox/SHRP in `vendor_boot` (AVB-verified). SUSFS for banking-app hiding is solved with a loadable module — next section.

## SUSFS on SukiSU Ultra 4.3.0 via a loadable module (verified 2026-11-02, survives reboot)

`susfs_guard_lkm.ko` v2.3.0-gki (`024aa0de…`, 601 624 B) is a standalone LKM built from KernelSU-Next `kernel/susfs`. It is loaded with `ksud insmod`, which runs the module with kallsyms access, so it resolves SukiSU's own symbols by name — `ksu_uid_should_umount`, `ksu_patch_text`, `add_try_umount` are present in SukiSU Ultra 4.3.0's `kernelsu.ko` — and needs no kernel rebuild and no `vbmeta` change.

It loads even though the module vermagic (`5.15.202-android13-5.15.202_r00-dirty`) differs from the running kernel (`5.15.149-android13-8-00008-gbe074b05e5af-ab12096863`): `ksud insmod` bypasses the module version check, and symbol CRC matching does not apply because the guard looks its symbols up by name at runtime.

Evidence collected on the device:

| Check | Result |
|---|---|
| `ksud susfs implementation` / `version` / `variant` / `status` | `lkm` / `v2.3.0` / `GKI` / `true` |
| Manager home screen | `SuSFS Version v2.3.0 (Tracepoint Syscall Redirect)` |
| Interfaces | `/proc/susfs_{path,kstat,opath,open_redirect,enable_log,avc_spoof,hide_modules,hide_mounts}` |
| Supercall transport | kprobe on the `reboot` syscall, dmesg `susfs supercall: armed (reboot ABI, version v2.3.0)` |
| End-to-end `set-uname` | `uname -r`/`uname -v` from a non-root shell reported the spoofed strings; reset to the stock strings afterwards |
| `add-sus-path` | `rc=0`; hide gates key off app uids (≥10000), root and ksu contexts still see the path |
| `lsmod` | empty by design — the module filters itself out of `/proc/modules`; use `/sys/module/susfs_guard_lkm` |

Persistence is a KernelSU module, `susfs_guard_lkm` (zip `55740001…`, id `susfs_guard_lkm`, version v2.3.0-gki), whose `post-fs-data.sh` and `service.sh` both call `/data/adb/ksud insmod /data/adb/modules/susfs_guard_lkm/susfs_guard_lkm.ko` and skip when `/sys/module/susfs_guard_lkm` already exists. After `adb reboot` the log `/data/adb/ksu/log/susfs_guard.log` records `2026-11-02 17:18:27 loading …` / `17:18:29 rc=0 present=yes`; root kept working, SELinux stayed **Enforcing**, `boot`/`init_boot` kernel untouched.

`ksud susfs module install` only generates the settings auto-start module (`susfs_manager` v4.0.0) that re-applies the saved SUSFS configuration at boot; it neither ships nor loads an LKM. That is why the guard LKM needs its own module.

The module is published as pre-release `mblu21-susfs-lkm-20261102` with `susfs_guard_lkm.zip` (sha256 `55740001f1133f067b324a316c779fe8907275d120dfc94cb9d8cef359ac9f66`) and `SHA256SUMS`.

Not covered by SUSFS: hiding the SukiSU manager app itself and Play Integrity attestation (a PIF-style module is needed for apps that call the Integrity API).


