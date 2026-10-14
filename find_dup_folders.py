#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that computes a content-based fingerprint for every folder in a set of user-specified directory trees and reports which folders have duplicate contents. The script should accept one or more root directories as input, walk through them to identify candidate folders, and produce a fingerprint for each folder based on the relative paths and full byte contents of the regular files it contains, ignoring symbolic links and skipping any folder that has no files. Read file data in fixed-size chunks so that very large files can be processed efficiently, and handle unreadable files gracefully without aborting the whole run.
The script should avoid comparing a folder against itself or against folders that are nested inside one another, since such comparisons would produce misleading results. Folders whose fingerprints match should be grouped together as duplicates, and the output should list each group of identical folders with their paths, clearly separated from one another. Where practical, persist the computed fingerprints to a cache file keyed by folder path and a modification signature so that repeated runs skip unchanged folders, and provide a way to ignore or refresh that cache.
The tool should print a concise, human-readable summary to the console and optionally write a machine-readable JSON report containing the duplicate groups, the fingerprint values, and basic statistics such as the number of folders scanned, files hashed, and total bytes processed. Include clear error messages for invalid or missing input paths, and make the behavior deterministic so that identical inputs always produce identical reports.
---"""

from __future__ import annotations
from collections import defaultdict
import json
from pathlib import Path
from dh import get_dirs
from xxhash import xxh64

CHUNK_SIZE = 1024 * 1024


def is_nested(path1: Path, path2: Path) -> bool:
    try:
        path1.resolve().relative_to(path2.resolve())
        return True
    except ValueError:
        pass
    try:
        path2.resolve().relative_to(path1.resolve())
        return True
    except ValueError:
        pass
    return False


def hash_folder(folder_path: Path) -> str:
    hasher = xxh64()
    files = []
    for path in folder_path.rglob("*"):
        if path.is_symlink():
            continue
        if path.is_file():
            files.append(path)
    if not files:
        return ""
    for file in sorted(files):
        rel = file.relative_to(folder_path)
        hasher.update(str(rel).encode("utf-8"))
        try:
            with file.open("rb") as f:
                while chunk := f.read(CHUNK_SIZE):
                    hasher.update(chunk)
        except OSError:
            continue
    return hasher.hexdigest()


def find_duplicate_folders(cwd: Path):
    folder_hashes = defaultdict(list)
    for path in get_dirs(cwd):
        if ".git" in path.parts:
            continue
        folder_hash = hash_folder(path)
        if folder_hash:
            folder_hashes.setdefault(folder_hash, []).append(path)
    return {h: paths for h, paths in folder_hashes.items() if len(paths) > 1}


if __name__ == "__main__":
    cwd = Path.cwd()
    duplicates = find_duplicate_folders(cwd)
    if duplicates:
        print("Duplicate folder groups:")
        for h, paths in duplicates.items():
            print(f"\nGroup (Hash: {h}):")
            for path in paths:
                print(f"  - {path}")
        cleaned = defaultdict(list)
        for h, paths in duplicates.items():
            for i in range(len(paths)):
                for j in range(i + 1, len(paths)):
                    p1 = Path(paths[i])
                    p2 = Path(paths[j])
                    if not is_nested(p1, p2):
                        cleaned[h].append(str(p1))
        with Path("/sdcard/dupdirs.json").open("w", encoding="utf-8") as fo:
            json.dump(cleaned, fo)
    else:
        print("No duplicate folders found.")
