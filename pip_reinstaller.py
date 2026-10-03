#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that reads a list of package names (one per line) from a file path giveninstalls each package via pip using the current Python interpreter with flags like --force-reinstall, --no-input, --disable-pip-version-check, and --root-user-action=ignore, setting a default CFLAGS=-O2 environment variable for the subprocess calls.
It should validate that the input file exists, print progress for each package (index, total count, and success/failure status), pause briefly between installs, and record any packages that failed to reinstall into a "reinstall_pip_failed.txt" file in the user's home directory, printing a final summary message pointing to that log file."""

from __future__ import annotations

import os
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
    pkgs = [l.strip() for l in pkg_file.read_text().splitlines() if l.strip()]
    failed_file = Path.home() / "reinstall_pip_failed.txt"
    failed_file.write_text("")
    py = sys.executable
    print(f"Total packages to reinstall: {len(pkgs)}")
    print(f"Interpreter: {py}\n")
    env = os.environ.copy()
    env.setdefault("CFLAGS", "-O2")
    for i, pkg in enumerate(pkgs, 1):
        print(f"[{i}/{len(pkgs)}] Reinstalling {pkg} ...", flush=True)
        r = subprocess.run(
            [
                py,
                "-m",
                "pip",
                "install",
                "--force-reinstall",
                "--no-input",
                "--disable-pip-version-check",
                "--root-user-action=ignore",
                pkg,
            ],
            env=env,
        )
        if r.returncode != 0:
            print(f"  !! Failed: {pkg} (exit {r.returncode})")
            with failed_file.open("a") as f:
                f.write(pkg + "\n")
        else:
            print("  ok")
        time.sleep(0.2)
    print(f"\nDone. Failures logged to {failed_file}")


if __name__ == "__main__":
    main()
