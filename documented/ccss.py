#!/data/data/com.termux/files/usr/bin/env python
"""ccss.py -- minify CSS files in place with ``cleancss``.

Empty files and files that hold a single line are skipped.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dh import cprint, fsz, get_files, gsz, mpf, runcmd


def process_file(path) -> bool:
    """Minify one CSS file with cleancss level 2 optimisations.

    Return ``True`` when the output file exists afterwards.
    """
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
    """Minify every CSS file in the working directory and report the space saved."""
    args = sys.argv[1:]
    cwd = Path.cwd()
    before = gsz(cwd)
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".css", ".min.css"])
    _ = mpf(process_file, files)
    diff_size = before - gsz(cwd)
    cprint(f"space freed : {fsz(diff_size)}", "green")


if __name__ == "__main__":
    raise SystemExit(main())
