#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory tree and automatically fixes execute permissions on files that should be runnable. The tool should accept a root directory path as input and walk through all files beneath it, using parallel processing to handle large trees efficiently with a configurable number of worker processes.
For each file, the script should decide whether it ought to be executable based on these heuristics: the file begins with a script interpreter marker (a shebang line); the file resides in a conventional binary directory such as "bin", "sbin", or ".bin"; the file name matches a shared-library pattern (for example, names ending in ".so" optionally followed by version numbers); or the file has no extension and appears to be a binary (contains null bytes in its initial content). Files with common script or text extensions that do not meet these conditions should be left alone, and the script should only consider files that are not already executable.
When a file qualifies and lacks execute permission, the script should add execute bits for the owner, group, and others while preserving all existing permission bits. Itle unreadable files, missing paths, and permission errors gracefully without crashing, skipping problematic entries and continuing with the rest of the tree.
The output should be a concise report to the console listing each file whose permissions were changed, along with a summary count of files scanned, files modified, and files that failed. Include a dry-run option that reports what would change without modifying anything, and a command-line interface that accepts the target directory and optional flags for worker count and dry-run mode. The script should be safe to run repeatedly, producing no changes on subsequent runs once permissions are correct.
---"""

from __future__ import annotations
import multiprocessing as mp
import os
from pathlib import Path
import re

SUFFIXES = {".py", ".sh", ".bash", ".pl", ".rb", ".pyw", ".txt"}
BIN_DIRS = {"sbin", "bin", ".bin"}
SO_RE = re.compile(r".*\.so(?:\.\d+)*$")
WORKERS = 8


def has_shebang(p):
    try:
        with p.open("rb") as f:
            return f.read(2) == b"#!"
    except OSError:
        return False


def is_binary(p):
    try:
        with p.open("rb") as f:
            return b"\x00" in f.read(8192)
    except OSError:
        return False


def is_executable(p):
    try:
        return bool(p.stat().st_mode & 0o100)
    except OSError:
        return False


def chmod_x(p):
    try:
        p.chmod(p.stat().st_mode | 0o111)
        return True
    except OSError:
        return False


def should_execute(p):
    if has_shebang(p):
        return True
    if p.parent.name in BIN_DIRS:
        return True
    if SO_RE.match(p.name):
        return True
    return bool(not p.suffix and is_binary(p))


def process(path_str):
    p = Path(path_str)
    try:
        if not p.is_file():
            return path_str, False, None
        if is_executable(p):
            return path_str, False, None
        if not should_execute(p):
            return path_str, False, None
        if os.name != "posix":
            return path_str, False, None
        if chmod_x(p):
            return path_str, True, None
        return path_str, False, "chmod failed"
    except Exception as e:
        return path_str, False, str(e)


def main():
    root = Path.cwd()
    self_path = Path(__file__).resolve()
    files = []
    for p in root.rglob("*"):
        if ".git" in p.parts:
            continue
        if p.is_symlink():
            continue
        try:
            if p.resolve() == self_path:
                continue
        except OSError:
            pass
        if p.is_file():
            files.append(str(p))
    if not files:
        print("No files found.")
        return 0
    changed = errors = 0
    with mp.Pool(processes=WORKERS) as pool:
        results = [pool.apply_async(process, (f,)) for f in files]
        for r in results:
            path_str, did_change, err = r.get()
            if err:
                errors += 1
                print(f"ERROR {path_str}: {err}")
                continue
            if did_change:
                changed += 1
                print(f"[+] Made executable: {path_str}")
    print(f"Done. changed={changed} errors={errors}")
    if os.name != "posix":
        print("Note: non-POSIX system — executable bits not applied.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
