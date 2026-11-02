# LineageOS 24.0 for Meizu mBlu 21 (M416H)

Local manifest, build script and static image checks for the unofficial LineageOS 24.0 build of the Meizu mBlu 21.

**Status: untested on hardware.** Releases are pre-releases labelled `UNTESTED` until they are booted on a phone. See [PLAN.md](PLAN.md) for the bring-up plan and the definition of "working".

## Repositories

| Repository | Content |
|---|---|
| [android_device_meizu_mblu21](https://github.com/tickernelz/android_device_meizu_mblu21) | device tree |
| [android_vendor_meizu_mblu21](https://github.com/tickernelz/android_vendor_meizu_mblu21) | stock images and proprietary files |

## Build

Requirements: about 300 GB free disk for source and `out/`, and about 50 GB of RAM plus swap for the Soong analysis phase. The first complete build (2026-11-02, `-j12`, 16 cores, 62 GB RAM, 96 GB swap) peaked at 43.6 GB RAM + 5.6 GB swap during analysis and took about 3.5 hours of compilation. On a 28 GB RAM WSL host the analysis never finished.

That build capped the Soong Go heap with `GOMEMLIMIT`. `soong_build` runs under `env -i`, so `patches/build_soong-gomemlimit.patch` passes `SOONG_GOMEMLIMIT` through; apply it with `git -C build/soong apply` and export `SOONG_GOMEMLIMIT=44GiB` (about 90% of the memory you give the build). It is optional on hosts with more RAM.

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

The command fetches the `vendor.img` release asset and checks every prebuilt image against `images.sha256` before building.

## Static checks

`validate-images.py` compares the build output with the stock layout: image sizes against partition sizes, boot image header versions, kernel hash and command lines, vbmeta chain layout and rollback index locations, the descriptors in each chained vbmeta, `avbtool verify_image --follow_chain_partitions`, and the dynamic partitions against the `group_unisoc` size.

```
./validate-images.py $OUT --firmware-dir <stock_dump> \
    --stock-kernel-sha256 8d46374c1cf3ccc7a332c1dd5abc10a5005011badc10cc37e7fbad45b921f20d
```

Run against the stock dump itself it passes 41/41 checks.
