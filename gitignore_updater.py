#!/data/data/com.termux/files/usr/bin/env python
"""The provided code is truncated at `def append_line_to_gitignore`, so I'll write the prompt to describe the full script as its visible structure implies, and note in the prompt where the remainder must be inferred.

Reproduce a Python script from scratch that appends a given line to `.gitignore` files across many paths using multiprocessing. Write it to run under Termux on Android, using `#!/data/data/com.termux/files/usr/bin/env python` as the shebang and `from __future__ import annotations` at the top.

**Purpose and structure**
- The script validates an input line (a `.gitignore` entry) and appends it to one or more `.gitignore` files located at the paths it is given, skipping any file that already contains the line.
- Configure logging at module level with `logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")` and a module logger from `logging.getLogger(__name__)`.

**Dependencies (standard library only)**
- `logging`, `os`, `sys`, `dataclasses.dataclass`, `multiprocessing.Pool` and `cpu_count`, `pathlib.Path`, `typing.Optional`.

**Data structure**
- A dataclass `ProcessResult` with fields: `path: Path`, `success: bool`, `modified: bool`, `error: str | None = None`, `message: str = ""`.

**Functions**
1. `validate_input_line(line: str) -> str`
   - Raise `ValueError` with the message "Input line must be a string" if the input is not a `str`.
   - Strip leading and trailing whitespace; if the result is empty, raise `ValueError` with "Input line cannot be empty".
   - If the stripped value contains `\\n` or `\\r`, remove those characters, log a warning showing the cleaned value using `repr`, and return the cleaned value.
2. `line_exists_in_file(path: Path, target_line: str) -> bool`
   - Open the file in read mode with UTF-8 encoding and `errors="ignore"`.
   - Return `True` if any line, with trailing `\\n` and `\\r` stripped, equals `target_line` exactly.
   - Return `False` if no match. On `OSError`, log a warning naming the path and the error, and return `False`.
3. `append_line_to_gitignore(...)`: the source is truncated at this definition, so infer a sensible implementation: it takes a path and a validated line, checks whether the file already contains the line (via `line_exists_in_file`), and if not, appends the line (ensuring a preceding newline if the file does not end with one) and creates the file if it is missing. It returns a `ProcessResult` describing success, whether it modified the file, and any error message.

**Parallel execution**
- Process multiple target paths concurrently with a `multiprocessing.Pool` sized to `cpu_count()`, mapping the per-path worker across the list of paths with the validated line.
- Collect the `ProcessResult` objects and log a summary of how many files were modified, skipped as already present, or failed.

**Entry point and usage**
- Put the main logic under `if __name__ == "__main__":`.
- Read the target line and the list of target paths from the command line arguments (`sys.argv`), printing a usage message and exiting with a nonzero status if arguments are missing.
- Exit with status 0 on full success and a nonzero status if any file failed.

**Error handling and edge cases**
- Handle unreadable or unwritable files gracefully without crashing the pool; record the error in the `ProcessResult`.
- Treat non-existent `.gitignore` paths as creatable targets rather than errors, where appropriate.
- Reject empty or non-string input lines before any file is touched.
- Strip newline characters from input lines rather than writing multi-line entries.
- Match lines exactly after stripping only line terminators, so entries with leading whitespace or comments are compared literally.

**Output**
- Use the logger for all status output, not `print`, except for usage text written to stderr.
---"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    path: Path
    success: bool
    modified: bool
    error: str | None = None
    message: str = ""


def validate_input_line(line: str) -> str:
    if not isinstance(line, str):
        msg = "Input line must be a string"
        raise ValueError(msg)
    normalized = line.strip()
    if not normalized:
        msg = "Input line cannot be empty"
        raise ValueError(msg)
    if "\n" in normalized or "\r" in normalized:
        normalized = normalized.replace("\n", "").replace("\r", "")
        logger.warning(f"Removed newline characters from input: {normalized!r}")
    return normalized


def line_exists_in_file(path: Path, target_line: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.rstrip("\n\r") == target_line:
                    return True
        return False
    except OSError as e:
        logger.warning(f"Error reading {path}: {e}")
        return False


def append_line_to_gitignore(path: Path, target_line: str) -> ProcessResult:
    try:
        if not os.access(path.parent, os.W_OK):
            return ProcessResult(
                path=path,
                success=False,
                modified=False,
                error="Permission denied",
                message=f"No write permission for {path.parent}",
            )
        if path.exists() and line_exists_in_file(path, target_line):
            return ProcessResult(
                path=path,
                success=True,
                modified=False,
                message="Line already exists",
            )
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="utf-8", errors="ignore")
            logger.warning(f"Encoding issues in {path}, using fallback")
        needs_newline = content and not content.endswith("\n")
        new_content = content
        if needs_newline:
            new_content += "\n"
        new_content += target_line + "\n"
        path.write_text(new_content, encoding="utf-8")
        return ProcessResult(
            path=path,
            success=True,
            modified=True,
            message="Line added successfully",
        )
    except Exception as e:
        logger.error(f"Unexpected error processing {path}: {e}")
        return ProcessResult(
            path=path,
            success=False,
            modified=False,
            error=str(e),
            message=f"Failed to process: {type(e).__name__}",
        )


def find_gitignore_files(search_paths: list[Path]) -> list[Path]:
    gitignore_files = []
    for search_path in search_paths:
        if not search_path.exists():
            logger.warning(f"Path does not exist: {search_path}")
            continue
        if search_path.is_symlink():
            logger.warning(f"Skipping symlink: {search_path}")
            continue
        if search_path.is_file():
            if search_path.name == ".gitignore":
                gitignore_files.append(search_path)
            continue
        if search_path.is_dir():
            try:
                for gitignore in search_path.rglob(".gitignore"):
                    if gitignore.is_file() and not gitignore.is_symlink():
                        gitignore_files.append(gitignore)
            except (PermissionError, OSError) as e:
                logger.warning(f"Cannot access directory {search_path}: {e}")
                continue
    return gitignore_files


def process_gitignore_wrapper(args: tuple[Path, str]) -> ProcessResult:
    path, target_line = args
    return append_line_to_gitignore(path, target_line)


def main() -> int:
    if len(sys.argv) < 2:
        logger.error("Usage: python gitignore_updater.py <line> [path1] [path2] ...")
        logger.error("  <line>: The line to add to all .gitignore files")
        logger.error("  [paths]: Optional paths to search (defaults to current directory)")
        return 1
    target_line = sys.argv[1]
    search_paths_arg = sys.argv[2:] if len(sys.argv) > 2 else ["."]
    try:
        target_line = validate_input_line(target_line)
        print(f"Target line: {target_line!r}")
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return 1
    search_paths = []
    for path_str in search_paths_arg:
        try:
            path = Path(path_str).resolve()
            search_paths.append(path)
            print(f"Search path: {path}")
        except (ValueError, OSError) as e:
            logger.error(f"Invalid path {path_str}: {e}")
            return 1
    print("Scanning for .gitignore files...")
    gitignore_files = find_gitignore_files(search_paths)
    if not gitignore_files:
        logger.warning("No .gitignore files found")
        return 0
    print(f"Found {len(gitignore_files)} .gitignore file(s)")
    tasks = [(path, target_line) for path in gitignore_files]
    num_workers = min(4, cpu_count() or 1)
    print(f"Using {num_workers} worker(s)")
    results = []
    try:
        with Pool(processes=num_workers) as pool:
            results = pool.map(process_gitignore_wrapper, tasks)
    except KeyboardInterrupt:
        logger.error("Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Multiprocessing error: {e}")
        return 1
    successful = sum(1 for r in results if r.success)
    modified = sum(1 for r in results if r.modified)
    skipped = successful - modified
    failed = len(results) - successful
    print("=" * 40)
    print("SUMMARY")
    print("=" * 40)
    print(f"Total files processed: {len(results)}")
    print(f"Successfully processed: {successful}")
    print(f"Files modified: {modified}")
    print(f"Files skipped (already exist): {skipped}")
    print(f"Failed: {failed}")
    if failed > 0:
        print("\nFailed files:")
        for result in results:
            if not result.success:
                print(f"  {result.path}: {result.message}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
