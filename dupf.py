#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script with the following specifications:

Build a command-line utility that finds duplicate files within one or more directory trees by content hash. It must be runnable as a Python script with a Termux-style shebang line (`#!/data/data/com.termux/files/usr/bin/env python`) and use `from __future__ import annotations` at the top.

**Dependencies:**
- `dh` package, providing `fsz` and `gsz` helpers (the agent should import these; they are assumed to exist in the environment and should be typed with a `# type: ignore[import-untyped]` comment).
- `loguru` for logging.
- `xxhash` package, specifically `xxh64`, for fast non-cryptographic file hashing (also with a `# type: ignore[import-untyped]` comment).
- Standard library: `argparse`, `collections.defaultdict`, `multiprocessing.pool` (`Pool`, `AsyncResult`), `pathlib.Path`, `typing` (`TYPE_CHECKING`, `TypeAlias`). `Sequence` is imported from `collections.abc` only under `TYPE_CHECKING`.

**Module-level constants:**
- `CHUNKSIZE` = 32768 bytes for streaming file reads.
- `POOL_WORKERS` = 8 worker processes.
- `SKIP_PARTS` = a tuple of path component names to ignore: `.git`, `__pycache__`, `.mypy_cache`, `.ruff_cache`.
- `POOL_METHODS` = a tuple of the supported parallel execution strategies: `"map"`, `"starmap"`, `"imap_unordered"`, `"apply_async"`.
- A type alias `HashResult` = `tuple[str | None, Path]`.

**Functions to implement:**

1. `should_skip(path: Path) -> bool`
   - Return True if the path is a symbolic link.
   - Return True if the file size is zero or the stat call raises `OSError`.
   - Return True if any component of the path's parts is in `SKIP_PARTS`.
   - Otherwise return False.

2. `get_hash_file(path: Path) -> HashResult`
   - If the path does not exist or is empty, return `(None, path)`.
   - Otherwise stream the file in `CHUNKSIZE` binary chunks into an `xxh64` hasher using a walrus-operator loop.
   - Return `(hexdigest, path)`.
   - On `OSError`, return `(None, path)` rather than raising.

3. `hash_paths(paths: Sequence[Path], method: str) -> list[HashResult]`
   - Create a `Pool(POOL_WORKERS)` and hash the given paths using the strategy named by `method`, which must be one of `POOL_METHODS`:
     - `map`: `pool.map(get_hash_file, paths)`.
     - `starmap`: wrap each path in a single-element tuple and call `pool.starmap`.
     - `imap_unordered`: collect results from `pool.imap_unordered`.
     - `apply_async`: submit each path with `pool.apply_async`, typed as `AsyncResult`, then collect `.get()` results.
   - Raise a `ValueError` for an unknown method.
   - Return the list of results.

**Main entry point (`main` function, invoked under `if __name__ == "__main__":`):**
- Use `argparse` to accept one or more directory paths (positional) and an option to choose the pool method (restricted to `POOL_METHODS`, with a sensible default such as `map`). Optionally include a flag to control verbosity or logging.
- Walk each given directory recursively, collect all regular files, filter them through `should_skip`, and convert to `Path` objects.
- Hash the remaining files via `hash_paths`.
- Group results by hash digest using a `defaultdict(list)`, discarding entries whose hash is `None`.
- Report only groups with two or more files as duplicates, listing the file sizes (via `fsz`/`gsz` helpers for human-readable formatting) and paths, and log totals such as the number of duplicate groups and wasted space using `loguru` logger calls.
- Exit cleanly when no duplicates are found, logging that fact.

**Behavioral notes and edge cases:**
- Symlinks, empty files, unreadable files, and files inside skipped directories must be excluded without crashing.
- Hashing errors must not abort the run; unreadable files simply produce `None` hashes and are ignored.
- Use `multiprocessing` guarded by `if __name__ == "__main__":` to be safe on spawn-based platforms.
- Keep the code typed, with `from __future__ import annotations`, and make the pool always closed (use a context manager).
- Log via `loguru` rather than `print` for diagnostic output; use `print` only for final results if appropriate.

