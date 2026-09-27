#!/data/data/com.termux/files/home/.local/bin/python
"""dirz.py — List top-level directories of the CWD, optionally with total sizes.



Usage:
    python dirz.py                # list top-level dirs
    python dirz.py -s            # list top-level dirs with total sizes
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterator, Optional, Tuple

# --------------------------------------------------------------------------
# Shared helpers (duplicated from the original compressed script)
# --------------------------------------------------------------------------


def format_size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if value < 1024 or unit == "PB":
            if unit == "B":
                return f"{int(value)}B"
            return f"{value:.1f}{unit}"
        value /= 1024
    # Unreachable: the loop always returns on the last iteration.


def walk_files(root: Path) -> Iterator[tuple[os.DirEntry, Optional[str]]]:
    # Stack of (path, top_level_name) pairs. top_level_name is None for
    # the root itself; for subdirectories it's the name of the first-level
    # subdirectory under root that contains them.

    stack: list[tuple[str, Optional[str]]] = [(str(root), None)]

    while stack:
        current_path, top_level = stack.pop()
        try:
            with os.scandir(current_path) as entries:
                for entry in entries:
                    if entry.name == ".git":
                        continue
                    if entry.is_symlink():
                        continue
                    if entry.is_file(follow_symlinks=False):
                        yield entry, top_level
                    elif entry.is_dir(follow_symlinks=False):
                        # Propagate top_level: if we're at the root, the first
                        # subdirectory's own name becomes the top_level for its
                        # contents; deeper subdirectories keep the same top_level.

                        child_top_level = (
                            top_level if top_level is not None else entry.name
                        )
                        stack.append((entry.path, child_top_level))
        except OSError:
            # Unreadable directory (permissions, vanished mid-scan, etc.):
            # skip it silently, matching the original behavior.
            continue


# --------------------------------------------------------------------------
# Argument parsing
# --------------------------------------------------------------------------


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List top-level directories of the CWD, optionally with total sizes.",
    )
    parser.add_argument(
        "-s",
        "--size",
        action="store_true",
        help="show total size per directory",
    )
    return parser.parse_args(argv)


# --------------------------------------------------------------------------
# Output formatting
# --------------------------------------------------------------------------


def print_directory_listing(
    dirs: list[str],
    sizes: dict[str, int],
    show_size: bool,
) -> None:
    size_strings: dict[str, str] = {}
    size_width = 0
    if show_size and dirs:
        size_strings = {name: format_size(sizes.get(name, 0)) for name in dirs}
        size_width = max(len(s) for s in size_strings.values())

    for dir_name in dirs:
        line = f"-{dir_name}"
        if show_size:
            line += f"  {size_strings[dir_name]:>{size_width}}"
        print(line)

    total_line = f"total:{len(dirs)} dirs"
    if show_size:
        total_line += f"  {format_size(sum(sizes.values()))}"
    print(total_line)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> None:
    args = parse_args(argv)
    root = Path.cwd()

    # Collect top-level directory names (non-recursive scandir of the root,
    # skipping symlinks and .git, matching the original behavior).

    dir_names: list[str] = []
    try:
        with os.scandir(root) as entries:
            for entry in entries:
                if entry.name == ".git":
                    continue
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    dir_names.append(entry.name)
    except OSError:
        pass
    dir_names.sort()

    # If sizes are requested, walk all files once and accumulate sizes per
    # top-level directory. This is a separate pass from the name collection
    # above (the original script did both in one pass, but here we only
    # need sizes when -s is given, so we skip the walk entirely otherwise).

    dir_sizes: dict[str, int] = {}
    if args.size:
        for entry, top_level in walk_files(root):
            if top_level is None:
                continue
            try:
                file_size = entry.stat(follow_symlinks=False).st_size
            except OSError:
                continue
            dir_sizes[top_level] = dir_sizes.get(top_level, 0) + file_size

    print_directory_listing(dir_names, dir_sizes, args.size)


if __name__ == "__main__":
    main()
