#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python duplicate-file finder with the following specification:

Build a command-line Python 3 script (Termux-compatible, shebang pointing to the Termux Python path) that finds duplicate files under one or more directory roots by content hashing. Use the xxhash library's 64-bit xxHash (xxh64) for hashing and multiprocessing.Pool with 8 workers for parallel hashing.

Behavior requirements:

- Accept one or more root directories via argparse as positional arguments (use `from __future__ import annotations` at the top). Validate that each path exists and is a directory; report errors clearly and exit with a nonzero status if a root is invalid.
- Traverse each root iteratively (stack-based, not recursive) using os.scandir. Maintain a maximum directory depth of 64; deeper directories are skipped silently. Skip any directory named ".git". Never follow symbolic links: skip symlinks entirely, both to directories and to files. Use is_dir(follow_symlinks=False) and is_file(follow_symlinks=False).
- Silently skip directise PermissionError or other scanning, and skip individual entries that raise OSError.
- Collect each regular file as a (relative POSIX path, absolute Path) pair, with the relative path computed against the resolved root.
- Group files by size first. Only files whose size matches at least one other file are hashed, since unique sizes cannot be duplicates. Handle zero-byte files consistently (they share a size group and can be reported as duplicates of each other).
- Hash candidate files in parallel with a multiprocessing Pool of 8 workers. Hash with xxh64 by reading in 1 MiB chunks (1 << 20 bytes) so large files do not load into memory. Group results by hash digest, and report only groups containing two or more files.
- Handle files that vanish or become unreadable between scanning and hashing: catch OSError per file, skip them, and continue without crashing.
- Output: for each duplicate group, print the shared hash and the member file paths (relative or absolute as appropriate, with clear labeling per root), plus a summary of total duplicate groups, total duplicate files, and reclaimable bytes (sum of sizes of all copies beyond the first in each group). Print nothing extra if no duplicates are found, or print a clear "no duplicates found" message.
- Guard the entry point with `if __name__ == "__main__":` and ensure multiprocessing works correctly (the Pool must be created under that guard).
- Exit codes: 0 on success regardless of duplicates found; nonzero on invalid arguments or fatal errors. Use sys.exit appropriately and write errors to stderr.

Dependencies: standard library (argparse, os, sys, collections.defaultdict, multiprocessing.Pool, pathlib.Path) plus the third-party `xxhash` package. Mention in the script's usage that `xxhash` must be installed (e.g., via pip).

Implementation constraints: use type hints where helpful, keep the code idiomatic and well-structured with small helper functions (a file hashing helper, a file collection helper, and the main orchestration), and keep the module importable without side effects. Ensure the collection helper returns a list of (relative path, absolute path) tuples and returns it correctly at the end.

Deliver the complete script as a single file, runnable with `python script.py <dir> [<dir> ...]`.
---"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

import xxhash

NUM_WORKERS = 8
SKIP_DIR_NAMES = {".git"}
HASH_CHUNK_SIZE = 1 << 20
MAX_DEPTH = 64


