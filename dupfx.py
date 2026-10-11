#!/data/data/com.termux/files/usr/bin/python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python duplicate-file finder with the following specification:

Create a single-file Python command-line script (targeting a Termux/Android environment with a Python shebang pointing to the Termux Python path) that finds duplicate files across one or more directories using a multi-stage hashing pipeline.

**Purpose and overall behavior:**
The script recursively scans the given directories, groups files by size, then narrows candidates with a cheap partial hash, and finally confirms duplicates with a full-content hash. Files that share identical full hashes are reported as duplicate groups. The tool should be efficient on large trees by avoiding full reads whenever a cheaper check can rule a file out.

**Inputs:**
- One or more directory paths supplied as positional command-line arguments, defaulting to the current directory if none are given.
- Optional flags defined with argparse for behavior such as the output mode (for example, printing groups versus deleting or listing extras), a minimum file size filter, and whether to follow symbolic links. Choose sensible flag names and document them in the help text.
- Constants: a quick-read window of 4096 bytes, a read chunk size of 65536 bytes, and a process pool of 8 workers.

**Outputs:**
- Human-readable report to standard output listing each duplicate group (file paths with their size), and a summary count of duplicate groups and wasted bytes.
- Logging of informational messages, warnings, and errors through the loguru library rather than the standard logging module or bare print for diagnostics.

**Dependencies:**
- Standard library: argparse, collections (defaultdict), multiprocessing (Pool), pathlib, typing.
- Third-party: loguru for logging, xxhash (xxh64 hasher) for hashing.
- Use `from __future__ import annotations` and a `TYPE_CHECKING` block for collections.abc type-only imports.

**Key logic to implement:**
1. Recursive traversal of each input directory collecting regular files only.
2. Deduplicate hard links and repeated paths: identify files by the (inode, device) pair obtained from stat; skip a file if its key was already seen, and return no key (treat as skipped) if stat fails.
3. Group files by size; discard size groups with fewer than two members. Skip zero-length files from hashing (they are considered identical to each other and may be reported as a group or handled explicitly, document the choice).
4. Quick hash stage: for each size-group candidate, compute an xxh64 hash over the first 4096 bytes. If the file is more than twice the quick-read size, also hash the last 4096 bytes. If the file is between 4096 and 8192 bytes, hash the remaining bytes after the head. Wrap I/O errors in an OSError with a descriptive message including the path, chained from the original exception.
5. Full hash stage: for remaining candidates, compute an xxh64 over the entire file read in 65536-byte chunks until EOF. On an OSError, return an empty-string hash for the path rather than crashing, and log the failure. Empty files return an empty hash immediately.
6. Use multiprocessing.Pool with 8 workers to parallelize the hashing stages across files, and collect results to group paths by hash using defaultdict(list).
7. Report groups with two or more members, ignoring the empty-hash sentinel from failed or empty reads unless explicitly documented otherwise.

**Error handling and edge cases:**
- Unreadable files, broken symbolic links, permission errors, and files that vanish mid-scan must not abort the run; log them and continue.
- Handle nonexistent input paths by logging an error and exiting with a nonzero status, or skipping them with a warning, and say which in the code.
- Handle files whose size changes between stat and read gracefully.
- Handle empty files and files smaller than the quick-read window correctly.
- Guard the entry point with `if __name__ == "__main__":` and ensure multiprocessing works correctly (picklable top-level worker functions, pool closed and joined).

**Execution details:**
- Make the script executable with the Termux Python shebang line.
- Runs from the command line as `python script.py [options] [directories...]`.
- Should work on Android/Termux with standard Python 3 and the two third-party packages installed via pip.

