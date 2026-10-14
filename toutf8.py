#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans a directory tree and converts all text files to UTF-8 encoding in place, using parallel processing to speed up the work across many files.
The script should accept a target directory path as a command-line argument and walk through all files beneath it. For each file, it should first determine whether the file is binary or unsupported; such files must be skipped and reported as skipped. For text files, it should sample the beginning of the file to automatically detect its character encoding, falling back to UTF-8 when detection is inconclusive or fails. Files already in UTF-8 should be left untouched and reported as such. Files in any other detected encoding should be decoded using that encoding and rewritten as UTF-8, replacing the original content.
Processing should run concurrently with a bounded number of worker processes (around eight). Each file's outcome should be collected and returned as a result containing the file path, whether a conversion succeeded or was needed, and a human-readable status message describing what happened, including any errors encountered. Errors on individual files must not stop the overall run.
At the end, the script should log progress and a summary to the console, reporting counts of converted, already-UTF-8, skipped, and failed files, and optionally list the failures in detail. Logging should use a structured logging library, and the script should exit with a clear status code reflecting whether any failures occurred. Include a clear usage message and handle invalid or missing directory arguments gracefully with informative error messages.
---"""

from __future__ import annotations
import argparse
from multiprocessing import Pool
from pathlib import Path
from typing import TYPE_CHECKING, Final
import chardet
from dh import get_nobinary, is_binary
from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Generator
    from multiprocessing.pool import AsyncResult
MAX_WORKERS: Final[int] = 8
SAMPLE_SIZE: Final[int] = 100_000
ConvertResult = tuple[Path, bool, str]


def detect_encoding(file_path: Path) -> str:
    try:
        with file_path.open("rb") as f:
            raw_data: bytes = f.read(SAMPLE_SIZE)
        result: dict[str, str | float | None] = chardet.detect(raw_data)
        encoding: str | float | None = result.get("encoding")
        if isinstance(encoding, str) and encoding:
            return encoding
        return "utf-8"
    except Exception:
        return "utf-8"


def convert_file(file_path: Path) -> ConvertResult:
    try:
        if is_binary(file_path):
            return file_path, False, "Skipped (binary/unsupported)"
        encoding: str = detect_encoding(file_path)
        if encoding.lower() == "utf-8":
            return file_path, True, "Already UTF8"
        with file_path.open("r", encoding=encoding, errors="replace") as f:
            content: str = f.read()
        with file_path.open("w", encoding="utf-8") as f:
            f.write(content)
        return file_path, True, f"Converted from {encoding}"
    except Exception as exc:
        return file_path, False, f"Error: {exc!s}"


def collect_files(paths: list[str]) -> Generator[Path, None, None]:
    for path_str in paths:
        path: Path = Path(path_str).resolve()
        if path.is_file():
            yield path
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file():
                    yield child
        else:
            logger.warning(f"⚠ {path} not found")


def main() -> int:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Convert non-UTF8 files to UTF8 encoding (in-place)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python script.py                    # Process current directory\n"
            "  python script.py ./src ./docs       # Process specific directories\n"
            "  python script.py file.txt dir/      # Process file and directory"
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to process (default: current directory)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed output for each file",
    )
    args: argparse.Namespace = parser.parse_args()
    input_paths: list[str] = list(args.paths) if args.paths else ["."]
    cwd: Path = Path.cwd()
    if args.paths:
        files: list[Path] = list(collect_files(input_paths))
    else:
        files = list(get_nobinary(cwd))
    if not files:
        print("No files to process.")
        return 0
    print(f"Processing {len(files)} file(s) with {MAX_WORKERS} worker(s)...\n")
    converted: int = 0
    skipped: int = 0
    errors: int = 0
    with Pool(processes=MAX_WORKERS) as pool:
        async_results: list[AsyncResult[ConvertResult]] = [pool.apply_async(convert_file, (f,)) for f in files]
        for async_res in async_results:
            file_path, success, message = async_res.get()
            if args.verbose:
                status: str = "✓" if success else "✗"
                try:
                    rel: Path = file_path.relative_to(cwd)
                except ValueError:
                    rel = file_path
                print(f"{status} {rel} - {message}")
            if success:
                if "Already UTF8" in message or "Skipped" in message:
                    skipped += 1
                else:
                    converted += 1
            else:
                errors += 1
    print("=" * 40)
    print("Summary:")
    print(f"  Converted: {converted}")
    print(f"  Skipped:   {skipped}")
    print(f"  Errors:    {errors}")
    print("=" * 40)
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
