#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that minifies CSS files using the external "cleancss" tool with duplicate-rule removal enabled.
It should accept file paths as arguments, or if none are given, recursively find all ".css" and ".min.css" files in the current directory, skipping files that don't exist or contain only a single line.
For each file it should run cleancss in place, print the filename plus a colored status ("NO CHANGE", "OK" with size reduction and percentage, or "ERROR"), process files in parallel, and finally report the total disk space freed."""

from __future__ import annotations
import sys
from pathlib import Path
from dh import cprint, fsz, get_files, gsz, mpf, runcmd


def process_file(path) -> bool:
    path = Path(path)
    before = gsz(path)
    if not path.exists():
        return False
    if len(path.read_text().splitlines()) == 1:
        return False
    print(f"{path.name}", end=" ")
    cmd = [
        "cleancss",
        "-O2",
        "all:off;removeDuplicateRules:on",
        str(path),
        "-o",
        str(path),
    ]
    res, _, _err = runcmd(cmd, show_output=True)
    if not res:
        after = gsz(path)
        diffsize = before - after
        if not diffsize:
            cprint("[NO CHANGE]", "white")
        if diffsize:
            ratio = after / before * 40
            cprint(f"[OK] - {fsz(diffsize)} {abs(ratio):.1f}%", "cyan")
        return True
    cprint("[ERROR]", "red")
    return False


def main() -> None:
    args = sys.argv[1:]
    cwd = Path.cwd()
    before = gsz(cwd)
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".css", ".min.css"])
    _ = mpf(process_file, files)
    diff_size = before - gsz(cwd)
    cprint(f"space freed : {fsz(diff_size)}", "green")


if __name__ == "__main__":
    raise SystemExit(main())
