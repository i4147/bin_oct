#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a project directory tree for test files and relocates them into a single centralized test folder in the user's home directory, while keeping a persistent record of every move.
The tool should:
- Accept a source directory path from the command line (with a sensible default of the current directory) and recursively search it for Python files whose names indicate they are tests, such as names containing "test_" or "_test" as part of the filename.
- Skip files that are already located inside the central test destination so they are not moved onto themselves.
- Move each identified test file into the central test folder, preserving its relative location within the source tree so that files from different subdirectories do not collide or overwrite one another. Create any missing destination directories automatically.
- Perform the file moves concurrently using a small pool of worker processes to speed up work on large trees, and collect the outcome of each move.
- For each attempted move, record whether it succeeded, the original path, and a human-readable message describing the destination or the error encountered, without letting one failed move stop the others.
- Append or write the results to a JSON log file in the user's home directory so the user can later review or audit which files were moved, and where.
- Log progress and summary information (number of files found, moved, and failed) using a clear logging approach, and print a concise final report to the console.
- Support a dry-run option that lists which files would be moved without actually moving anything.
- Handle common errors gracefully, including missing source directories, permission problems, and name conflicts at the destination, and return a meaningful exit status indicating overall success or failure.
- Be runnable as a standalone command-line program with clear help text describing its options.
---"""

from __future__ import annotations
import argparse
import json
from multiprocessing import Pool
from pathlib import Path
import shutil
from typing import Any
from loguru import logger

TESTS_DIR: Path = Path.home() / "tmp" / "tests"
MOVED_FILES_LOG: Path = Path.home() / "tmp" / "moved_files.json"
POOL_WORKERS: int = 8
MoveResult = tuple[str, bool, str]


def is_test_file(path: Path) -> bool:
    stem: str = path.stem
    return "_test" in stem or "test_" in stem


def get_relative_path(path: Path, base_dir: Path) -> Path:
    try:
        return path.relative_to(base_dir)
    except ValueError:
        return path


def move_file(source: Path, dest: Path) -> MoveResult:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
        return str(source), True, f"Moved to {dest}"
    except Exception as e:
        return str(source), False, f"Error: {e!s}"


def find_test_files(base_dir: Path) -> list[Path]:
    test_files: list[Path] = []
    for py_file in base_dir.rglob("*.py"):
        if is_test_file(py_file):
            test_files.append(py_file)
    return test_files


def move_files_parallel(
    test_files: list[Path],
    base_dir: Path,
) -> tuple[dict[str, str], list[tuple[str, str]]]:
    file_mapping: dict[str, str] = {}
    results: list[tuple[str, str]] = []
    pool: Pool = Pool(processes=POOL_WORKERS)
    try:
        async_results: list[tuple[Any, Path, Path]] = []
        for source_file in test_files:
            relative_path: Path = get_relative_path(source_file, base_dir)
            dest_file: Path = TESTS_DIR / relative_path
            async_result = pool.apply_async(move_file, (source_file, dest_file))
            async_results.append((async_result, source_file, dest_file))
        for async_result, source_file, dest_file in async_results:
            _source_str, success, message = async_result.get()
            if success:
                file_mapping[str(source_file)] = str(dest_file)
                results.append((str(source_file), message))
                logger.success(message)
            else:
                results.append((str(source_file), message))
                logger.error(message)
    finally:
        pool.close()
        pool.join()
    return file_mapping, results


def reverse_move(moved_files_log: Path) -> tuple[dict[str, str], list[tuple[str, str]]]:
    if not moved_files_log.exists():
        msg = f"Log file not found: {moved_files_log}"
        raise FileNotFoundError(msg)
    with open(moved_files_log) as f:
        file_mapping: dict[str, str] = json.load(f)
    results: list[tuple[str, str]] = []
    pool: Pool = Pool(processes=POOL_WORKERS)
    try:
        async_results: list[tuple[Any, Path, Path]] = []
        for original_path, moved_path in file_mapping.items():
            moved_file: Path = Path(moved_path)
            original_file: Path = Path(original_path)
            if moved_file.exists():
                async_result = pool.apply_async(move_file, (moved_file, original_file))
                async_results.append((async_result, moved_file, original_file))
        for async_result, source_file, _dest_file in async_results:
            _source_str, success, message = async_result.get()
            if success:
                results.append((str(source_file), message))
                logger.success(message)
            else:
                results.append((str(source_file), message))
                logger.error(message)
    finally:
        pool.close()
        pool.join()
    return file_mapping, results


def save_log(file_mapping: dict[str, str], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(file_mapping, f, indent=2)
    print(f"📋 Log saved to: {log_path}")


def cleanup_empty_dirs(root: Path) -> None:
    try:
        for parent in sorted(root.rglob("*"), reverse=True):
            if parent.is_dir():
                try:
                    if not any(parent.iterdir()):
                        parent.rmdir()
                except OSError:
                    continue
    except OSError:
        pass


def main() -> int:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=("Move Python test files to ~/tmp/tests with directory structure preservation.")
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Reverse the move operation (return files to original locations).",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path.cwd(),
        help="Base directory to search for test files (default: current directory).",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=MOVED_FILES_LOG,
        help=f"Path to log file (default: {MOVED_FILES_LOG}).",
    )
    args: argparse.Namespace = parser.parse_args()
    try:
        if args.reverse:
            print(f"🔄 Reversing move operation from log: {args.log}")
            _file_mapping, results = reverse_move(args.log)
            print(f"✅ Reversed {len(results)} files")
            cleanup_empty_dirs(TESTS_DIR)
        else:
            print(f"🔍 Searching for test files in: {args.dir}")
            test_files: list[Path] = find_test_files(args.dir)
            if not test_files:
                logger.warning("❌ No test files found.")
                return 0
            print(f"📦 Found {len(test_files)} test file(s)")
            print(f"📍 Destination: {TESTS_DIR}")
            file_mapping, _results = move_files_parallel(test_files, args.dir)
            save_log(file_mapping, args.log)
            print(f"✅ Moved {len(file_mapping)} file(s)")
    except FileNotFoundError as e:
        logger.error(f"❌ Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