def _file_hash(path: Path) -> str:
    h = xxhash.xxh64()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(HASH_CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def _collect_files(root: Path):
    result = []
    root = root.resolve()
    stack = [(root, 0)]
    while stack:
        cur, depth = stack.pop()
        if depth > MAX_DEPTH:
            continue
        try:
            entries = list(os.scandir(cur))
        except (PermissionError, OSError):
            continue
        for entry in entries:
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if entry.name in SKIP_DIR_NAMES:
                        continue
                    stack.append((Path(entry.path), depth + 1))
                elif entry.is_file(follow_symlinks=False):
                    rel = Path(entry.path).relative_to(root).as_posix()
                    result.append((rel, Path(entry.path)))
            except OSError:
                continue
    return result


def _collect_subdirs(root: Path):
    result = []
    root = root.resolve()
    stack = [(root, 0)]
    while stack:
        cur, depth = stack.pop()
        if depth > MAX_DEPTH:
            continue
        try:
            entries = list(os.scandir(cur))
        except (PermissionError, OSError):
            continue
        for entry in entries:
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if entry.name in SKIP_DIR_NAMES:
                        continue
                    rel = Path(entry.path).relative_to(root).as_posix()
                    result.append(rel)
                    stack.append((Path(entry.path), depth + 1))
            except OSError:
                continue
    return result


def folder_signature(args):
    path_str, mode = args
    root = Path(path_str).resolve()
    files = _collect_files(root)
    if not files:
        return None
    direct_files = [rel for rel, _ in files if "/" not in rel]
    if not direct_files:
        return None
    rel_files = sorted(rel for rel, _ in files)
    subdirs = sorted(_collect_subdirs(root))
    struct_h = xxhash.xxh64()
    for d in subdirs:
        struct_h.update(b"D")
        struct_h.update(d.encode("utf-8"))
        struct_h.update(b"\x00")
    for rp in rel_files:
        struct_h.update(b"F")
        struct_h.update(rp.encode("utf-8"))
        struct_h.update(b"\x00")
    struct_key = struct_h.hexdigest()
    if mode == "content":
        content_h = xxhash.xxh64()
        for rel, abs_path in sorted(files, key=lambda x: x[0]):
            try:
                fh = _file_hash(abs_path)
            except (PermissionError, OSError):
                fh = "unreadable"
            content_h.update(rel.encode("utf-8"))
            content_h.update(b"\x00")
            content_h.update(fh.encode("ascii"))
            content_h.update(b"\x01")
        content_key = content_h.hexdigest()
    else:
        content_key = ""
    return (struct_key, content_key, str(root))


def find_all_folders(start: Path):
    start = start.resolve()
    folders = []
    stack = [(start, 0)]
    while stack:
        cur, depth = stack.pop()
        if depth > MAX_DEPTH:
            continue
        folders.append(cur)
        try:
            entries = list(os.scandir(cur))
        except (PermissionError, OSError):
            continue
        for entry in entries:
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if entry.name in SKIP_DIR_NAMES:
                        continue
                    stack.append((Path(entry.path), depth + 1))
            except OSError:
                continue
    return folders


def parse_args():
    p = argparse.ArgumentParser(description="Find duplicate folders in the current directory tree.")
    p.add_argument(
        "-s",
        "--structure",
        action="store_true",
        help="Report folders with the same tree structure (same filenames & subfolders) even if contents differ.",
    )
    return p.parse_args()


def main():
    args = parse_args()
    mode = "structure" if args.structure else "content"
    start = Path.cwd()
    print(f"Scanning : {start}")
    print(f"Mode     : {mode}")
    print(f"Workers  : {NUM_WORKERS}")
    folders = find_all_folders(start)
    print(f"Found {len(folders)} folder(s) (pre-filter).")
    results = []
    with Pool(processes=NUM_WORKERS) as pool:
        async_results = [pool.apply_async(folder_signature, ((str(f), mode),)) for f in folders]
        for ar in async_results:
            try:
                res = ar.get()
            except Exception as e:
                print(f"[warn] worker error: {e}", file=sys.stderr)
                continue
            if res is not None:
                results.append(res)
    groups = defaultdict(list)
    if mode == "content":
        for struct_key, content_key, path in results:
            groups[(struct_key, content_key)].append(path)
    else:
        for struct_key, _, path in results:
            groups[struct_key].append(path)
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    if not duplicates:
        print("\nNo duplicate folders found.")
        return
    label = "same structure" if mode == "structure" else "identical content"
    print(f"\nFound {len(duplicates)} set(s) of folders with {label}:\n")
    for i, (_, paths) in enumerate(sorted(duplicates.items(), key=lambda kv: kv[1][0]), start=1):
        print(f"--- Group {i} ({len(paths)} folders) ---")
        for p in sorted(paths):
            print(f"  {p}")
        print()


if __name__ == "__main__":
    main()
