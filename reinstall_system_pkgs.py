#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that reinstalls a list of APT packages on a Debian/Ubuntu system.
It should take a file path as a command-line argument, where the file contains one package name per line, and validate that the file exists before proceeding.
For each package, it should run "apt install --reinstall -y" via subprocess, printing progress with an index counter and a short delay between installs, while logging any package names that fail (non-zero exit code) to a reset file named "reinstall_failed.txt" in the user's home directory.
At the end, it should print a summary indicating completion and the location of the failure log."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <pkg_list_file>")
        sys.exit(1)
    pkg_file = Path(sys.argv[1]).expanduser()
    if not pkg_file.is_file():
        print(f"File not found: {pkg_file}")
        sys.exit(1)
    pkgs = [line.strip() for line in pkg_file.read_text().splitlines() if line.strip()]
    failed_file = Path.home() / "reinstall_failed.txt"
    failed_file.write_text("")
    print(f"Total packages to reinstall: {len(pkgs)}\n")
    for i, pkg in enumerate(pkgs, 1):
        print(f"[{i}/{len(pkgs)}] Reinstalling {pkg} ...", flush=True)
        r = subprocess.run(["apt", "install", "--reinstall", "-y", pkg])
        if r.returncode != 0:
            print(f"  !! Failed: {pkg} (exit {r.returncode})")
            with failed_file.open("a") as f:
                f.write(pkg + "\n")
        else:
            print("  ok")
        time.sleep(0.2)
    print(f"\nDone. Failures (if any) logged to {failed_file}")


if __name__ == "__main__":
    main()
