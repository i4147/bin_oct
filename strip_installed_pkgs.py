#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that cleans a requirements.txt file by removing entries for packages that are already installed in the current environment or that belong to the standard library, using helper utilities `STDLIB` and `get_installed_pkgs` from a local `dh` module.
It should read the requirements file (defaulting to "requirements.txt" or a path given as a command-line argument), normalize package names by lowercasing and replacing hyphens with underscores, filter out matches against installed packages and stdlib modules, then write the remaining unique package names back to the same file in sorted order, one per line.
Finally, it should print how many packages were removed."""

import sys
from pathlib import Path
from dh import STDLIB, get_installed_pkgs


def read_requirements(filename) -> list[str]:
    req_file = Path(filename)
    with req_file.open(encoding="utf-8") as f:
        return [
            line.strip().replace("-", "_").lower()
            for line in f
            if line.strip() and not line.startswith("#")
        ]


def strip_installed_from_requirements(fname: str) -> None:
    installed = get_installed_pkgs()
    installed = [p.lower().replace("-", "_") for p in installed if p]
    lines = read_requirements(fname)
    new_lines = [line for line in lines if line not in installed]
    new_lines = [line for line in new_lines if line not in STDLIB]
    new_lines = sorted(set(new_lines))
    Path(fname).write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    removed = len(lines) - len(new_lines)
    print(f"Removed {removed} packages")


if __name__ == "__main__":
    fn = "requirements.txt"
    if len(sys.argv) > 1:
        fn = sys.argv[1]
    strip_installed_from_requirements(fn)
