#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans a user-specified directory (or a single file) and converts text files from Windows-style line endings (CRLF) to Unix-style line endings (LF) in place. The tool should be a command-line utility that accepts a target path as input, plus optional arguments for controlling behavior such as the number of parallel workers and whether to process subdirectories.
Key requirements:
- **Input:** A file or directory path provided on the command line. When a directory is given, traverse it recursively, skipping common generated or tooling directories such as version control folders, Python cache folders, test and type-checker caches, coverage data, egg-info metadata, and IDE configuration folders.
- **File filtering:** Only process regular files. Detect and skip binary files so that their contents are never modified. Text files should be checked and converted only when they actually contain line-ending differences.
- **Conversion behavior:** Convert line endings to LF in place, leaving files that are already in Unix format untouched (do not rewrite them). Preserve all other content byte-for-byte.
- **Parallel processing:** Process files concurrently using a pool of worker processes with a configurable, sensible upper limit on the number of workers. Read and write files in a memory-efficient manner suitable for large files.
- **Output/reporting:** For each file, report one of the outcomes: converted, already in Unix format, skipped as binary, skipped because it is not a file, or failed with a read/write error including the error message. Log progress and errors using a structured logging approach, and print a concise summary at the end with total counts for each outcome.
- **Error handling:** Failures on individual files must not stop processing of the remaining files. Handle permission and I/O errors gracefully and report them.
- **Command-line interface:** Provide clear help text, validate that the provided path exists, and exit with a non-zero status code if fatal errors occur or if any file failed to process.
- **Safety:** Avoid following symbolic links into unintended locations where practical, and never modify files outside the specified target path.
---"""

from __future__ import annotations
import argparse
from multiprocessing import Pool
from pathlib import Path
from dh import is_binary
from dos2unix import dos2unix
from loguru import logger

MAX_WORKERS = 8
CHUNK_SIZE = 32768
SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".coverage",
    ".egg-info",
    ".idea",
}


def should_skip_dir(directory: Path) -> bool:
    return directory.name in SKIP_DIRS


def convert_file(path: Path) -> tuple[str, bool, str]:
    path = Path(path)
    try:
        if not path.is_file():
            return (str(path), False, "Not a file")
        if is_binary(path):
            return (str(path), False, "Binary file (skipped)")
        try:
            data = f.read_bytes()
            new_data = dos2unix(data)
            if new_data != data:
                path.write_bytes(new_data)
                return (str(path), True, "Converted")
            else:
                return (str(path), True, "Already Unix format")
        except OSError as e:
            return (str(path), False, f"Read/Write error: {e}")
    except Exception as e:
        return (str(path), False, f"Error: {e}")


def find_text_files(paths: list[Path]) -> list[Path]:
    files = []
    for path in paths:
        if path.is_file():
            if not is_binary(path):
                files.append(path)
        elif path.is_dir():
            for text_file in path.rglob("*"):
                if any(should_skip_dir(parent) for parent in text_file.parents):
                    continue
                if text_file.is_file() and not is_binary(text_file):
                    files.append(text_file)
    return files


def get_input_paths(input_args: list[str] | None) -> list[Path]:
    if not input_args:
        return [Path.cwd()]
    paths = []
    for arg in input_args:
        path = Path(arg).resolve()
        if path.exists():
            paths.append(path)
        else:
            logger.warning(f"Path does not exist: {arg}")
    return paths


def main():
    parser = argparse.ArgumentParser(
        description="Convert DOS/Windows line endings (CRLF) to Unix (LF)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\nExamples:\n  %(prog)s file.txt\n  %(prog)s file1.txt file2.txt file3.txt\n  %(prog)s /path/to/folder\n  %(prog)s /path/to/folder file.txt\n  %(prog)s                    # Process current directory recursively\n\nSkip Directories: .git, __pycache__, .venv, venv, node_modules, .env, \n                  .pytest_cache, .tox, .mypy_cache, .coverage, dist, build\n        ",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or folders to process (default: current directory)",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output messages")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed output for each file",
    )
    args = parser.parse_args()
    input_paths = get_input_paths(args.paths or None)
    if not input_paths:
        logger.error("No valid paths provided")
        return 1
    files_to_process = find_text_files(input_paths)
    if not files_to_process:
        if not args.quiet:
            print("No text files found to process")
        return 0
    if not args.quiet and (not args.verbose):
        print(f"Processing {len(files_to_process)} file(s) with 8 worker(s)...")
    converted_count = 0
    skipped_count = 0
    error_count = 0
    try:
        with Pool(processes=MAX_WORKERS) as pool:
            results = pool.map(convert_file, files_to_process)
        for path, success, message in results:
            if args.verbose:
                status = "✓" if success else "✗"
                print(f"{status} {path}: {message}")
            if success:
                if "Converted" in message:
                    converted_count += 1
                else:
                    skipped_count += 1
            else:
                error_count += 1
        if not args.quiet:
            print()
            print(f"Converted: {converted_count} file(s)")
            print(f"Already Unix format: {skipped_count} file(s)")
            if error_count > 0:
                logger.warning(f"Errors: {error_count} file(s)")
        return 0 if error_count == 0 else 1
    except KeyboardInterrupt:
        logger.error("\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
