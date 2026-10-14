#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that compares two directory trees of files and organizes duplicate and differing files into newly created group folders. The tool should accept two directory paths as inputs (for example via command-line arguments) and walk through the files in both trees to determine which files are identical by content, which exist only in the first directory, and which exist only in the second.
Key behaviors:
- Identify identical files efficiently by comparing content fingerprints rather than reading entire files into memory, handling large files gracefully.
- Support processing many files in parallel to speed up comparisons on large directory trees.
- Detect files that share the same relative path but differ in content, and files that appear in only one of the two trees.
- Optionally normalize text files (such as stripping surrounding whitespace on each line) before comparing their line contents, and report line counts for text files.
- For each category of result, move the relevant files into automatically numbered group folders created under a specified output or base location, never overwriting existing groups; the next available group number should be chosen automatically.
- Preserve the original relative structure or clearly record where each moved file came from so the operation is traceable.
- Provide a clear summary printed to the console showing how many files were identical, unique to each side, or differing, and the location of the created groups.
- Include a dry-run mode that reports the planned moves without modifying the file system.
- Handle missing paths, permission errors, and unreadable files gracefully with informative messages, continuing processing where possible.
- Use colored or clearly formatted console output for status and warnings.
---"""

from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
from pathlib import Path
import shutil
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
