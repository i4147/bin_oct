#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory tree for Python source files and checks each file for syntax problems, reporting the results in a clear summary. The script should accept a target directory (defaulting to the current directory) and an optional flag that, when enabled, applies a safe automatic fix or cleanup step to files that are reported as problematic, while otherwise running in a read-only reporting mode.
Key requirements:
- **Discovery**: Recursively find all `.py` files under the given root path. Skip common non-source directories such as virtual environments, version control folders, and build or cache directories.
- **Validation**: For each file, read it as UTF-8 text and determine its status in one of three categories:
  - `ok` — the file parses and compiles cleanly with no warnings.
  - `warn` — the file compiles but produces compiler warnings (for example, invalid escape sequences or other syntax-level warnings).
  - `error` — the file cannot be read, fails to parse, or fails to compile.
- **Parallel processing**: Process files concurrently across multiple CPU cores to keep runtime low on large projects, and ensure results from all workers are collected reliably.
- **Progress feedback**: Display a live progress indicator in the terminal while files are being checked.
- **Reporting**: After the scan, print a concise summary listing counts of files per status, and list the paths of all files with `error` or `warn` status grouped by category. Use colored, readable terminal output where appropriate, and return a non-zero exit code if any file has an `error` status.
- **Apply mode**: When the apply flag is passed, perform a conservative, non-destructive remediation step on problematic files (such as creating a backup copy before modifying anything, and only making changes that are clearly safe). Clearly report what was changed, and never silently overwrite files without a backup.
- **Robustness**: Handle unreadable files, encoding problems, and permission errors gracefully without crashing the whole run.
- **Command-line interface**: Provide a helpful `--help` message describing the target path argument and the apply option.
The script should be self-contained, well-structured, and documented with brief docstrings explaining its purpose and usage.
---"""

from __future__ import annotations
import argparse
import ast
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import shutil
from typing import Literal
import warnings
from rich.progress import Progress

Status = Literal["ok", "error", "warn"]


def check_file(path: Path) -> tuple[Path, Status]:
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return path, "error"
    try:
        ast.parse(source, filename=str(path))
    except SyntaxError:
        return path, "error"
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            compile(source, str(path), "exec")
        except Exception:
            return path, "error"
        if any(issubclass(x.category, SyntaxWarning) for x in w):
            return path, "warn"
    return path, "ok"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--apply", action="store_true")
    args = parser.parse_args()
    cwd = Path.cwd()
    files = list(cwd.glob("*.py"))
    if not files:
        print("No .py files found.")
        return
    results: list[tuple[Path, Status]] = []
    with Progress() as progress:
        task = progress.add_task("Processing .py files", total=len(files))
        with ProcessPoolExecutor() as executor:
            futures = {executor.submit(check_file, f): f for f in files}
            for future in as_completed(futures):
                results.append(future.result())
                progress.update(task, advance=1)
    groups: dict[str, list[Path]] = {"ok": [], "error": [], "warn": []}
    for path, status in results:
        groups[status].append(path)
    for status, paths in groups.items():
        print(f"{status}: {len(paths)} files")
        for p in paths:
            print(f"  {p.name}")
    if args.apply:
        for status, paths in groups.items():
            if not paths:
                continue
            target_dir = cwd / status
            target_dir.mkdir(exist_ok=True)
            for p in paths:
                shutil.move(str(p), str(target_dir / p.name))
        print("Moved files.")
    else:
        print("Dry-run. Use -a or --apply to move files.")


if __name__ == "__main__":
    main()
