#!/data/data/com.termux/files/home/.local/bin/python
"""extz.py — Report recursive per-extension file counts in the CWD, optionally
with total sizes per extension, and a per-extension filename sample column.

Usage:
    python extz.py                # show per-extension file counts
    python extz.py -s            # show per-extension counts with total sizes
    python extz.py -f            # show filename samples (2 max, or all if <3)
    python extz.py -s -f        # both size and filename columns
"""

from __future__ import annotations

import argparse
import os
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Iterator, Optional, Tuple

# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------


def file_extension(name: str) -> str:
    dot_index = name.rfind(".")
    if 0 < dot_index < len(name) - 1:
        return name[dot_index:]
    return ""


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
        description="Report recursive per-extension file counts in the CWD.",
    )
    parser.add_argument(
        "-s",
        "--size",
        action="store_true",
        help="show total size per extension",
    )
    parser.add_argument(
        "-f",
        "--filenames",
        action="store_true",
        help=(
            "show filename samples per extension: all names if the group has "
            "fewer than 3 files, otherwise 2 names plus '...'"
        ),
    )
    return parser.parse_args(argv)


# --------------------------------------------------------------------------
# Output formatting
# --------------------------------------------------------------------------


def _format_filename_sample(filenames: list[str], total_count: int) -> str:
    if total_count < 3:
        return ", ".join(filenames)
    return ", ".join(filenames[:2]) + ", ..."


def print_extension_histogram(
    counts: dict[str, int],
    sizes: dict[str, int],
    filenames: dict[str, list[str]],
    show_size: bool,
    show_filenames: bool,
) -> None:
    if not counts:
        print("No files found.")
        return

    # Column widths: extension column sized to longest extension name;
    # count column sized to largest count value; size column (if shown)
    # sized to longest formatted size string; filename column (if shown)
    # sized to longest formatted filename sample.

    ext_width = max(len(ext) for ext in counts)
    count_width = max(len(str(count)) for count in counts.values())
    size_strings: dict[str, str] = {}
    size_width = 0
    if show_size:
        size_strings = {ext: format_size(sizes.get(ext, 0)) for ext in counts}
        size_width = max(len(s) for s in size_strings.values())

    filename_strings: dict[str, str] = {}
    filename_width = 0
    if show_filenames:
        filename_strings = {
            ext: _format_filename_sample(filenames.get(ext, []), counts[ext])
            for ext in counts
        }
        filename_width = max(len(s) for s in filename_strings.values())

    print("extensions found:")
    for ext, count in sorted(counts.items()):
        line = f" {ext:<{ext_width}}  {count:>{count_width}}"
        if show_size:
            line += f"  {size_strings[ext]:>{size_width}}"
        if show_filenames:
            line += f"  {filename_strings[ext]:<{filename_width}}"
        print(line)

        # Special case: after the ".no_ext" row, print a separator line
        # to visually set it apart from the rest of the histogram. This only
        # happens when the ".no_ext" group exists (i.e. there are files with
        # no extension).

        if show_filenames and ext == ".no_ext":
            print(
                "-"
                * (
                    ext_width
                    + count_width
                    + (size_width + 2 if show_size else 0)
                    + (filename_width + 2 if show_filenames else 0)
                    + 4
                )
            )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> None:
    args = parse_args(argv)
    root = Path.cwd()

    ext_counts: defaultdict[str, int] = defaultdict(int)
    ext_sizes: defaultdict[str, int] = defaultdict(int)
    ext_filenames: defaultdict[str, list[str]] = defaultdict(list)

    for entry, _ in walk_files(root):
        ext = file_extension(entry.name) or ".no_ext"
        ext_counts[ext] += 1
        if args.size:
            try:
                file_size = entry.stat(follow_symlinks=False).st_size
            except OSError:
                continue
            ext_sizes[ext] += file_size
        if args.filenames:
            ext_filenames[ext].append(entry.name)

    print_extension_histogram(
        dict(ext_counts),
        dict(ext_sizes),
        dict(ext_filenames),
        args.size,
        args.filenames,
    )


if __name__ == "__main__":
    main()
