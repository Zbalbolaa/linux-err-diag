#!/usr/bin/env bash
# Dump the man pages of the commands our 6 domains rely on, as plain text.
# Run on your Kali/Ubuntu/Arch VM:  bash scripts/fetch_manpages.sh data/man
set -u
OUT="${1:-data/man}"; mkdir -p "$OUT"
CMDS=(pacman pacman.conf makepkg pacman-key
      systemctl journalctl systemd.unit systemd-analyze grub-install mkinitcpio bootctl fstab
      ip nmcli networkctl resolvectl ss ping dig ssh sshd_config nft iptables
      chmod chown chgrp sudo sudoers visudo usermod groupadd umask setfacl getfacl su
      mount umount fdisk parted lsblk blkid fsck e2fsck mkfs mkswap swapon df du
      xrandr Xorg xorg.conf startx loginctl)
for c in "${CMDS[@]}"; do
  if man -w "$c" >/dev/null 2>&1; then
    MANWIDTH=100 man -P cat "$c" 2>/dev/null | col -bx > "$OUT/$c.txt" && echo "ok  $c"
  else
    echo "--  $c (not installed here)"
  fi
done
