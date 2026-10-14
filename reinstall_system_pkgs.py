#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a text file containing a list of system package names (one per line, ignoring blank lines) passed as a command-line argument, and reinstalls each package in sequence using the system's package manager in forced-reinstall, non-interactive mode. The script should accept a path that may use a home-directory shorthand, and it must exit with a usage message if no argument is given and with a clear error if the file does not exist.
Before processing, the script should report how many packages will be handled. While processing, it should show live progress in the form of a running counter (current index out of total) and the package name being reinstalled, flushing output so progress appears immediately. After each package, it should report success or failure along with the exit status of the operation.
Failures must not stop the run: every package should be attempted. Any package that fails should be recorded in a report file written to the user's home directory, which is cleared at the start of each run so it reflects only the current execution. At the end, the script should print a concise summary showing how many packages were processed and how many failed, and point the user to the failure report location.
Include a short, deliberate pause between consecutive package operations to avoid overwhelming the system or the package manager. The script should be robust, readable, and suitable for running from a terminal with appropriate exit codes (non-zero when the input is invalid, and a meaningful status reflecting whether any reinstallation failed).
---"""

from __future__ import annotations
from pathlib import Path
import subprocess
import sys
import time


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
