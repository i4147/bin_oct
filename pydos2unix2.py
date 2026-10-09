#!/data/data/com.termux/files/usr/bin/env python
"""Build a Python command-line utility that recursively scans a target directory and normalizes line endings in text files, converting Windows-style CRLF ("\r\n") to Unix-style LF ("\n") in place.
Requirements and behavior: 1.
**CLI interface** (via `argparse`): - A positional argument for the root directory to scan.
- An option to specify file glob patterns to include (e.g.
`*.py`, `*.txt`), supporting multiple patterns, with sensible defaults if none are given.
- An option to specify glob patterns or directory names to exclude (e.g.
`.git`, `node_modules`, `venv`), with sensible defaults.
- A `--dry-run` flag that reports which files would be converted without modifying anything.
- An option to control the number of parallel worker processes.
- A verbosity/logging option (e.g.
`-v`/`--verbose`) to control log detail via the `logging` module.
2.
**File discovery**: - Recursively walk the directory tree using `pathlib`.
- Match files against the include glob patterns using `fnmatch`.
- Skip files/directories matching the exclude patterns.
3.
**Binary file detection**: - Implement a function that reads a chunk (e.g.
first 4096 bytes) of a file and determines whether it is binary, by checking for null bytes and by computing the proportion of non-printable/non-text bytes (treating bytes 32–126 plus `\n`, `\r`, `\t`, `\b` as "text" characters).
If the non-text ratio exceeds a threshold (e.g.
30%), or any null byte is found, the file is classified as binary and skipped.
- Handle read errors gracefully by treating unreadable files as binary (so they get skipped).
4.
**Detection of files needing conversion**: - Implement a function using `mmap` to efficiently check whether a file contains any `\r\n` sequences, to avoid unnecessary rewrites of files that are already LF-only.
5.
**Conversion logic**: - Implement an in-place conversion function that uses `mmap` to read the file's bytes, replace all `\r\n` with `\n`, and write the result back into the same file, truncating it to the new (shorter) length.
If no replacement was needed, it should do nothing.
- Implement a fallback conversion function that uses a temporary file (same path with a `.tmp` suffix added) and UTF-8 text mode (decoding with errors ignored) to rewrite the file line-by-line with `\r\n` replaced by `\n`, then atomically replaces the original file with `os.replace`.
This fallback should be used when the in-place `mmap` approach fails (e.g.
due to encoding or OS-level issues).
- Implement a top-level "safe convert" function per file that: - Skips the file if it doesn't exist or isn't a regular file (returns a status like `SKIP_NOT_FOUND` or similar).
- Skips binary files.
- Skips files that don't need conversion.
- In dry-run mode, reports that the file would be converted without changing it.
- Otherwise attempts the in-place mmap conversion, falling back to the temp-file method on failure.
- Returns a status string per file describing the outcome (e.g.
converted, skipped-binary, skipped-no-change, dry-run, error, not-found), suitable for aggregation and logging.
6.
**Parallel processing**: - Use `multiprocessing.Pool` to process discovered files concurrently, with the worker count controlled by the CLI option.
- Use `tqdm` to display a progress bar while files are being processed.
7.
**Output/summary**: - Collect and log/print a summary at the end: counts of files converted, skipped (binary, no-change, not-found), errors, and (if dry-run) how many would be converted.
- Use the `logging` module throughout for status messages, with verbosity controlled by the CLI flag, and exit with a non-zero status code if errors occurred.
The script should be robust against unreadable or unusual files (permission errors, non-UTF-8 content, etc.), never crash on a single bad file, and clearly report per-file and aggregate results.
It should run as a standalone script (`if __name__ == "__main__":` entry point) invoked from the command line.
--- LiveDoc: https://felo.ai/zh-Hans/livedoc/k8jr7RBDD6NGPywohFwjnE"""

from __future__ import annotations
import argparse
import fnmatch
import logging
import mmap
from multiprocessing import Pool
import os
from pathlib import Path
import sys

from tqdm import tqdm


def is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(4096)
        if b"\x00" in chunk:
            return True
        text_chars = bytearray(range(32, 127)) + b"\n\r\t\b"
        nontext = sum(1 for b in chunk if b not in text_chars)
        return nontext / max(len(chunk), 1) > 0.30
    except Exception:
        return True


def needs_conversion(path: Path) -> bool:
    try:
        with (
            path.open("rb") as f,
            mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm,
        ):
            return mm.find(b"\r\n") != -1
    except Exception:
        return False


def convert_in_place(path: Path) -> None:
    with path.open("r+b") as f, mmap.mmap(f.fileno(), 0) as mm:
        data = mm[:]
        new = data.replace(b"\r\n", b"\n")
        if new == data:
            return
        mm.seek(0)
        mm.write(new)
        mm.flush()
        f.truncate(len(new))


def convert_with_temp(path: Path) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with (
        path.open("r", encoding="utf-8", errors="ignore", newline="") as src,
        tmp.open("w", encoding="utf-8", newline="") as dst,
    ):
        for line in src:
            dst.write(line.replace("\r\n", "\n"))
    os.replace(tmp, path)


def safe_convert(path: Path, dry_run: bool = False) -> str:
    if not path.is_file():
        return "SKIP_NOT_FILE"
    if is_binary(path):
        return "SKIP_BINARY"
    if not needs_conversion(path):
        return "SKIP_ALREADY_UNIX"
    if dry_run:
        return "DRY_RUN"
    try:
        convert_in_place(path)
        return "CONVERTED_MMAP"
    except Exception:
        try:
            convert_with_temp(path)
            return "CONVERTED_TEMP"
        except Exception:
            return "ERROR"


def scan_paths(inputs, recursive: bool, excludes) -> list[Path]:
    result = []
    for inp in inputs:
        p = Path(inp)
        if p.is_dir():
            if recursive:
                result.extend(p.rglob("*"))
            else:
                result.extend(p.glob("*"))
        else:
            result.append(p)
    out = []
    for p in result:
        if any(fnmatch.fnmatch(str(p), pat) for pat in excludes):
            continue
        out.append(p)
    return out


def worker(args):
    path, dry = args
    res = safe_convert(path, dry_run=dry)
    if res == "ERROR":
        logging.error(f"Failed to convert: {path}")
    return res


def parse_args():
    parser = argparse.ArgumentParser(description="Fast dos2unix converter with mmap, tqdm, error logging.")
    parser.add_argument("paths", nargs="*", help="Files or directories.")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--chunksize", type=int, default=50)
    parser.add_argument("--exclude", nargs="*", default=[])
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.paths:
        args.paths = ["."]
        args.recursive = True
    log_dir = Path.home() / "tmp"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "pydos2unix.log"
    logging.basicConfig(
        filename=str(log_file),
        level=logging.ERROR,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    files = scan_paths(args.paths, args.recursive, args.exclude)
    tasks = [(p, args.dry_run) for p in files]
    if args.parallel > 1:
        with Pool(args.parallel) as pool, tqdm(total=len(tasks), unit="file") as bar:
            for _ in pool.imap_unordered(worker, tasks, chunksize=args.chunksize):
                bar.update(1)
    else:
        for task in tqdm(tasks, unit="file"):
            worker(task)


if __name__ == "__main__":
    main()
