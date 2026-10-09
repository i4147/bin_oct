#!/data/data/com.termux/files/usr/bin/python
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
