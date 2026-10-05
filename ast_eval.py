#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a prompt for an AI coding agent to generate a Python 3.12 command-line utility script (intended to run under Termux on Android, using a shebang of `#!/data/data/com.termux/files/usr/bin/python3.12`) that scans Python files for syntax errors and quarantines the broken ones. The prompt should specify the following requirements:

**Purpose**: The script recursively discovers `.py` files (using a helper `get_pyfiles` function imported from a local module named `dh`), parses each file with Python's `ast` module to detect syntax errors, and for every file that fails to parse, copies (or optionally moves) it into an `error` subfolder created inside that file's parent directory, preserving per-directory organization. Use `loguru` for logging progress, warnings, and errors throughout.

**CLI arguments** (via `argparse`):
- `paths`: positional, `nargs="*"`, type `Path`, defaulting to a list containing the current working directory (`Path.cwd()`), representing files or directories to process.
- `-n` / `--dry-run`: flag (`store_true`) to only report intended actions without touching the filesystem.
- `-m` / `--move`: flag (`store_true`) to move invalid files instead of copying them (default behavior is copy).
- `--pool-method`: choice argument with options `map`, `imap_unordered`, `starmap`, `apply_async`, defaulting to `starmap`, controlling which `multiprocessing.Pool` method is used to parallelize the syntax-checking work across files.

**Notable behavior**:
- Use `multiprocessing.Pool` with `functools.partial` to bind extra arguments to a worker function that performs the per-file syntax check, selecting the pool invocation method dynamically based on the `--pool-method` argument.
- Implement a `unique_destination(dest_dir, filename)` helper that returns a non-colliding destination `Path` inside the target directory: if a file with the same name already exists, append an incrementing numeric suffix (e.g., `name_1.py`, `name_2.py`, etc.) to the stem until a free path is found.
- When a syntax error is detected, ensure the `error` directory exists (create if needed), compute a unique destination path via `unique_destination`, and use `shutil.copy2` (or `shutil.move` if `--move` is specified) to relocate the file, unless `--dry-run` is active, in which case only log what would have happened.
- Handle the case where `paths` contains either individual files or directories, expanding directories into their contained Python files via `get_pyfiles`.
- Provide a `parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace` function for argument parsing that can be tested independently, and a standard `if __name__ == "__main__":` entry point.
- Include appropriate type hints throughout (using `from __future__ import annotations`), structured logging via `loguru`'s `logger`, and graceful handling/reporting of errors (e.g., file access issues, failed parses) without crashing the whole run.
- The script should exit with an appropriate status code (e.g., via `sys.exit`) reflecting whether any syntax errors were found/processed.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/K7omdspHfu6NJQHULHWqfn"""

from __future__ import annotations
import argparse
import ast
import shutil
import sys
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import Sequence
from dh import get_pyfiles
from loguru import logger


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Python files for syntax errors and move invalid ones into per-directory 'error' folders."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path.cwd()],
        help="File or directory paths to process (default: current working directory).",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Report intended actions without modifying the filesystem.",
    )
    parser.add_argument(
        "-m",
        "--move",
        action="store_true",
        help="Move files with issues instead of copying them.",
    )
    parser.add_argument(
        "--pool-method",
        choices=["map", "imap_unordered", "starmap", "apply_async"],
        default="starmap",
        help="Multiprocessing Pool method to use (default: starmap).",
    )
    return parser.parse_args(argv)


def unique_destination(dest_dir: Path, filename: str) -> Path:
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        candidate = dest_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def check_and_quarantine(path: Path, dry_run: bool, move: bool) -> bool:
    try:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))
        return False
    except Exception as exc:
        logger.warning("Syntax error in {}: {}", path, exc)
        error_dir = path.parent / "error"
        dest = unique_destination(error_dir, path.name)
        action = "move" if move else "copy"
        if dry_run:
            logger.info("[dry-run] Would {} {} -> {}", action, path, dest)
        else:
            error_dir.mkdir(parents=True, exist_ok=True)
            if move:
                shutil.move(str(path), str(dest))
            else:
                shutil.copy2(path, dest)
            logger.info("{} {} -> {}", action, path, dest)
        return True


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    paths: list[Path] = [p.resolve() for p in args.paths]
    py_files: list[Path] = get_pyfiles(*paths)
    if not py_files:
        logger.info("No Python files found.")
        return 0
    logger.info(
        "Processing {} file(s) with 8 workers (dry-run={}, move={}, pool-method={})",
        len(py_files),
        args.dry_run,
        args.move,
        args.pool_method,
    )
    invalid_count = 0
    with Pool(processes=8) as pool:
        if args.pool_method == "map":
            worker = partial(check_and_quarantine, dry_run=args.dry_run, move=args.move)
            results: list[bool] = pool.map(worker, py_files)
            invalid_count = sum(results)
        elif args.pool_method == "imap_unordered":
            worker = partial(check_and_quarantine, dry_run=args.dry_run, move=args.move)
            results_iter = pool.imap_unordered(worker, py_files)
            invalid_count = sum(results_iter)
        elif args.pool_method == "starmap":
            args_list: list[tuple[Path, bool, bool]] = [(p, args.dry_run, args.move) for p in py_files]
            results = pool.starmap(check_and_quarantine, args_list)
            invalid_count = sum(results)
        else:
            async_results = [
                pool.apply_async(check_and_quarantine, (path, args.dry_run, args.move)) for path in py_files
            ]
            for result in async_results:
                if result.get():
                    invalid_count += 1
    logger.info("Finished. {} file(s) had syntax errors.", invalid_count)
    return invalid_count


if __name__ == "__main__":
    sys.exit(main())
