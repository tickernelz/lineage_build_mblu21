# Flashing LineageOS 24.0 on the Meizu mBlu 21 (M416H)

**Everything here erases data and can leave the phone unbootable.** The image in this repository is built but has never been booted. Take a full partition dump first; the stock restore path in the last section depends on it.

All commands run on Linux (Fedora). `adb`, `fastboot` and `spd_dump` must work; the Unisoc download-mode USB ID needs a udev rule:

    SUBSYSTEM=="usb", ATTR{idVendor}=="1782", ATTR{idProduct}=="4d00", TAG+="uaccess"

## 1. Bootloader unlock

The mBlu 21 is an Unisoc UMS9230 device. Unlock uses [TomKing062's CVE-2022-38694 release](https://github.com/TomKing062/CVE-2022-38694_unlock_bootloader/releases) through download mode; build `spd_dump`, `gen_spl-unlock` and `chsize` from that repository on Linux.

Put the phone in download mode: power it off, hold **Volume Down**, plug USB, keep holding until `lsusb` shows `1782:4d00`. Work from the directory holding `fdl1-dl.bin`, `fdl2-dl.bin`, `fdl2-cboot.bin` and `misc-wipe.bin`.

    cd ~/re/mblu21/tools/linux
    ./spd_dump --wait 300 exec_addr 0x65015f08 fdl fdl1-dl.bin 0x65000800 fdl fdl2-dl.bin 0x9efffe00 exec r splloader r uboot e splloader e splloader_bak reset
    ./gen_spl-unlock splloader.bin
    mv splloader.bin u-boot-spl-16k-sign.bin
    ./chsize uboot.bin
    mv uboot.bin uboot_bak.bin
    ./spd_dump --wait 300 exec_addr 0x65015f08 fdl fdl1-dl.bin 0x65000800 fdl fdl2-dl.bin 0x9efffe00 exec w uboot fdl2-cboot.bin reset
    sleep 10
    ./spd_dump exec_addr 0x65015f08 fdl spl-unlock.bin 0x65000800
    ./spd_dump exec_addr 0x65015f08 fdl fdl1-dl.bin 0x65000800 fdl fdl2-dl.bin 0x9efffe00 exec verbose 2 read_part miscdata 8192 64 m.bin reset
    xxd m.bin | head

`m.bin` of 64 zeros means still locked; a device string plus two hashes means unlocked. Run the unlock line twice if the first run leaves it locked, then restore the bootloader:

    ./spd_dump exec_addr 0x65015f08 fdl fdl1-dl.bin 0x65000800 fdl fdl2-dl.bin 0x9efffe00 exec r boot w splloader u-boot-spl-16k-sign.bin w uboot uboot_bak.bin w misc misc-wipe.bin reset

`find port failed` is not an error: replug the phone in download mode and rerun the same command.

## 2. Flash the release

    mkdir -p ~/mblu21-flash && cd ~/mblu21-flash
    gh release download lineage-24.0-20261102-UNOFFICIAL-mblu21 -R tickernelz/lineage_build_mblu21
    sha256sum -c SHA256SUMS

### With fastboot

    fastboot devices
    fastboot --disable-verification --disable-verity flash vbmeta vbmeta.img
    fastboot flash dtbo dtbo.img
    fastboot flash init_boot init_boot.img
    fastboot flash boot boot.img
    fastboot flash vendor_boot vendor_boot.img
    fastboot reboot recovery
    adb sideload lineage-24.0-20261102-UNOFFICIAL-mblu21.zip

In Lineage Recovery finish with *Factory reset → Format data → Reboot system*.

### Without fastboot, through download mode

The OTA writes dynamic partitions, so this route needs `super.img` from `m superimage` in the build tree; it replaces `super` as a whole.

    cd ~/re/mblu21/tools/linux
    D=~/mblu21-flash
    ./spd_dump exec_addr 0x65015f08 fdl fdl1-dl.bin 0x65000800 fdl fdl2-dl.bin 0x9efffe00 exec \
        w boot_a $D/boot.img w init_boot_a $D/init_boot.img w vendor_boot_a $D/vendor_boot.img \
        w dtbo_a $D/dtbo.img w vbmeta_a $D/vbmeta.img w super $D/super.img reset

The active slot is `_a`; write `_b` partitions only after switching slots.

## 3. Restore stock

Keep the 44-partition dump (`full_dump/*.bin`) reachable. Write every partition back from download mode:

    ./spd_dump exec_addr 0x65015f08 fdl fdl1-dl.bin 0x65000800 fdl fdl2-dl.bin 0x9efffe00 exec \
        w boot_a <dump>/boot_a.bin w super <dump>/super.bin w ... reset

Restore `splloader`, `uboot_a`, `misc` and `vbmeta_a` last, then `reset`. When the phone boots to the stock system again, take a fresh dump and compare it with the old one.
