#!/bin/bash
#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

set -euo pipefail

ANDROID_ROOT="${ANDROID_ROOT:?set ANDROID_ROOT to the lineage-24.0 checkout}"
JOBS="${JOBS:-12}"
VARIANT="${VARIANT:-userdebug}"
STOCK_RELEASE_URL="${STOCK_RELEASE_URL:-https://github.com/tickernelz/android_stock_meizu_mblu21/releases/download/mblu21-stock-U01005-20261031}"

cd "${ANDROID_ROOT}"
stock_dir="$(mktemp -d)"
trap 'rm -rf "${stock_dir}"' EXIT
for f in boot_a.bin vendor_a.img; do
    curl -fL --retry 3 -o "${stock_dir}/${f}" "${STOCK_RELEASE_URL}/${f}"
done
(cd device/meizu/mblu21 && ./extract-files.py "${stock_dir}")

export USE_CCACHE=1
export CCACHE_EXEC="${CCACHE_EXEC:-$(command -v ccache)}"
export CCACHE_DIR="${CCACHE_DIR:-${HOME}/.cache/ccache-lineage}"
ccache -M "${CCACHE_SIZE:-50G}" >/dev/null

set +u
source build/envsetup.sh
breakfast mblu21 "${VARIANT}"
set -u

nice -n 10 m -j"${JOBS}" bacon
