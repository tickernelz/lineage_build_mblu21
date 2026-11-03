#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0

import argparse
import hashlib
import json
import os
import zipfile

REPO = "tickernelz/lineage_build_mblu21"


def ota_metadata(package):
    with zipfile.ZipFile(package) as z:
        text = z.read("META-INF/com/android/metadata").decode()
    return dict(line.split("=", 1) for line in text.splitlines() if "=" in line)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Write the LineageOS Updater feed for an A/B OTA package published on a GitHub release.")
    parser.add_argument("package")
    parser.add_argument("tag")
    parser.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "mblu21.json"))
    args = parser.parse_args()

    meta = ota_metadata(args.package)
    if meta.get("ota-type") != "AB" or meta.get("pre-device") != "mblu21":
        raise SystemExit("not an mblu21 A/B OTA package")
    filename = os.path.basename(args.package)
    version, _, rest = filename.removeprefix("lineage-").partition("-")
    release_type = rest.split("-")[1].lower()
    feed = [
        {
            "datetime": int(meta["post-timestamp"]),
            "type": release_type,
            "version": version,
            "files": [
                {
                    "filename": filename,
                    "os_patch_level": meta["post-security-patch-level"],
                    "os_sdk_level": int(meta["post-sdk-level"]),
                    "ota_property_files": meta["ota-property-files"].strip(),
                    "sha256": sha256(args.package),
                    "size": os.path.getsize(args.package),
                    "url": f"https://github.com/{REPO}/releases/download/{args.tag}/{filename}",
                }
            ],
        }
    ]
    with open(args.out, "w") as f:
        json.dump(feed, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
