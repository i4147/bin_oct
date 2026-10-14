#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans the current working directory tree, gathers all text-based files while skipping hidden files and binary file types, and computes how often each non-empty, whitespace-trimmed line appears across the entire set of files. The script should process files concurrently using a pool of worker processes to speed up reading large projects, and it should tolerate unreadable or badly encoded files by logging an error and continuing rather than aborting. Each file should be read leniently as UTF-8, ignoring undecodable characters. The final output should be a summary report that lists the most frequently repeated lines (with their counts) to help identify duplicated code, boilerplate, or repeated content across a codebase, and it should also report overall statistics such as the number of files processed and the total number of lines analyzed. The script should be runnable from the command line with options that let the user control things like the number of results shown, the minimum occurrence threshold, and the level of logging detail, and it should print a clear, readable result to the console.
---"""

from __future__ import annotations
import argparse
from collections import Counter
from multiprocessing.pool import AsyncResult, Pool
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias
from dh import BIN_EXT
from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Sequence
EXCLUDED_EXTENSIONS: frozenset[str] = frozenset(BIN_EXT)
POOL_WORKERS: int = 8
POOL_METHODS: tuple[str, ...] = ("map", "starmap", "imap_unordered", "apply_async")
LineCounter: TypeAlias = Counter[str]


def process_file(path: Path) -> LineCounter:
    counter: LineCounter = Counter()
    try:
        with path.open(encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.strip()
                if line:
                    counter[line] += 1
    except Exception as exc:
        logger.error(f"Error reading {path}: {exc}")
    return counter


def collect_files_by_extension() -> dict[str, list[Path]]:
    ext_map: dict[str, list[Path]] = {}
    cwd = Path.cwd()
    for root, _dirnames, filenames in cwd.walk():
        for fname in filenames:
            if fname.startswith("."):
                continue
            path = root / fname
            ext = path.suffix
            if ext in EXCLUDED_EXTENSIONS:
                continue
            ext_map.setdefault(ext, []).append(path)
    return ext_map


def process_paths(paths: Sequence[Path], method: str) -> list[LineCounter]:
    with Pool(processes=POOL_WORKERS) as pool:
        if method == "map":
            return pool.map(process_file, paths)
        if method == "starmap":
            return pool.starmap(process_file, [(path,) for path in paths])
        if method == "imap_unordered":
            return list(pool.imap_unordered(process_file, paths))
        if method == "apply_async":
            async_results: list[AsyncResult[LineCounter]] = [pool.apply_async(process_file, (path,)) for path in paths]
            return [result.get() for result in async_results]
    msg = f"Unsupported pool method: {method}"
    raise ValueError(msg)


def collect_lines_for_extension(ext: str, files: Sequence[Path], pool_method: str) -> None:
    if not files:
        return
    global_counter: LineCounter = Counter()
    logger.info(f"Processing {len(files)} files with extension '{ext}'")
    for result in process_paths(files, pool_method):
        global_counter.update(result)
    output_name = ext.lstrip(".") or "no_extension"
    output_file = Path(f"{output_name}.txt")
    written_lines = 0
    with output_file.open("w", encoding="utf-8") as fo:
        for line, count in global_counter.most_common():
            if count >= 2:
                fo.write(line + "\n")
                written_lines += 1
    logger.info(f"Saved {written_lines} duplicate lines to {output_file}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pool-method",
        choices=POOL_METHODS,
        default="map",
        help="Multiprocessing pool method to use for line counting.",
    )
    return parser.parse_args()


def main() -> None:
    args: argparse.Namespace = parse_args()
    pool_method: str = args.pool_method
    ext_map = collect_files_by_extension()
    if not ext_map:
        logger.info("No eligible files found.")
        return
    for ext, files in ext_map.items():
        collect_lines_for_extension(ext, files, pool_method)


if __name__ == "__main__":
    raise SystemExit(main())
