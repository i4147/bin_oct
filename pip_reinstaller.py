#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a text file containing a list of package names (one per line, ignoring blank lines), then force-reinstalls each package into the currently running Python interpreter using pip, in the order listed.
The script should accept the path to the package list file as a single command-line argument, expand user home shortcuts in that path, and exit with a usage message or a clear "file not found" message if the argument is missing or the file does not exist.
Before starting, it should report the total number of packages and which Python interpreter is being used. During processing, it should print progress in the form "[current/total] Reinstalling <package> ..." so the user can follow along in real time, with output flushed immediately.
Each installation should run non-interactively: suppress prompts, skip pip's version-check notice, and allow running as root without warnings. Pass the environment through to pip, while ensuring a default compiler flag of "-O2" is set only if the user has not already defined one.
Any package whose installation fails (non-zero exit status) should be recorded by name in a report file placed in the user's home directory, named reinstall_pip_failed.txt. The report file should be created or cleared at the start of each run so it reflects only the current run. The script should continue with the remaining packages after a failure rather than aborting.
At the end, the script should print a summary showing how many packages succeeded and how many failed, and point the user to the failure report. It should also record and display the total elapsed time for the run. The script should exit with a nonzero status if any installations failed, and zero otherwise.
---"""

from __future__ import annotations
import os
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
