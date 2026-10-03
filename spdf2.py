#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python CLI script that optimizes PDF files by running qpdf with linearization and object-stream generation to reduce file size.
It should accept file paths as command-line arguments, or if none are given, automatically discover all PDF files in the current directory; each file is processed by creating a temporary linearized copy, comparing its size to the original, replacing the original only if the new version is smaller, and printing before/after sizes and space saved (using helper functions fsz, get_files, gsz, mpf, and runcmd from a local dh module).
Multiple files should be processed concurrently using a multiprocessing/thread pool helper with a worker limit of 4, while a single file is processed directly, and the script should report total directory space freed at the end when processing multiple files."""

from __future__ import annotations

import sys
from pathlib import Path

from dh import fsz, get_files, gsz, mpf, runcmd

MAX_WORKERS = 4


def process_file(path: Path) -> None:
    path = Path(path)
    if not path.exists():
        print("Input file not found.", file=sys.stderr)
        sys.exit(1)
    temp_qpdf = path.with_name(f"temp_qpdf_{path.name}")
    before = path.stat().st_size
    print(f"{path.name} Before : {fsz(before)}")
    qpdf_cmd = [
        "qpdf",
        "--linearize",
        "--object-streams=generate",
        str(path),
        str(temp_qpdf),
    ]
    runcmd(qpdf_cmd, show_output=True)
    if temp_qpdf.exists():
        after = temp_qpdf.stat().st_size
        print(f"{path.name} After  : {fsz(after)}")
        diff = before - after
        sign = "-" if diff >= 0 else "+"
        if after < before:
            temp_qpdf.replace(path)
            print(f"Saved  : {sign}{fsz(abs(diff))}")
        else:
            print("original file is smaller")
            temp_qpdf.unlink(missing_ok=True)


def main() -> None:
    cwd = Path.cwd()
    before = gsz(cwd)
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".pdf"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(0)
    mpf(process_file, files)
    after = gsz(cwd)
    dsz = before - after
    if dsz:
        print(f"space freed: {fsz(dsz)}")


if __name__ == "__main__":
    raise SystemExit(main())
