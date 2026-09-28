#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that runs the shell command "apt list --upgradable" using a custom runcmd helper from a "dh" module, then parses the output line by line to extract just the package names (stripping everything from the "/" character onward, and skipping lines containing "listing").
The resulting list of upgradable package names should be written, one per line, to the file "/sdcard/alu" if any are found, and each extracted package name should also be printed to the console using the cprint helper prefixed with "  - "."""

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
