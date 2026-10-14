#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that batch-optimizes PDF files in the current working directory by reducing their file size using a PDF restructuring tool. The script should discover all PDF files in the folder it is run from, process them concurrently with a small, fixed limit on parallel workers, and for each file report the size before and after optimization in human-readable units. It should only replace an original file when the optimized version is actually smaller; otherwise it should keep the original untouched, clean up any temporary output, and report that the original was already smaller. For each processed file, the script should print the net savings (or indicate an increase), and at the end provide a summary of the total space saved across all files. If an input file is missing or an external tool fails, the script should report a clear error message to the standard error stream and handle the failure gracefully without corrupting the original files. The optimization should produce a linearized, web-optimized PDF with compressed object streams. The script should be self-contained, use only the standard library plus any helper utilities it needs to be written from scratch, and print concise, user-friendly progress output throughout.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import fsz, get_files, gsz, mpf, runcmd

MAX_WORKERS = 4


def process_file(path):
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


def main():
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
