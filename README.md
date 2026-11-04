# LineageOS 24.0 for Meizu mBlu 21 (M416H)

Local manifest, build script and static image checks for the unofficial LineageOS 24.0 build of the Meizu mBlu 21.

**Status: boots and runs daily use on one M416H; the test matrix is partial.** Releases are pre-releases; one that has not been booted on the phone says so in its title. [PLAN.md](PLAN.md) defines "working".

| Build | Tested on the phone |
|---|---|
| [`lineage-24.0-20261103-UNOFFICIAL-mblu21`](https://github.com/tickernelz/lineage_build_mblu21/releases/tag/lineage-24.0-20261103-UNOFFICIAL-mblu21) (device `7dd4b55`, vendor `e14f366`, this repo `0c2dc99`) | 2026-11-03: boot, display, touch, FBE unlock with a PIN, USB adb, charging, Wi-Fi, Telkomsel LTE data, microphone, rear and front camera photo and video. **Emergency call, GPS, MTP and USB tethering: passed, manual test by Zhafron 2026-11-03.** SELinux is permissive in this build. The release notes carry the full table. |
| Local build adding device `79d312d` and `0d92969` | 2026-11-03: SELinux enforcing with Wi-Fi, LTE, Bluetooth on and camera working; voice calls with two-way audio and SMS; Volume Down in Android and Lineage Recovery without resetting the phone. Not released on its own. |
| `lineage-24.0-20261103-UNOFFICIAL-mblu21` r3 on slot _b (installed by the Updater), SELinux enforcing | 2026-11-03, measured over adb: accelerometer at rest (-0.01, -0.50, 9.85) m/s2; battery Charging at 4.39 V, 38.9 C, level 99; screenrecord encodes with `c2.unisoc.avc.encoder` and playback decodes with `c2.unisoc.avc.decoder`; Wi-Fi factory MAC 90:f0:52:dc:64:ef and Bluetooth MAC 90:07:23:EA:FE:E4 equal the stock `prodnv` values (the connected MAC is Android's per-network random one). **Face unlock: enroll failed** because Settings held the front camera the face HAL needs; fix on device branch `zha4374-face`, not yet tested. **Fingerprint: cannot be proven on this unit, its sensor is broken in hardware.** |
| [`lineage-24.0-20261103-UNOFFICIAL-mblu21-r6`](https://github.com/tickernelz/lineage_build_mblu21/releases/tag/lineage-24.0-20261103-UNOFFICIAL-mblu21-r6) (device `zha4555-volte`: Unisoc IMS stack, OTA without `boot`/`dtbo`/`vbmeta`, Updater feed), SELinux enforcing | 2026-11-03: installed by the LineageOS Updater (as were r3, r4 and r5, alternating slots), `/data` and SukiSU root kept. IMS stack bound as MMTEL with `ims_bridged`, `srmi_proxyd` and RadioInteractor running, no SELinux denials, no crashes. **VoLTE does not register: Telkomsel reports IMS voice over PS not supported (`mVopsSupport = 3`), the same value the stock firmware logged on 2026-11-01.** r2 never booted; r5 crash-looped `com.android.phone` and is withdrawn. |
| [`lineage-24.0-20261103-UNOFFICIAL-mblu21-r7`](https://github.com/tickernelz/lineage_build_mblu21/releases/tag/lineage-24.0-20261103-UNOFFICIAL-mblu21-r7) (r6 plus the `ions_ex` service label) | 2026-11-03: installed by the Updater to slot `_b`; after 17 minutes 0 SELinux denials and 0 crashes for the IMS domains. **VoLTE on Telkomsel: network/SIM limitation** — the modem has IMS voice on (`AT+CAVIMS: 1`) but the network reports VoPS not supported (`AT+CIREP: 1,0`), and the stock firmware never showed VoLTE with this SIM; retest with another operator's SIM. |
| [`lineage-24.0-20261103-UNOFFICIAL-mblu21-r8`](https://github.com/tickernelz/lineage_build_mblu21/releases/tag/lineage-24.0-20261103-UNOFFICIAL-mblu21-r8) (r7 on top of the source-built kernel modules, IMS extracted by `extract-files.py`) | not booted yet; not in the Updater feed |
| [`lineage-24.0-20261102-UNOFFICIAL-mblu21`](https://github.com/tickernelz/lineage_build_mblu21/releases/tag/lineage-24.0-20261102-UNOFFICIAL-mblu21) | not booted; superseded by 20261103 |

Not tested on any build yet: Bluetooth pairing, fingerprint. Battery deep sleep was not measured: the overnight run was skipped by Zhafron's decision on 2026-11-03, so there is no drain data. VoLTE on the Telkomsel test SIM is a network/SIM limitation (see r7).

The 2026-11-02 hardware session found that this phone's bootloader rejects every `vbmeta` it did not get from Meizu, even with the bootloader unlocked. Builds since 20261103 therefore keep `boot`, `dtbo` and every `vbmeta*` stock and drop the `avb` flags from the first-stage fstab. The measurements are in [BRINGUP_STATUS_2026-11-02.md](BRINGUP_STATUS_2026-11-02.md) and in [android_kernel_meizu_mblu21/docs/HARDWARE-2026-11-02.md](https://github.com/tickernelz/android_kernel_meizu_mblu21/blob/main/docs/HARDWARE-2026-11-02.md). Root works through `init_boot`; that lives in the kernel repository.

## Repositories

| Repository | Content |
|---|---|
| [android_device_meizu_mblu21](https://github.com/tickernelz/android_device_meizu_mblu21) | device tree |
| [android_vendor_meizu_mblu21](https://github.com/tickernelz/android_vendor_meizu_mblu21) | stock images and proprietary files |
| [android_kernel_meizu_mblu21](https://github.com/tickernelz/android_kernel_meizu_mblu21) | kernel path, root images, step-by-step root tutorial |

## Build

Requirements: about 300 GB free disk for source and `out/`, and about 50 GB of RAM plus swap for the Soong analysis phase. The first complete build (2026-11-02, `-j12`, 16 cores, 62 GB RAM, 96 GB swap) peaked at 43.6 GB RAM + 5.6 GB swap during analysis and took about 3.5 hours of compilation. On a 28 GB RAM WSL host the analysis never finished.

Face unlock needs `patches/frameworks_av-unlisted-hidden-cameras.patch`: the stock face HAL opens camera 30, which the Unisoc camera HAL serves without listing it, and the patch lets cameraserver register the ids in `ro.camera.unlisted_hidden_ids` (set by the device tree) as hidden secure cameras that only system-uid clients can open. Apply it with `git -C frameworks/av apply` before building, and revert it with `git -C frameworks/av checkout -- services/camera/libcameraservice/common` before the next `repo sync`.

That build capped the Soong Go heap with `GOMEMLIMIT`. `soong_build` runs under `env -i`, so `patches/build_soong-gomemlimit.patch` passes `SOONG_GOMEMLIMIT` through; apply it with `git -C build/soong apply` and export `SOONG_GOMEMLIMIT=44GiB` (about 90% of the memory you give the build). It is optional on hosts with more RAM. Revert it with `git -C build/soong checkout -- ui/build/soong.go` before the next `repo sync` or `/opt/crave/resync.sh`, which refuse to update a project with uncommitted changes.

```
mkdir lineage-24.0 && cd lineage-24.0
repo init -u https://github.com/LineageOS/android.git -b lineage-24.0 --git-lfs --depth=1
git clone --depth 1 https://github.com/tickernelz/lineage_build_mblu21 .repo/local_manifests
repo sync -c --no-tags -j8
ANDROID_ROOT=$PWD .repo/local_manifests/build.sh
```

GitHub-hosted runners (4 vCPU, 16 GB RAM, 14 GB disk) cannot hold the source tree, so the ROM is built on a local machine and CI here only lints the scripts.

### foss.crave.io

This repository is laid out as a local manifest directory: `mblu21.xml` sits at its root, so cloning it into `.repo/local_manifests` is enough. Every repository it references is public, as Crave requires. From a Crave devspace (the script re-initialises the checkout to `lineage-24.0`, so a base project on another LineageOS branch also works):

```
./crave-build.sh
```

The command downloads `vendor_a.img` from the [`mblu21-stock-U01005-20261031`](https://github.com/tickernelz/android_stock_meizu_mblu21/releases/tag/mblu21-stock-U01005-20261031) release, stops unless it matches its SHA-256, and runs `device/meizu/mblu21/extract-files.py` on it before building, which adds `vendor.img` to the vendor tree.

## Static checks

`validate-images.py` compares the build output with the stock layout: image sizes against partition sizes, boot image header versions, kernel hash and command lines, vbmeta chain layout and rollback index locations, the descriptors in each chained vbmeta, `avbtool verify_image --follow_chain_partitions`, and the dynamic partitions against the `group_unisoc` size.

```
./validate-images.py $OUT --firmware-dir <stock_dump> \
    --stock-kernel-sha256 8d46374c1cf3ccc7a332c1dd5abc10a5005011badc10cc37e7fbad45b921f20d
```

Run against the stock dump itself it passes 41/41 checks.
