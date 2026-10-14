#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans a directory tree for Python source files and toggles the way the `re` regular-expression module is imported in each file. In its default mode, the script should replace the standard-library `re` import line with an equivalent import of the third-party `regex` package aliased as `re`, so that the rest of each file continues to work unchanged. In reverse mode, it should undo that change, restoring the standard `import re` form.
The script should accept a root directory path (defaulting to the current directory) and a flag that selects the reverse direction. It should locate every `.py` file under the root, process them in parallel using a pool of about eight worker processes to keep throughput high on large trees, and rewrite only the first matching import statement found at the start of a line in each file, leaving all other content, line endings, and encoding intact (UTF-8).
Each file should be handled independently: if a file cannot be read due to an operating-system error, the script should record a clear error message naming the file and the reason, and continue processing the remaining files without crashing. Files without a matching import should be left untouched and not rewritten.
Logging should be handled through a structured logging facility, reporting which files were modified, which were skipped, and any errors encountered, with a final summary of counts for updated, unchanged, and failed files. The script should exit with a non-zero status code if any file failed to process, and zero otherwise. Provide a clear command-line interface with help text describing the directory argument and the reverse option.
---"""

from __future__ import annotations
import argparse
from multiprocessing.pool import AsyncResult, Pool
from pathlib import Path
import re
from typing import TYPE_CHECKING, Final, TypeAlias
from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Sequence
POOL_WORKERS: Final[int] = 8
POOL_METHODS: Final[tuple[str, ...]] = (
    "map",
    "starmap",
    "imap_unordered",
    "apply_async",
)
NORMAL_IMPORT: Final[str] = r"^import re\b"
REGEX_IMPORT: Final[str] = r"^import regex as re\b"
FileResult: TypeAlias = str | None
UpdateTask: TypeAlias = tuple[Path, bool]


def get_pyfiles(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if p.is_file()]


def update_file(file_path: Path, reverse: bool = False) -> FileResult:
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    except OSError as exc:
        return f"Error processing {file_path}: {exc}"
    new_lines: list[str] = []
    changed = False
    search_pat = REGEX_IMPORT if reverse else NORMAL_IMPORT
    replacement = "import re" if reverse else "import regex as re"
    for line in lines:
        if not changed and re.match(search_pat, line):
            new_lines.append(re.sub(search_pat, replacement, line))
            changed = True
        else:
            new_lines.append(line)
    if not changed:
        return None
    try:
        file_path.write_text("".join(new_lines), encoding="utf-8")
    except OSError as exc:
        return f"Error processing {file_path}: {exc}"
    return f"Updated: {file_path}"


def _update_file_tuple(task: UpdateTask) -> FileResult:
    path, reverse = task
    return update_file(path, reverse)


def _run_pool(tasks: Sequence[UpdateTask], method: str) -> list[FileResult]:
    with Pool(processes=POOL_WORKERS) as pool:
        if method == "map":
            return pool.map(_update_file_tuple, tasks)
        if method == "starmap":
            return pool.starmap(update_file, tasks)
        if method == "imap_unordered":
            return list(pool.imap_unordered(_update_file_tuple, tasks))
        if method == "apply_async":
            async_results: list[AsyncResult[FileResult]] = [
                pool.apply_async(_update_file_tuple, (task,)) for task in tasks
            ]
            return [result.get() for result in async_results]
    msg = f"Unsupported pool method: {method}"
    raise ValueError(msg)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recursively swap 'import re' with 'import regex as re'")
    parser.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        help="Reverse the replacement (regex as re -> re)",
    )
    parser.add_argument(
        "--pool-method",
        choices=POOL_METHODS,
        default="map",
        help="Multiprocessing pool method to use for updates.",
    )
    return parser.parse_args()


def main() -> int:
    args: argparse.Namespace = parse_args()
    reverse: bool = bool(args.reverse)
    pool_method: str = args.pool_method
    cwd = Path.cwd()
    py_files = get_pyfiles(cwd)
    logger.info(f"Scanning {len(py_files)} files...")
    tasks: list[UpdateTask] = [(path, reverse) for path in py_files]
    if not tasks:
        logger.info("Task complete. Files modified: 0")
        return 0
    results = _run_pool(tasks, pool_method)
    updates: list[str] = [r for r in results if r is not None]
    for msg in updates:
        logger.info(msg)
    logger.info(f"Task complete. Files modified: {len(updates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
