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
