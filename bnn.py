#!/data/data/com.termux/files/usr/bin/env python
"""Create tells an AI coding agent how to build a Python command-line tool for bulk find-and-replace across files, using parallel processing, with the details below.

The tool should be a single Python script that runs under Termux on Android (shebang pointing to the Termux Python path). It uses `from __future__ import annotations`, `argparse`, `logging`, `shutil`, `tempfile`, `dataclasses`, `pathlib`, `typing.TYPE_CHECKING` (with `collections.abc.Generator` imported only under that guard), and `joblib.Parallel` / `delayed` for parallel execution. Logging is configured at INFO level with the format `LEVELNAME (padded to 8) message`, using a module-level logger named after `__name__`.

The script defines a dataclass `FileStats` with fields: `path` (Path), `success` (bool), `replacements` (int, default 0), `original_size` (int, default 0), `new_size` (int, default 0), and `error_msg` (optional str, default None). Its `__str__` shows the path relative to the current working directory. On failure it prints a cross mark, the relative path, and the error message. On success it prints a check mark, the relative path, the replacement count, and a signed byte-size delta in parentheses, or "(no size change)" when the delta is zero.

Write a helper `is_text_file(path, max_sample=8192)` that reads up to `max_sample` bytes in binary mode and returns True only if no NUL byte is present; it returns False on any OSError.

Write `should_process_file(path, text_only=True)` that returns False for directories and symlinks, and when `text_only` is set, returns False for files that fail the text check.

Continue the script with the remaining logic the original implies: a generator (typed with the guarded `Generator` import) that walks the target directory tree and yields candidate files, a per-file processing function that performs the replacement and returns a `FileStats`, and a `main` that parses arguments and drives processing with `joblib.Parallel(delayed(...))`. Use `shutil` and `tempfile` for safe writes: write the modified content to a temporary file in the same directory and then move it over the original, so a failure never leaves a partially written file. Wrap each file's processing in try/except so that an exception produces a `FileStats` with `success=False` and the message in `error_msg` rather than aborting the whole run. Read files with explicit encoding handling and treat decode failures as errors for that file.

Command-line interface: the script takes a search string and a replacement string as positional arguments, plus optional arguments for the root directory (defaulting to the current directory), a flag to include binary files (text-only by default), a worker count for parallelism (with a sensible default such as -1 for all cores), and a dry-run flag that reports what would change without writing anything. Include `--help` text describing each argument.

Execution details: the script should be runnable directly as an executable with the Termux shebang. After processing, it prints one line per file using `FileStats.__str__`, then a summary of total files scanned, files changed, total replacements, and failures. Exit with status 0 if all files succeeded and non-zero if any failed. Handle edge cases: empty search strings should be rejected with a clear message, missing root directories should produce an error and non-zero exit, files that cannot be read or written should be reported and skipped, and zero matches should produce no file writes at all. Preserve file permissions when replacing files. Log warnings for skipped files and errors for failed ones through the module logger.

Output only the script's functionality as described; write the complete script in a single file with no external dependencies beyond the standard library and joblib.
---"""

from __future__ import annotations

import argparse
import logging
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from joblib import Parallel, delayed

if TYPE_CHECKING:
    from collections.abc import Generator
logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class FileStats:
    path: Path
    success: bool
    replacements: int = 0
    original_size: int = 0
    new_size: int = 0
    error_msg: str | None = None

    def __str__(self) -> str:
        relpath = self.path.relative_to(Path.cwd())
        if not self.success:
            return f"✗ {relpath}: {self.error_msg}"
        size_delta = self.new_size - self.original_size
        size_change = f"({size_delta:+d} bytes)" if size_delta != 0 else "(no size change)"
        return f"✓ {relpath}: {self.replacements} replacements {size_change}"


def is_text_file(path: Path, max_sample: int = 8192) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(max_sample)
            return b"\x00" not in chunk
    except OSError:
        return False


def should_process_file(path: Path, text_only: bool = True) -> bool:
    if path.is_dir() or path.is_symlink():
        return False
    return not (text_only and not is_text_file(path))


