#!/data/data/com.termux/files/usr/bin/python

from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import argparse
import os
import sys

from dh import fsz


# Directories to skip entirely (matched by basename at any depth).
SKIP_DIRS = {
    # VCS
    ".git",
    ".hg",
    ".svn",
    ".bzr",
    # Python
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    "env",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".ipynb_checkpoints",
    "eggs",
    ".eggs",
    # Node / web
    "node_modules",
    ".next",
    ".nuxt",
    ".parcel-cache",
    # Build outputs
    "build",
    "dist",
    "target",
    "out",
    # Editors
    ".idea",
    ".vscode",
    # Misc caches
    ".cache",
    ".sass-cache",
}


def iter_files(cwd: Path):
    """Yield regular (non-symlink) files, pruning SKIP_DIRS and symlinked dirs."""
    for root, dirnames, filenames in os.walk(cwd, topdown=True, followlinks=False):
        # Prune in-place so os.walk never descends into these.
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not os.path.islink(os.path.join(root, d))]
        for name in filenames:
            p = Path(root) / name
            if p.is_symlink():
                continue
            yield p


def show_all(cwd: Path) -> None:
    counts: dict[str, int] = defaultdict(int)
    sizes: dict[str, int] = defaultdict(int)

    for f in iter_files(cwd):
        ext = f.suffix.lstrip(".") or "(none)"
        try:
            size = f.stat().st_size
        except OSError:
            continue
        counts[ext] += 1
        sizes[ext] += size

    if not sizes:
        print("No files found in current directory")
        return

    for ext in sorted(sizes, key=lambda e: sizes[e], reverse=True):
        label = f".{ext}" if ext != "(none)" else ext
        print(f"{label}: {counts[ext]} files, {fsz(sizes[ext])}")

    print("-" * 40)
    print(f"Total: {sum(counts.values())} files, {fsz(sum(sizes.values()))}")


def show_one(cwd: Path, ext: str) -> None:
    files = [f for f in iter_files(cwd) if f.suffix.lstrip(".") == ext]
    if not files:
        print(f"No .{ext} files found in current directory")
        return
    total_size = sum(f.stat().st_size for f in files)
    print(f"Total number of .{ext} files: {len(files)}")
    print(f"Total size of .{ext} files: {fsz(total_size)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("extension", nargs="?", help="extension to scan (e.g. py)")
    ap.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="show all found extensions with total size for each",
    )
    args = ap.parse_args()

    cwd = Path.cwd()
    if args.all:
        show_all(cwd)
    elif args.extension:
        show_one(cwd, args.extension.lstrip("."))
    else:
        ap.print_help()
        sys.exit(1)


if __name__ == "__main__":
    raise SystemExit(main())