**Output requirement:** Produce one complete, runnable Python file that follows these specifications, using clear naming, concise docstrings, and type hints throughout.
---"""

from __future__ import annotations

import argparse
from collections import defaultdict
from multiprocessing.pool import AsyncResult, Pool
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

from dh import fsz, gsz  # type: ignore[import-untyped]
from loguru import logger
from xxhash import xxh64  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from collections.abc import Sequence
CHUNKSIZE: int = 32768
POOL_WORKERS: int = 8
SKIP_PARTS: tuple[str, ...] = (".git", "__pycache__", ".mypy_cache", ".ruff_cache")
POOL_METHODS: tuple[str, ...] = ("map", "starmap", "imap_unordered", "apply_async")
HashResult: TypeAlias = tuple[str | None, Path]


def should_skip(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        if not path.stat().st_size:
            return True
    except OSError:
        return True
    return any(part in SKIP_PARTS for part in path.parts)


def get_hash_file(path: Path) -> HashResult:
    try:
        if not path.exists() or path.stat().st_size == 0:
            return (None, path)
        h = xxh64()
        with path.open("rb") as f:
            while chunk := f.read(CHUNKSIZE):
                h.update(chunk)
        return (h.hexdigest(), path)
    except OSError:
        return (None, path)


def hash_paths(paths: Sequence[Path], method: str) -> list[HashResult]:
    with Pool(processes=POOL_WORKERS) as pool:
        if method == "map":
            return pool.map(get_hash_file, paths)
        if method == "starmap":
            return pool.starmap(get_hash_file, [(path,) for path in paths])
        if method == "imap_unordered":
            return list(pool.imap_unordered(get_hash_file, paths))
        if method == "apply_async":
            async_results: list[AsyncResult[HashResult]] = [pool.apply_async(get_hash_file, (path,)) for path in paths]
            return [result.get() for result in async_results]
    msg = f"Unsupported pool method: {method}"
    raise ValueError(msg)


def find_duplicates(pool_method: str = "map") -> None:
    cwd = Path.cwd()
    files_by_hash: defaultdict[str, list[Path]] = defaultdict(list)
    paths: list[Path] = [path for path in cwd.rglob("*") if path.is_file() and not should_skip(path)]
    files_by_size: dict[int, list[Path]] = {}
    for path in paths:
        try:
            size = path.stat().st_size
        except OSError as exc:
            logger.error(f"Error getting size for {path}: {exc}")
            continue
        files_by_size.setdefault(size, []).append(path)
    paths_to_hash: list[Path] = []
    for size_paths in files_by_size.values():
        if len(size_paths) > 1:
            paths_to_hash.extend(size_paths)
    if not paths_to_hash:
        logger.info("NO DUPS")
        return
    for hash_result, path in hash_paths(paths_to_hash, pool_method):
        if hash_result is not None:
            files_by_hash[hash_result].append(path)
    total: int = 0
    for hash_value, duplicate_paths in files_by_hash.items():
        if len(duplicate_paths) > 1:
            logger.info(f"hash {hash_value} :")
            for file_path in duplicate_paths:
                relative_path = file_path.relative_to(cwd)
                logger.info(f" - {relative_path}")
                total += gsz(file_path)
    if total:
        logger.info(f"total : {fsz(total)}")
    else:
        logger.info("NO DUPS")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pool-method",
        choices=POOL_METHODS,
        default="map",
        help="Multiprocessing pool method to use for hashing.",
    )
    return parser.parse_args()


def main() -> None:
    args: argparse.Namespace = parse_args()
    pool_method: str = args.pool_method
    find_duplicates(pool_method)


if __name__ == "__main__":
    main()
