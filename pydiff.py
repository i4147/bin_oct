#!/data/data/com.termux/files/usr/bin/env python
"""Create a Python command Android, using the shebang `/data/data/com.termux/files/usr/bin/python3.12`) that compares two text files line-by-line and reports the differences between them.

**Purpose:**
The script takes two file paths as input and determines which lines are unique to each file (i.e., lines present in file1 but not file2, and vice versa). It is intended for quickly diffing large line-based files (e.g., lists, logs, dictionaries) with attention to performance and optional file management actions.

**Main behavior:**
1. **Fast equality check first:** Before doing any line-level comparison, compute the SHA-256 hash of both files (reading in 1MB chunks for memory efficiency). If the hashes match, the files are identical, so the script can skip the diff entirely and report that the files are the same.
2. **Parallel file reading:** If the files differ, read both files concurrently using a `ProcessPoolExecutor` (configurable number of workers, default 2) to speed up I/O-bound loading, using a shared helper `read_lines` from a local `dh` module.
3. **Optional line stripping:** Support a `strip` option that trims whitespace from each line before comparison.
4. **Line count reporting:** Report the number of lines in each file (counted by counting newline bytes, accounting for files without a trailing newline).
5. **Diff computation:** Compute the set difference in both directions — lines only in file1, and lines only in file2 — supporting chunked/batched filtering logic (`filter_diff_chunk` with modes `only_in_first` and its complement) so the comparison can potentially be parallelized or processed in pieces.
6. **Optional file organization:** Support a `move` option that, when enabled, creates a new sequential directory named `group_1`, `group_2`, etc. (auto-incrementing to avoid collisions) in the current working directory, and moves both compared files into that new group directory — useful for archiving/organizing files after comparison.
7. **Colored console output:** Use a `cprint` helper (from the local `dh` module) to print status/result messages in color (e.g., magenta for the "moved to group_X/" message), making CLI output more readable.

**Inputs:**
- Two file paths (positional arguments) to compare.
- Optional flags: whether to strip whitespace from lines, whether to move the files into a new group folder after comparison, and the number of parallel worker processes to use for reading.

**Outputs:**
- Console-printed report showing line counts for each file, whether the files are identical, and/or the lines that differ between the two files.
- Side effect: if the move option is enabled and files differ, both files are relocated into a newly created `group_N` directory.

**Implementation notes:**
- Use `argparse` for CLI argument parsing.
- Use `pathlib.Path` for all filesystem path handling.
- Use `hashlib` (SHA-256) for the fast identity check.
- Use `shutil.move` for relocating files.
- Use `concurrent.futures.ProcessPoolExecutor` and `as_completed` for concurrent file reading.
- Depend on a local module `dh` providing `cprint` (colored print) and `read_lines` (line-reading utility with a `ke` keyword argument controlling line-ending handling).
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/iPPRGahoGTvBu6WzKw6tXJ"""

from __future__ import annotations
import argparse
import hashlib
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from dh import cprint, read_lines


def count_lines(path: Path) -> int:
    return path.read_bytes().count(b"\n") + 1


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_file_task(path: Path, use_mmap: bool, strip: bool) -> tuple[Path, list[str]]:
    lines = read_lines(path, ke=False)
    if strip:
        lines = [line.strip() for line in lines]
    return path, lines


def filter_diff_chunk(chunk: list[str], exclude_set: frozenset[str], mode: str) -> list[str]:
    if mode == "only_in_first":
        return [p for p in chunk if p not in exclude_set]
    else:
        return [p for p in chunk if p in exclude_set]


def next_group_dir(base: Path) -> Path:
    n = 1
    while (base / f"group_{n}").exists():
        n += 1
    return base / f"group_{n}"


def move_files_to_group(path1: Path, path2: Path) -> None:
    base = Path.cwd()
    target = next_group_dir(base)
    target.mkdir()
    shutil.move(str(path1.resolve()), str(target / path1.name))
    shutil.move(str(path2.resolve()), str(target / path2.name))
    cprint(f"moved to {target.name}/", "magenta")


def report_diff_lines(
    path1: Path,
    path2: Path,
    strip: bool = False,
    move: bool = False,
    num_workers: int = 2,
) -> None:
    if file_hash(path1) == file_hash(path2) and not strip:
        cprint(f"{path1.name} and {path2.name} are identical", "blue")
        if move:
            move_files_to_group(path1, path2)
        return
    lines1_count = count_lines(path1)
    lines2_count = count_lines(path2)
    use_mmap1 = lines1_count > 5000
    use_mmap2 = lines2_count > 5000
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future1 = executor.submit(read_file_task, path1, use_mmap1, strip)
        future2 = executor.submit(read_file_task, path2, use_mmap2, strip)
        _, lines1 = future1.result()
        _, lines2 = future2.result()
    set1 = set(lines1)
    set2 = set(lines2)
    if lines1_count > 10000 and lines2_count > 10000:
        chunk_size = max(1000, len(lines1) // num_workers)
        chunks = [lines1[i : i + chunk_size] for i in range(0, len(lines1), chunk_size)]
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(filter_diff_chunk, chunk, frozenset(set2), "only_in_first") for chunk in chunks]
            only_in_first = []
            for future in as_completed(futures):
                only_in_first.extend(future.result())
    else:
        only_in_first = [p for p in lines1 if p not in set2]
    only_in_second = [p for p in lines2 if p not in set1]
    common_count = len(set1 & set2)
    if move and strip and not only_in_first and not only_in_second:
        move_files_to_group(path1, path2)
    if only_in_first:
        cprint(f"only in {path1.name}:", "cyan")
        for line in only_in_first[:5]:
            cprint(f"  - {line}", "green")
        if len(only_in_first) > 5:
            cprint(f"  ... and {len(only_in_first) - 5} lines more", "green")
    if only_in_second:
        cprint(f"only in {path2.name}:", "cyan")
        for line in only_in_second[:5]:
            cprint(f"  - {line}", "yellow")
        if len(only_in_second) > 5:
            cprint(f"  ... and {len(only_in_second) - 5} lines more", "yellow")
    cprint(
        f"common lines: {common_count}\n"
        f"only in {path1.name}: {len(only_in_first)}\n"
        f"only in {path2.name}: {len(only_in_second)}",
        "blue",
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="pydiff", description="Diff two files line by line")
    parser.add_argument("file1", type=Path)
    parser.add_argument("file2", type=Path)
    parser.add_argument(
        "-s",
        "--strip",
        action="store_true",
        help="strip leading and trailing whitespace from lines before comparing",
    )
    parser.add_argument(
        "-m",
        "--move",
        action="store_true",
        help="with -s, if files match, move both into a group_N subdir in the current folder",
    )
    parser.add_argument("-w", "--workers", type=int, default=2, help="number of worker processes")
    args = parser.parse_args()
    report_diff_lines(
        args.file1,
        args.file2,
        strip=args.strip,
        move=args.move,
        num_workers=args.workers,
    )


if __name__ == "__main__":
    main()
