#!/bin/bash
#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

set -euo pipefail

MANIFEST_URL="${MANIFEST_URL:-https://github.com/tickernelz/lineage_build_mblu21}"
VARIANT="${VARIANT:-userdebug}"
STOCK_RELEASE_URL="${STOCK_RELEASE_URL:-https://github.com/tickernelz/android_stock_meizu_mblu21/releases/download/mblu21-stock-U01005-20261031}"

crave run --no-patch -- "rm -rf .repo/local_manifests && \
git clone --depth 1 ${MANIFEST_URL} .repo/local_manifests && \
repo init -u https://github.com/LineageOS/android.git -b lineage-24.0 --git-lfs && \
/opt/crave/resync.sh && \
rm -rf /tmp/mblu21-stock && mkdir /tmp/mblu21-stock && \
for f in boot_a.bin vendor_a.img; do curl -fL --retry 3 -o /tmp/mblu21-stock/\$f ${STOCK_RELEASE_URL}/\$f || exit 1; done && \
(cd device/meizu/mblu21 && ./extract-files.py /tmp/mblu21-stock) && \
source build/envsetup.sh && \
breakfast mblu21 ${VARIANT} && \
m bacon"
