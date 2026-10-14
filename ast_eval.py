#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans one or more files or directories for Python source files, checks each file for syntax errors, and quarantines the invalid ones into an "error" folder located alongside each affected file.
The script should accept a list of file or directory paths from the command line, defaulting to the current working directory when none are given. When a directory is provided, it should recursively discover all Python files within it. Each file should be validated by attempting to parse it as Python source, and any file that fails to parse should be handled as follows:
- By default, copy the problematic file into a sibling "error" directory, leaving the original in place.
- Provide an option to move the problematic file instead of copying it, so the original is removed from its location.
- Provide a dry-run option that reports every intended action (which files would be copied or moved, and where) without modifying the filesystem.
The processing of many files should run in parallel using multiple worker processes to improve throughput on large codebases. The user should be able to select which parallel execution strategy is used from a set of common multiprocessing pool methods, with a sensible default.
The script should log its progress and results clearly, reporting which files passed, which failed with their syntax error details (file, line, and message), and a final summary of counts. It should handle missing paths and unreadable files gracefully with informative messages rather than crashing, and it should return a non-zero exit status if any syntax errors were found, so it can be used in automated pipelines.
Include a help message that describes the purpose and every available option.
---"""

from __future__ import annotations
import argparse
import ast
from functools import partial
from multiprocessing import Pool
from pathlib import Path
import shutil
import sys
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
