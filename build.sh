#!/bin/bash
#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

set -euo pipefail

ANDROID_ROOT="${ANDROID_ROOT:?set ANDROID_ROOT to the lineage-24.0 checkout}"
JOBS="${JOBS:-12}"
VARIANT="${VARIANT:-userdebug}"

cd "${ANDROID_ROOT}"
bash vendor/meizu/mblu21/fetch-images.sh

export USE_CCACHE=1
export CCACHE_EXEC="${CCACHE_EXEC:-$(command -v ccache)}"
export CCACHE_DIR="${CCACHE_DIR:-${HOME}/.cache/ccache-lineage}"
ccache -M "${CCACHE_SIZE:-50G}" >/dev/null

set +u
source build/envsetup.sh
breakfast mblu21 "${VARIANT}"
set -u

nice -n 10 m -j"${JOBS}" bacon
