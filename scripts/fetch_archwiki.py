#!/usr/bin/env python3
"""Download the Arch Wiki corpus (6 domains) and split it into sections.

Run on your own machine (needs internet):
    pip install requests beautifulsoup4
    python scripts/fetch_archwiki.py --out data/corpus.jsonl

Output: one JSON line per section
    {"id", "domain", "page", "section", "url", "text"}

Pages = seed list below + members of each domain's wiki categories,
capped at --per-domain pages per domain (default 25 -> ~150 pages).
"""
import argparse, json, re, time
import requests
from bs4 import BeautifulSoup

API = "https://wiki.archlinux.org/api.php"
UA = {"User-Agent": "UIR-AI-course-project/0.1 (student project, polite crawl)"}

DOMAINS = {
    "pacman": {
        "seed": ["Pacman", "Pacman/Package signing", "Pacman/Tips and tricks",
                 "Pacman/Rosetta", "Pacman/Pacnew and Pacsave", "Mirrors",
                 "Reflector", "Arch User Repository", "Makepkg", "Downgrading packages",
                 "System maintenance", "Arch Linux Archive", "Official repositories"],
        "categories": ["Category:Package manager", "Category:Package management"],
    },
    "boot_systemd": {
        "seed": ["Arch boot process", "Systemd", "Systemd/Journal", "Systemd/Timers",
                 "GRUB", "Systemd-boot", "Mkinitcpio", "Kernel parameters",
                 "Unified Extensible Firmware Interface", "Fstab", "General troubleshooting",
                 "Microcode", "Kernel module"],
        "categories": ["Category:Boot process", "Category:Boot loaders"],
    },
    "network": {
        "seed": ["Network configuration", "NetworkManager", "Systemd-networkd",
                 "Systemd-resolved", "Domain name resolution", "Network configuration/Wireless",
                 "Iwd", "Wpa_supplicant", "Dhcpcd", "OpenSSH", "Nftables", "Iptables",
                 "Network configuration/Ethernet"],
        "categories": ["Category:Network configuration", "Category:Wireless networking"],
    },
    "permissions": {
        "seed": ["File permissions and attributes", "Users and groups", "Sudo", "Polkit",
                 "Su", "Umask", "Access Control Lists", "Capabilities", "Security",
                 "AppArmor", "PAM", "SSH keys", "Doas", "Core dump", "Audit framework"],
        "categories": ["Category:Security", "Category:Users and groups"],
    },
    "disks": {
        "seed": ["File systems", "Partitioning", "Fdisk", "Parted", "Ext4", "Btrfs",
                 "Swap", "Fsck", "Udisks", "Persistent block device naming", "LVM",
                 "Dm-crypt", "Mount", "S.M.A.R.T."],
        "categories": ["Category:File systems", "Category:Storage"],
    },
    "display": {
        "seed": ["Xorg", "Wayland", "Display manager", "GDM", "SDDM", "LightDM",
                 "NVIDIA", "AMDGPU", "Intel graphics", "Kernel mode setting",
                 "Xrandr", "Hardware video acceleration", "Desktop environment"],
        "categories": ["Category:X server", "Category:Graphics", "Category:Display managers"],
    },
}


# Off-topic pages pulled in by broad categories (no terminal errors to diagnose)
EXCLUDE = {"Guix", "Nix", "Pkgsrc", "Bisecting bugs with Git", "Ghostmirror", "Makepkg-optimize",
           "Aurweb RPC interface", "AUR submission guidelines", "Activating numlock on bootup",
           "Bootchart", "DSDT", "Kdump", "Kexec", "AirPort", "Wireless bonding", "Ad-hoc networking",
           "Arch Security Team", "ClamAV", "FreeIPA", "List of applications/Security",
           "Metasploit Framework", "Nmap", "Oo7", "Parental control", "Disk quota", "Dm-verity",
           "BeeGFS", "Davfs2", "Foremost", "Clipboard", "Cursor themes", "Desktop notifications",
           "Dunst", "Greenclip", "Icons", "Idesk", "Extreme Multihead"}


def api(**params):
    params.update(format="json", formatversion=2)
    r = requests.get(API, params=params, headers=UA, timeout=30)
    r.raise_for_status()
    time.sleep(0.5)  # be polite
    return r.json()


def category_members(cat, limit=50):
    data = api(action="query", list="categorymembers", cmtitle=cat,
               cmnamespace=0, cmlimit=limit)
    return [m["title"] for m in data.get("query", {}).get("categorymembers", [])
            if not re.search(r"\((Español|Français|Deutsch|Русский|日本語|简体中文|Português|Italiano|Polski)\)", m["title"])]


def page_sections(title):
    data = api(action="parse", page=title, prop="text", redirects=1)
    if "error" in data:
        return []
    real = data["parse"]["title"]
    soup = BeautifulSoup(data["parse"]["text"], "html.parser")
    for junk in soup.select(".mw-editsection, .toc, #toc, .archwiki-template-box, sup.reference, style, script"):
        junk.decompose()
    root = soup.select_one(".mw-parser-output") or soup
    sections, cur_title, cur_anchor, buf = [], "Introduction", "", []

    def flush():
        txt = re.sub(r"\n{3,}", "\n\n", "\n".join(buf)).strip()
        if len(txt) > 80:
            url = "https://wiki.archlinux.org/title/" + real.replace(" ", "_")
            sections.append({"page": real, "section": cur_title,
                             "url": url + (f"#{cur_anchor}" if cur_anchor else ""),
                             "text": txt})

    for el in root.children:
        name = getattr(el, "name", None)
        if name in ("h2", "h3", "h4") or (name == "div" and "mw-heading" in (el.get("class") or [])):
            flush()
            h = el if name != "div" else el.find(["h2", "h3", "h4"])
            cur_title = h.get_text(" ", strip=True) if h else el.get_text(" ", strip=True)
            cur_anchor = (h.get("id") if h else None) or cur_title.replace(" ", "_")
            buf = []
        elif name:
            t = el.get_text("\n" if name == "pre" else " ", strip=True)
            if t:
                buf.append(t)
    flush()
    return sections


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/corpus.jsonl")
    ap.add_argument("--per-domain", type=int, default=25)
    a = ap.parse_args()

    seen, n_sec, n_pages = set(), 0, 0
    with open(a.out, "w", encoding="utf-8") as f:
        for domain, cfg in DOMAINS.items():
            titles = list(cfg["seed"])
            for cat in cfg["categories"]:
                try:
                    titles += category_members(cat)
                except Exception as e:
                    print(f"  ! category {cat}: {e}")
            kept = 0
            for t in dict.fromkeys(titles):
                if kept >= a.per_domain or t in seen or t in EXCLUDE or t.replace("_", " ") in seen:
                    continue
                try:
                    secs = page_sections(t)
                except Exception as e:
                    print(f"  ! {t}: {e}")
                    continue
                if not secs or secs[0]["page"] in seen:  # empty or redirect to a page we already have
                    seen.add(t)
                    continue
                seen.add(t); seen.add(secs[0]["page"]); kept += 1
                for i, s in enumerate(secs):
                    s.update(id=f"{domain}:{s['page']}:{i}", domain=domain)
                    f.write(json.dumps(s, ensure_ascii=False) + "\n")
                    n_sec += 1
                n_pages += 1
                print(f"[{domain}] {kept:>2} {t} ({len(secs)} sections)")
    print(f"\nDone: {n_pages} pages, {n_sec} sections -> {a.out}")


if __name__ == "__main__":
    main()
