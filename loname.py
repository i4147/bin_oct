#!/data/data/com.termux/files/usr/bin/python
"""Rename files to a normalized lowercase form.

Normalization rules (applied to the filename stem; extension is preserved):
1. Lowercase the name.
2. Convert spaces to underscores and strip punctuation characters.
3. Collapse any run of the characters `_`, `-`, `:` into a single `_`.
4. Strip leading/trailing underscores.
5. If the resulting name collides, append a numeric suffix via unique_path.
"""

from __future__ import annotations

import argparse
import re
import string
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, Iterator, Optional, Sequence

# Characters treated as punctuation to remove (ASCII set is usually enough for filenames)
_PUNCT_TO_REMOVE: str = string.punctuation.replace("_", "").replace("-", "").replace(":", "")
_TRANSLATE_TABLE = str.maketrans({c: None for c in _PUNCT_TO_REMOVE} | {" ": "_"})

# After the first pass, collapse any sequence of _, -, : into a single _
_COLLAPSE_RE = re.compile(r"[_:\-]+")


def normalize_name(name: str) -> str:
    """Return a normalized version of a filename (stem + suffix)."""
    path = Path(name)
    stem = path.stem
    suffix = path.suffix  # includes the leading dot, or empty

    # 1. lowercase
    stem = stem.lower()

    # 2. remove punctuation + turn spaces into underscores
    stem = stem.translate(_TRANSLATE_TABLE)

    # 3. collapse runs of _ - : into a single underscore
    stem = _COLLAPSE_RE.sub("_", stem)

    # tidy edges
    stem = stem.strip("_")

    if not stem:
        stem = "unnamed"

    return stem + suffix.lower()


def unique_path(path: Path) -> Path:
    """Return a non-existing path by appending _N before the suffix if needed."""
    if not path.exists():
        return path

    parent = path.parent
    stem = path.stem
    suffix = path.suffix
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def process_file(
    path: Path | str,
    *,
    dry_run: bool = False,
) -> Optional[str]:
    """Normalize and rename a single file. Returns a log message or None."""
    path = Path(path)

    # Tolerate case-only differences on case-insensitive filesystems
    if not path.exists():
        lowered = Path(str(path).lower())
        if not lowered.exists():
            return None
        path = lowered

    if not path.is_file():
        return None

    new_name = normalize_name(path.name)
    if new_name == path.name:
        return None

    new_path = path.with_name(new_name)
    if new_path.exists() and new_path.resolve() != path.resolve():
        new_path = unique_path(new_path)

    if dry_run:
        return f"[dry-run] {path.name} -> {new_path.name}"

    path.rename(new_path)
    return f"{path.name} -> {new_path.name}"


def mpf(
    func,
    items: Iterable,
    *,
    max_workers: Optional[int] = None,
) -> Iterator:
    """Simple parallel map using ProcessPoolExecutor (replacement for dh.mpf)."""
    items = list(items)
    if not items:
        return

    # For very small batches the process overhead is not worth it
    if len(items) < 4 or max_workers == 1:
        for item in items:
            yield func(item)
        return

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(func, item): item for item in items}
        for future in as_completed(futures):
            try:
                yield future.result()
            except Exception as exc:  # noqa: BLE001
                print(f"Error processing {futures[future]}: {exc}", file=sys.stderr)


def collect_files(
    root: Path,
    *,
    recursive: bool,
) -> list[Path]:
    """Collect files to process, skipping .git and symlinks."""
    if recursive:
        candidates = root.rglob("*")
    else:
        candidates = root.glob("*")

    return [p for p in candidates if p.is_file() and not p.is_symlink() and ".git" not in p.parts]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize filenames: lowercase, strip punctuation, spaces→_, collapse _-:"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or directories to process (default: current directory)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recurse into subdirectories",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without changing anything",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=None,
        metavar="N",
        help="Number of parallel workers (default: CPU count)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    cwd = Path.cwd()

    if not args.paths:
        files = collect_files(cwd, recursive=args.recursive)
    else:
        files = []
        for p in args.paths:
            p = p if p.is_absolute() else cwd / p
            if p.is_dir():
                files.extend(collect_files(p, recursive=args.recursive))
            elif p.is_file():
                files.append(p)

    if not files:
        print("No files to process.", file=sys.stderr)
        return 0

    # Bind dry_run so the worker function stays picklable
    def worker(path: Path) -> Optional[str]:
        return process_file(path, dry_run=args.dry_run)

    for msg in mpf(worker, files, max_workers=args.jobs):
        if msg:
            print(msg)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
