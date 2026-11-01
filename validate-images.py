#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

"""Static checks of mblu21 build output against the stock partition layout."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

PARTITION_SIZES = {
    "boot": 67108864,
    "init_boot": 8388608,
    "vendor_boot": 104857600,
    "dtbo": 8388608,
    "vbmeta": 1048576,
    "vbmeta_system": 1048576,
    "vbmeta_vendor": 1048576,
    "vbmeta_system_ext": 1048576,
    "vbmeta_product": 1048576,
    "vbmeta_odm": 1048576,
}

STOCK_CHAINS = {
    "boot": 1,
    "init_boot": 8,
    "dtbo": 6,
    "vendor_boot": 18,
    "vbmeta_system": 2,
    "vbmeta_vendor": 4,
    "vbmeta_system_ext": 3,
    "vbmeta_product": 5,
    "vbmeta_odm": 7,
    "l_modem": 11,
    "l_ldsp": 12,
    "l_gdsp": 13,
    "pm_sys": 14,
    "l_agdsp": 15,
}

FIRMWARE_PARTITIONS = ["l_modem", "l_ldsp", "l_gdsp", "pm_sys", "l_agdsp"]

STOCK_VBMETA_CONTENTS = {
    "vbmeta_system": {"system", "system_ext"},
    "vbmeta_vendor": {"vendor"},
    "vbmeta_system_ext": {"system_dlkm", "vendor_dlkm"},
    "vbmeta_product": {"product"},
    "vbmeta_odm": {"odm"},
}

DYNAMIC_PARTITIONS = ["system", "system_ext", "product", "vendor", "odm", "vendor_dlkm", "system_dlkm"]
GROUP_SIZE = 5553258496

STOCK_VENDOR_CMDLINE = "console=ttyS1,115200n8 bootconfig bootconfig"
STOCK_VENDOR_BOOTCONFIG = "androidboot.hardware=ums9230_6h10"


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def avb_info(avbtool, image):
    return run([avbtool, "info_image", "--image", image])


def unpack(tool, image, out):
    info = run([tool, "--boot_img", image, "--out", out, "--format=info"])
    fields = {}
    for line in info.splitlines():
        m = re.match(r"^([a-z_ .]+?):\s*(.*)$", line.strip())
        if m:
            fields[m.group(1)] = m.group(2)
    return fields


def extract_ramdisks(vendor_boot_dir):
    found = {}
    for name in sorted(os.listdir(vendor_boot_dir)):
        if not name.startswith("vendor_ramdisk") or name == "vendor_ramdisk-by-name":
            continue
        dest = os.path.join(vendor_boot_dir, name + ".d")
        os.makedirs(dest)
        data = run_bytes(["lz4", "-dc", os.path.join(vendor_boot_dir, name)])
        subprocess.run(["cpio", "-idm", "--quiet"], input=data, cwd=dest, check=True)
        found[name] = dest
    return found


def run_bytes(cmd):
    return subprocess.run(cmd, check=True, capture_output=True).stdout


def ramdisk_types(info):
    return re.findall(r"type:\s*(0x[0-9a-f]+)", info)


def vendor_owned_files(root):
    files = {}
    for rel in ("lib/modules", "first_stage_ramdisk"):
        base = os.path.join(root, rel)
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            path = os.path.join(base, name)
            if not os.path.isfile(path):
                continue
            if rel == "lib/modules" and not (name.endswith(".ko") or name in ("modules.load", "modules.load.recovery")):
                continue
            if rel == "first_stage_ramdisk" and not name.startswith("fstab."):
                continue
            files[f"{rel}/{name}"] = sha256(path)
    for name in os.listdir(root):
        if name.startswith("ueventd.") and name.endswith(".rc"):
            files[name] = sha256(os.path.join(root, name))
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("product_out")
    parser.add_argument("--stock-kernel-sha256", required=True)
    parser.add_argument("--avbtool", default=shutil.which("avbtool") or "avbtool")
    parser.add_argument("--unpack-bootimg", default=shutil.which("unpack_bootimg") or "unpack_bootimg")
    parser.add_argument("--firmware-dir", required=True, help="stock dump holding vendor_boot_a.bin, l_modem_a.bin and the other chained firmware partitions")
    parser.add_argument("--json", help="write results as JSON to this path")
    args = parser.parse_args()

    out = args.product_out
    rows = []
    failures = []

    def check(name, ok, detail):
        rows.append({"check": name, "ok": ok, "detail": detail})
        if not ok:
            failures.append(name)

    for part, limit in PARTITION_SIZES.items():
        path = os.path.join(out, f"{part}.img")
        if not os.path.exists(path):
            check(f"{part}.img exists", False, "missing")
            continue
        size = os.path.getsize(path)
        check(f"{part}.img size", size <= limit, f"{size} <= {limit}")

    with tempfile.TemporaryDirectory() as tmp:
        boot = unpack(args.unpack_bootimg, os.path.join(out, "boot.img"), os.path.join(tmp, "boot"))
        check("boot header v4", boot.get("boot image header version") == "4", boot.get("boot image header version", "?"))
        check("boot cmdline = stock", boot.get("command line args", "") == "", repr(boot.get("command line args", "")))
        kernel_sha = sha256(os.path.join(tmp, "boot", "kernel"))
        check("boot kernel = stock GKI", kernel_sha == args.stock_kernel_sha256, kernel_sha)

        init_boot = unpack(args.unpack_bootimg, os.path.join(out, "init_boot.img"), os.path.join(tmp, "init_boot"))
        check("init_boot header v4", init_boot.get("boot image header version") == "4", init_boot.get("boot image header version", "?"))
        check("init_boot kernel empty", init_boot.get("kernel_size") == "0", init_boot.get("kernel_size", "?"))
        check("init_boot ramdisk present", int(init_boot.get("ramdisk size", "0")) > 0, init_boot.get("ramdisk size", "?"))

        vboot = unpack(args.unpack_bootimg, os.path.join(out, "vendor_boot.img"), os.path.join(tmp, "vendor_boot"))
        check("vendor_boot header v4", vboot.get("vendor boot image header version") == "4", vboot.get("vendor boot image header version", "?"))
        check("vendor_boot cmdline = stock", vboot.get("vendor command line args") == STOCK_VENDOR_CMDLINE, repr(vboot.get("vendor command line args")))
        with open(os.path.join(tmp, "vendor_boot", "bootconfig"), "rb") as f:
            bootconfig = f.read().decode(errors="replace").strip("\x00\n ")
        check("vendor_boot bootconfig = stock", bootconfig == STOCK_VENDOR_BOOTCONFIG, repr(bootconfig))

        stock_vb = os.path.join(tmp, "stock_vendor_boot")
        unpack(args.unpack_bootimg, os.path.join(args.firmware_dir, "vendor_boot_a.bin"), stock_vb)
        check("vendor_boot dtb = stock", sha256(os.path.join(tmp, "vendor_boot", "dtb")) == sha256(os.path.join(stock_vb, "dtb")), sha256(os.path.join(tmp, "vendor_boot", "dtb")))

        built = extract_ramdisks(os.path.join(tmp, "vendor_boot"))
        stock = extract_ramdisks(stock_vb)
        info = run([args.unpack_bootimg, "--boot_img", os.path.join(out, "vendor_boot.img"), "--format=info", "--out", os.path.join(tmp, "vbinfo")])
        types = ramdisk_types(info)
        check("vendor_boot has platform + recovery ramdisks", sorted(types) == ["0x1", "0x2"], ",".join(types))

        merged = {}
        for name, root in built.items():
            merged.update(vendor_owned_files(root))
        expected = vendor_owned_files(next(iter(stock.values())))
        missing = sorted(set(expected) - set(merged))
        changed = sorted(k for k in expected if k in merged and merged[k] != expected[k])
        check("vendor ramdisk vendor files = stock", not missing and not changed, f"{len(expected)} files, missing {len(missing)}, changed {len(changed)}" + (f" e.g. {(missing + changed)[0]}" if missing or changed else ""))

        recovery_roots = [root for name, root in built.items() if os.path.isfile(os.path.join(root, "system", "bin", "recovery"))]
        check("recovery ramdisk has /system/bin/recovery", bool(recovery_roots), str(len(recovery_roots)))
        check("recovery ramdisk has fastbootd", any(os.path.isfile(os.path.join(r, "system", "bin", "fastbootd")) for r in recovery_roots), "system/bin/fastbootd")

    vbmeta = avb_info(args.avbtool, os.path.join(out, "vbmeta.img"))
    chains = dict(re.findall(r"Partition Name:\s+(\S+)\s+Rollback Index Location:\s+(\d+)", vbmeta))
    for part, loc in STOCK_CHAINS.items():
        got = chains.get(part)
        check(f"vbmeta chains {part}@{loc}", got == str(loc), f"location {got}")
    extra = set(chains) - set(STOCK_CHAINS)
    check("vbmeta has no extra chains", not extra, ",".join(sorted(extra)) or "none")
    inline = len(re.findall(r"^\s+(Hash|Hashtree) descriptor:", vbmeta, re.M))
    check("vbmeta has no inline hash/hashtree descriptors", inline == 0, str(inline))

    for image, expected in STOCK_VBMETA_CONTENTS.items():
        info = avb_info(args.avbtool, os.path.join(out, f"{image}.img"))
        names = set(re.findall(r"Partition Name:\s+(\S+)", info))
        check(f"{image} descriptors", names == expected, ",".join(sorted(names)))

    with tempfile.TemporaryDirectory() as tree:
        for name in os.listdir(out):
            if name.endswith(".img"):
                os.symlink(os.path.abspath(os.path.join(out, name)), os.path.join(tree, name))
        for part in FIRMWARE_PARTITIONS:
            os.symlink(os.path.abspath(os.path.join(args.firmware_dir, f"{part}_a.bin")), os.path.join(tree, f"{part}.img"))
        try:
            run([args.avbtool, "verify_image", "--image", os.path.join(tree, "vbmeta.img"), "--follow_chain_partitions"])
            check("avbtool verify_image --follow_chain_partitions", True, "all descriptors match images")
        except subprocess.CalledProcessError as e:
            check("avbtool verify_image --follow_chain_partitions", False, (e.stderr or e.stdout).strip().splitlines()[-1])

    total = 0
    for part in DYNAMIC_PARTITIONS:
        path = os.path.join(out, f"{part}.img")
        if os.path.exists(path):
            total += os.path.getsize(path)
        else:
            check(f"{part}.img exists", False, "missing")
    check("dynamic partitions fit group_unisoc", total <= GROUP_SIZE, f"{total} <= {GROUP_SIZE}")

    width = max(len(r["check"]) for r in rows)
    for r in rows:
        print(f"{'PASS' if r['ok'] else 'FAIL'}  {r['check']:<{width}}  {r['detail']}")
    if args.json:
        with open(args.json, "w") as f:
            json.dump(rows, f, indent=2)
    print(f"{len(rows) - len(failures)}/{len(rows)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
