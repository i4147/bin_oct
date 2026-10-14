#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory tree for files and finds pairs of files with highly similar content using fuzzy hashing. The tool should accept a root directory path, an optional minimum file size to skip tiny files, and a similarity threshold (0–100) that determines which pairs are reported. It should recursively collect candidate files, skip anything that is not a regular file or cannot be read, compute a fuzzy hash for each qualifying file, and then compare every unique pair of hashes to produce a similarity score. Only pairs meeting or exceeding the threshold should be reported, sorted from most to least similar.
The output should be a structured report, either as human-readable text or as JSON when requested, listing each matching pair with both file paths (shown relative to the scanned root when possible), the similarity score, and summary statistics such as the number of files scanned, files hashed, and matches found. Support an option to write the report to an output file, and handle errors gracefully so that a single unreadable file never stops the overall scan. Include a command-line interface with clear help text, sensible defaults, and proper exit codes for success, invalid arguments, and missing dependencies.
---"""

from __future__ import annotations
import argparse
import json
import operator
from pathlib import Path
import shutil
import sys
from dh import get_files
import ssdeep


def relative(path, base):
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def compute_hashes(files, min_size):
    hashes = []
    for path in files:
        p = Path(path)
        try:
            if not p.is_file():
                continue
            if p.stat().st_size < min_size:
                continue
            digest = ssdeep.hash_from_file(str(p))
        except Exception:
            continue
        if digest:
            hashes.append((p, digest))
    return hashes


def compare_hashes(hashes, threshold, base):
    results = []
    for i in range(len(hashes)):
        path_a, hash_a = hashes[i]
        for j in range(i + 1, len(hashes)):
            path_b, hash_b = hashes[j]
            try:
                score = ssdeep.compare(hash_a, hash_b)
            except Exception:
                continue
            if score >= threshold:
                results.append({
                    "file1": relative(path_a, base),
                    "file2": relative(path_b, base),
                    "score": score,
                })
    results.sort(key=operator.itemgetter("score"), reverse=True)
    return results


def group_files(results, base):
    for index, item in enumerate(results, 1):
        group = base / "group{:03d}".format(index)
        group.mkdir(parents=True, exist_ok=True)
        for key in ("file1", "file2"):
            source = base / item[key]
            if not source.exists():
                continue
            dest = group / source.name
            if dest.exists():
                dest = group / "{}_{}{}".format(source.stem, index, source.suffix)
            try:
                shutil.move(source, dest)
            except Exception:
                continue


def main(argv=None):
    parser = argparse.ArgumentParser(description="Find similar files using ssdeep.")
    parser.add_argument("path", nargs="?", default=".", help="directory to scan")
    parser.add_argument("-t", "--threshold", type=int, default=70)
    parser.add_argument("-m", "--min-size", type=int, default=1)
    parser.add_argument("-g", "--group-similar", action="store_true")
    parser.add_argument("-o", "--output", default="simz.json")
    args = parser.parse_args(argv)
    base = Path.cwd()
    files = get_files(args.path)
    hashes = compute_hashes(files, args.min_size)
    results = compare_hashes(hashes, args.threshold, base)
    if args.group_similar:
        group_files(results, base)
    text = json.dumps(results, indent=2)
    if args.output == "-":
        print(text)
    else:
        Path(args.output).write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