Produce the complete script following these requirements, with clear function boundaries (scanning, size grouping, quick hashing, full hashing, grouping, reporting, and argument parsing), docstrings or brief comments where helpful, and consistent naming and style.
---"""

from __future__ import annotations

import argparse
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from xxhash import xxh64

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

QUICK_READ: int = 4096
CHUNK_SIZE: int = 65536
POOL_WORKERS: int = 8


def file_stat_key(p: Path) -> tuple[int, int] | None:
    try:
        st = p.stat()
        return (st.st_ino, st.st_dev)
    except OSError:
        return None


def quick_hash(path: Path, n: int = QUICK_READ) -> str:
    h = xxh64()
    try:
        size = path.stat().st_size
        with path.open("rb") as f:
            head = f.read(n)
            h.update(head)
            if size > n * 2:
                f.seek(max(size - n, 0))
                tail = f.read(n)
                h.update(tail)
            elif size > n:
                rest = f.read()
                h.update(rest)
    except OSError as e:
        msg = f"quick_hash error {path}: {e}"
        raise OSError(msg) from e
    return h.hexdigest()


def full_hash(path: Path) -> tuple[str, Path]:
    try:
        if not path.stat().st_size:
            return ("", path)
    except OSError:
        return ("", path)
    h = xxh64()
    try:
        with path.open("rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return (h.hexdigest(), path)
    except OSError:
        return ("", path)


def iter_files(
    root: Path,
    recursive: bool,
    follow_symlinks: bool,
    include_git: bool = False,
) -> Iterator[Path]:
    if recursive:
        iterator: Iterable[Path] = root.rglob("*")
    else:
        iterator = root.iterdir()
    for p in iterator:
        if not include_git and ".git" in p.parts:
            continue
        if not p.is_file():
            continue
        if p.is_symlink() and not follow_symlinks:
            continue
        yield p


def choose_keep(files: list[Path], policy: str = "oldest") -> Path:
    if not files:
        msg = "Empty file list"
        raise ValueError(msg)
    if policy == "first":
        return min(files, key=str)
    elif policy == "oldest":
        return min(files, key=lambda p: p.stat().st_mtime)
    elif policy == "newest":
        return max(files, key=lambda p: p.stat().st_mtime)
    else:
        return min(files, key=str)


def format_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    elif n < 1024 * 1024:
        return f"{n / 1024:.2f} KiB"
    elif n < 1024 * 1024 * 1024:
        return f"{n / 1024 / 1024:.2f} MiB"
    else:
        return f"{n / 1024 / 1024 / 1024:.2f} GiB"


def main() -> None:
    cwd = Path.cwd()
    p = argparse.ArgumentParser(description="Find and delete duplicate files by content.")
    p.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Search directories recursively (default: True).",
    )
    p.add_argument(
        "-r",
        "--remove",
        action="store_true",
        default=False,
        help="Actually delete duplicate files. Without this flag, only report them.",
    )
    p.add_argument(
        "-a",
        "--all",
        action="store_true",
        default=False,
        help="Include .git directories in the search (symlinks are still skipped).",
    )
    p.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        default=False,
        help="Don't delete; just show what would be done.",
    )
    p.add_argument(
        "--follow-symlinks",
        action="store_true",
        default=False,
        help="Follow symlinks to files.",
    )
    p.add_argument(
        "-k",
        "--keep",
        choices=("first", "oldest", "newest"),
        default="oldest",
        help="Which file to keep within duplicates.",
    )
    args = p.parse_args()
    root = Path.cwd()

    size_groups: defaultdict[int, list[Path]] = defaultdict(list)
    total_files = 0
    for f in iter_files(
        root,
        args.recursive,
        args.follow_symlinks,
        include_git=args.all,
    ):
        total_files += 1
        try:
            size = f.stat().st_size
            size_groups[size].append(f)
        except OSError:
            continue
    candidates: dict[int, list[Path]] = {s: lst for s, lst in size_groups.items() if len(lst) > 1}
    if not candidates:
        print(f"Scanned {total_files} files. No potential duplicates found.")
        return

    quick_groups: defaultdict[tuple[int, str], list[Path]] = defaultdict(list)
    with Pool(processes=POOL_WORKERS) as pool:
        futures: list[tuple[Path, object]] = []
        for files in candidates.values():
            for fpath in files:
                futures.append((fpath, pool.apply_async(quick_hash, (fpath,))))
        for fpath, fut in futures:
            try:
                h: str = fut.get()
                key = (fpath.stat().st_size, h)
                quick_groups[key].append(fpath)
            except Exception as e:
                logger.warning(f"Skipping {fpath}: {e}")
    need_full: list[list[Path]] = [group for group in quick_groups.values() if len(group) > 1]
    if not need_full:
        print(f"Scanned {total_files} files. No duplicates found.")
        return

    full_groups: defaultdict[str, list[tuple[Path, tuple[int, int] | None]]] = defaultdict(list)
    with Pool(processes=POOL_WORKERS) as pool:
        futures2: list[tuple[Path, tuple[int, int] | None, object]] = []
        for group in need_full:
            for fpath in group:
                st_key = file_stat_key(fpath)
                futures2.append((fpath, st_key, pool.apply_async(full_hash, (fpath,))))
        for fpath, st_key, fut in futures2:
            try:
                h, _ = fut.get()
                if h:
                    full_groups[h].append((fpath, st_key))
            except Exception as e:
                logger.warning(f"Skipping {fpath}: {e}")

    deletion_groups: list[tuple[int, list[tuple[Path, Path]]]] = []
    for entries in full_groups.values():
        if len(entries) < 2:
            continue
        inode_map: defaultdict[tuple[int, int] | None, list[Path]] = defaultdict(list)
        for p_path, stk in entries:
            inode_map[stk].append(p_path)
        group_reps: list[Path] = [min(ps, key=str) for ps in inode_map.values()]
        if len(group_reps) < 2:
            continue
        keep_file = choose_keep(group_reps, policy=args.keep)
        deletes = [rep for rep in group_reps if rep != keep_file]
        if not deletes:
            continue
        try:
            group_size = keep_file.stat().st_size
        except OSError:
            group_size = 0
        pairs = [(keep_file, d) for d in deletes]
        deletion_groups.append((group_size, pairs))

    if not deletion_groups:
        print(f"Scanned {total_files} files. No duplicates found.")
        return

    total_deletes = sum(len(pairs) for _, pairs in deletion_groups)
    for idx, (group_size, pairs) in enumerate(deletion_groups, start=1):
        print()
        print(f"[Group {idx}]  {format_size(group_size)} each")
        for keep_file, del_file in pairs:
            try:
                keep_rel = keep_file.relative_to(cwd)
            except ValueError:
                keep_rel = keep_file
            try:
                del_rel = del_file.relative_to(cwd)
            except ValueError:
                del_rel = del_file
            print(f"  KEEP     {keep_rel}")
            print(f"  REMOVE   {del_rel}")

    print()
    if not args.remove:
        print(f"Report-only mode. Re-run with -r/--remove to delete {total_deletes} file(s)")
        return
    if args.dry_run:
        print(f"Dry run complete. Re-run with -a/--apply to delete {total_deletes} file(s)")
        return

    removed = 0
    failed = 0
    freed_space = 0
    for _, pairs in deletion_groups:
        for _, del_file in pairs:
            try:
                size = del_file.stat().st_size
                del_file.unlink()
                freed_space += size
                removed += 1
            except OSError as e:
                failed += 1
                logger.error(f"Failed: {del_file} - {e}")

    print()
    print(f"Deleted {removed} file(s)")
    if failed:
        print(f"Failed: {failed}")
    if freed_space:
        print(f"Space freed: {format_size(freed_space)}")


if __name__ == "__main__":
    raise SystemExit(main())