def collect_files(inputs: list[str | Path]) -> Generator[Path, None, None]:
    for input_path in inputs:
        path = Path(input_path).resolve()
        if path.is_file():
            if should_process_file(path):
                yield path
        elif path.is_dir():
            for path in path.rglob("*"):
                if should_process_file(path):
                    yield path
        else:
            logger.warning(f"Path not found: {path}")


def process_file_chunked(
    path: Path,
    chunk_size: int = 1024 * 1024,
) -> FileStats:
    stats = FileStats(path=path, success=True)
    try:
        stats.original_size = path.stat().st_size
        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            encoding="utf-8",
            newline="",
        ) as temp_file:
            temp_path = Path(temp_file.name)
            try:
                total_replacements = 0
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    buffer = ""
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            if buffer:
                                new_buffer, count = (
                                    buffer.replace("\\n", "\n"),
                                    buffer.count("\\n"),
                                )
                                temp_file.write(new_buffer)
                                total_replacements += count
                            break
                        buffer += chunk
                        last_safe_pos = len(buffer)
                        if buffer.endswith("\\"):
                            last_safe_pos -= 1
                        processable = buffer[:last_safe_pos]
                        buffer = buffer[last_safe_pos:]
                        new_content, count = (
                            processable.replace("\\n", "\n"),
                            processable.count("\\n"),
                        )
                        temp_file.write(new_content)
                        total_replacements += count
                stats.replacements = total_replacements
            except Exception as e:
                temp_path.unlink()
                raise
            temp_path.chmod(path.stat().st_mode)
        stats.new_size = temp_path.stat().st_size
        shutil.move(str(temp_path), str(path))
    except UnicodeDecodeError as e:
        stats.success = False
        stats.error_msg = f"Encoding error: {e}"
        if temp_path.exists():
            temp_path.unlink()
    except PermissionError as e:
        stats.success = False
        stats.error_msg = f"Permission denied: {e}"
        if temp_path.exists():
            temp_path.unlink()
    except Exception as e:
        stats.success = False
        stats.error_msg = f"Error: {type(e).__name__}: {e}"
        if temp_path.exists():
            temp_path.unlink()
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Replace literal \\n with actual newlines in files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s file.txt
  %(prog)s dir1 dir2 file.txt
  %(prog)s --workers 8 --chunk-size 2M dir/
        """,
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Files or directories to process (default: current directory)",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)",
    )
    parser.add_argument(
        "-c",
        "--chunk-size",
        default="1M",
        help="Chunk size for streaming (default: 1M, e.g., 512K, 2M)",
    )
    parser.add_argument(
        "--include-binary",
        action="store_true",
        help="Process binary files (not recommended)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed logging")
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    chunk_size_str = args.chunk_size.upper()
    multipliers = {"K": 1024, "M": 1024**2, "G": 1024**3}
    try:
        if chunk_size_str[-1] in multipliers:
            chunk_size = int(chunk_size_str[:-1]) * multipliers[chunk_size_str[-1]]
        else:
            chunk_size = int(chunk_size_str)
    except ValueError:
        logger.error(f"Invalid chunk size: {args.chunk_size}")
        return 1
    if not args.inputs:
        inputs = [Path.cwd()]
        print("No inputs provided, processing current directory recursively")
    else:
        inputs = args.inputs
    files = list(collect_files(inputs))
    if not files:
        logger.warning("No files found to process")
        return 0
    print(f"Found {len(files)} files to process")
    print(f"Starting parallel processing with {args.workers} workers")
    results = Parallel(n_jobs=args.workers, verbose=0)(
        delayed(process_file_chunked)(path, chunk_size) for path in files
    )
    print("\n" + "=" * 40)
    print("PROCESSING RESULTS")
    print("=" * 40)
    successful = 0
    total_replacements = 0
    total_size_change = 0
    for stats in results:
        print(stats)
        if stats.success:
            successful += 1
            total_replacements += stats.replacements
            total_size_change += stats.new_size - stats.original_size
    failed = len(results) - successful
    print("=" * 40)
    print(f"Summary: {successful} succeeded, {failed} failed out of {len(results)} files")
    print(f"Total replacements: {total_replacements}")
    print(f"Total size change: {total_size_change:+d} bytes")
    print("=" * 40 + "\n")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
