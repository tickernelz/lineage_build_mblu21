#!/bin/bash
#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

set -euo pipefail

MANIFEST_URL="${MANIFEST_URL:-https://github.com/tickernelz/lineage_build_mblu21}"
VARIANT="${VARIANT:-userdebug}"

crave run --no-patch -- "rm -rf .repo/local_manifests && \
git clone --depth 1 ${MANIFEST_URL} .repo/local_manifests && \
/opt/crave/resync.sh && \
bash vendor/meizu/mblu21/fetch-images.sh && \
source build/envsetup.sh && \
breakfast mblu21 ${VARIANT} && \
m bacon"
