#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that checks the system's package manager for upgradable packages on a Debian/Ubuntu-based system, extracts the bare package names from that listing, saves them to a plain-text file on the device's shared storage (one package name per line, UTF-8 encoded), and prints each package name as a bulleted item to the console. The script should run the upgradable-package query silently, skip the header line that the package manager prints, handle any blank or unexpected lines gracefully, write the file only when at least one upgradable package is found, and report the results in a clear, readable format. It should be designed to run as a standalone command-line utility, with the output file location and the package query command kept easy to adjust.
---"""

from __future__ import annotations
from pathlib import Path
from dh import cprint, runcmd

if __name__ == "__main__":
    cmd = ["apt", "list", "--upgradable"]
    _, txt, _ = runcmd(cmd, show_output=False)
    nl = []
    target_char = "/"
    for line in txt.splitlines():
        stripped = line.strip()
        if stripped and target_char in stripped:
            indx = stripped.index(target_char)
            cleaned = stripped[:indx]
            nl.append(cleaned)
        elif stripped and "listing" not in stripped.lower():
            nl.append(stripped)
    file_name = Path("/sdcard/alu")
    if nl:
        file_name.write_text("\n".join(nl), encoding="utf-8")
        for k in nl:
            cprint(f"  - {k}")
