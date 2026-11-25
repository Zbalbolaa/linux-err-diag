"""Capability 4 - Flag risky commands (no LLM, pure rules). v2 (Lab 9): systemctl flags, pacman cache .part files.

flag("sudo rm -rf /var/lib/pacman")
 -> {"verdict": "risky", "reasons": [...], "requires_confirmation": True}
"""
import re
import shlex

# (rule id, regex on the normalised command, why it is risky)
RULES = [
    ("rm_recursive_force", r"\brm\s+(-\w*r\w*f\w*|-\w*f\w*r\w*|(-r|-R|--recursive)\s+(-f|--force)|(-f|--force)\s+(-r|-R|--recursive))\b",
     "recursive forced deletion"),
    ("rm_root_or_glob", r"\brm\b.*\s(/|/\*|~|\*|/(etc|usr|boot|var(?!/cache/pacman/pkg/)|home|lib)\S*)(\s|$)",
     "deletion on a system path or wildcard"),
    ("dd_write", r"\bdd\b.*\bof=/dev/", "raw write to a block device"),
    ("mkfs", r"\bmkfs(\.\w+)?\b|\bmkswap\b", "formats a partition (data loss)"),
    ("partition_edit", r"\b(fdisk|parted|sgdisk|wipefs)\b(?!.*\s-l\b)", "modifies the partition table"),
    ("chmod_777_recursive", r"\bchmod\b.*-\w*R\w*.*\b0?777\b|\bchmod\b.*\b0?777\b.*-\w*R", "world-writable recursively"),
    ("chmod_777", r"\bchmod\b.*\b0?777\b", "world-writable permissions"),
    ("chown_recursive_root", r"\bchown\b.*-\w*R\w*.*\s/(\s|$|etc|usr|var|bin|lib)", "recursive ownership change on system path"),
    ("pacman_rdd", r"\bpacman\b.*\s-R\w*dd", "removes a package ignoring dependencies"),
    ("pacman_overwrite", r"\bpacman\b.*--overwrite", "overwrites files owned by other packages"),
    ("pacman_partial_upgrade", r"\bpacman\b\s+-Sy(\s|$)(?!.*archlinux-keyring)(?!.*-Su)", "partial upgrade (unsupported on Arch)"),
    ("pacman_siglevel_never", r"SigLevel\s*=\s*Never", "disables package signature checking"),
    ("pacman_db_lock_rm", r"\brm\b.*/var/lib/pacman/db\.lck", "only safe if no pacman is running"),
    ("curl_pipe_shell", r"\b(curl|wget)\b.*\|\s*(sudo\s+)?(ba|z)?sh\b", "pipes remote code into a shell"),
    ("fork_bomb", r":\(\)\s*\{\s*:\|:&\s*\};:", "fork bomb"),
    ("redirect_to_disk", r">\s*/dev/(sd|nvme|vd|mmcblk)", "overwrites a block device"),
    ("disable_security", r"\b(setenforce\s+0|systemctl\s+(stop|disable|mask)(\s+--?[\w-]+)*\s+(apparmor|firewalld|nftables|ufw|iptables))\b",
     "disables a security control"),
    ("iptables_flush", r"\b(iptables\s+-F|nft\s+flush\s+ruleset)\b", "flushes all firewall rules"),
    ("sudoers_direct_edit", r"(>|>>|tee).*?/etc/sudoers\b|\b(nano|vim?|echo)\b.*\s/etc/sudoers\b", "edit sudoers without visudo"),
    ("mount_rw_force", r"\bfsck\b.*\s-\w*y", "auto-repairs a filesystem (unmount first)"),
    ("kill_init", r"\bkill\s+-9\s+1\b", "kills PID 1"),
]
COMPILED = [(rid, re.compile(rx), why) for rid, rx, why in RULES]


def _normalise(cmd: str) -> str:
    cmd = cmd.strip()
    try:  # collapse quoting so 'rm' "-rf" still matches
        cmd = " ".join(shlex.split(cmd, posix=True, comments=False))
    except ValueError:
        pass
    return re.sub(r"\s+", " ", cmd)


def flag(command: str) -> dict:
    """Return verdict for one shell command (may contain ; && || pipes)."""
    norm = _normalise(command)
    hits = [{"rule": rid, "why": why} for rid, rx, why in COMPILED if rx.search(norm)]
    return {"command": command, "verdict": "risky" if hits else "safe",
            "requires_confirmation": bool(hits), "reasons": hits}


def flag_all(commands):
    return [flag(c) for c in commands]


if __name__ == "__main__":
    import sys
    for line in sys.stdin:
        if line.strip():
            r = flag(line)
            print(f"{r['verdict'].upper():6} {line.strip()}  " +
                  ", ".join(h["rule"] for h in r["reasons"]))
