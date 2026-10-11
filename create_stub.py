#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python script that generates `.pyi` type stub files for Python source files by invoking the external `stubgen` tool (from mypy). Requirements:

**Purpose:** A command-line utility that batch-generates stub files (`.pyi`) for Python modules, skipping any module that already has a stub.

**Shebang and imports:** Start with a Termux-style shebang (`#!/data/data/com.termux/files/usr/bin/env python`). Enable postponed annotations via `from __future__ import annotations`. Use only the standard library modules `subprocess`, `sys`, and `pathlib.Path`, plus two helpers imported from a local module named `dh`: `get_files` (scans a directory for files with given extensions) and `mpf` (runs a function over a list of items in parallel, multi-process style). Do not reimplement these helpers.

**Per-file function (`process_file`, takes a path, returns None):**
- Convert the argument to a `Path`, and print `processing <filename>` (name only, not full path).
- Compute the stub path by replacing the suffix with `.pyi`.
- If the stub already exists, print `[SKIP] <filename> (stub already exists)` and return without running anything.
- Otherwise run the external command `stubgen <path>` via `subprocess.run` with `capture_output=True`, `text=True`, and `check=True`, inside a try block.
- On success, print `[OK] <filename>`.
- On `subprocess.CalledPro[ERROR] <filename>` followed on the next line by an indented (two-space) copy of the captured stderr. Do not re-raise; continue gracefully.
- Note: the function should not raise if `stubgen` is missing in a way that is not a CalledProcessError; keep behavior limited to the described handling unless a plain implementation naturally does otherwise.

**Main function (`main`, returns None):**
- Take the current working directory via `Path.cwd()`.
- Read command-line arguments from `sys.argv[1:]`. If any are given, convert each to a `Path`; otherwise call `get_files(cwd, ext=[".py"])` to discover all Python files in the current directory.
- If exactly one file is present, call `process_file` on it directly and then call `sys.exit(0)`.
- Otherwise call `mpf(process_file, files)` to process all files (possibly in parallel).
- After processing, collect every file whose `.pyi` counterpart does not exist. If that list is non-empty, print a blank line, then `Files without generated stubs:`, then one line per file in the form ` - <filename>` (name only).
- If there are no stubless files, print nothing extra.

**Entry point:** Under the standard `if __name__ == "__main__":` guard, call `main()` wrapped as `raise SystemExit(main())`.

**Style:** Use type annotations on function signatures (`-> None`, and `path` left untyped in `process_file`). Keep the code concise, with f-strings for output and no extra logging frameworks, no classes, and no third-party dependencies beyond the local `dh` module and the external `stubgen` executable. Use no docstrings beyond what is minimal, and avoid unnecessary comments.

**Usage notes to honor:** It is run from the directory containing target files, or with explicit file paths as arguments. Output is printed to stdout only. Errors from stubgen are reported inline and do not abort the batch.
---"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from dh import get_files, mpf


def process_file(path) -> None:
    path = Path(path)
    print(f"processing {path.name}")
    stubfile = path.with_suffix(".pyi")
    if stubfile.exists():
        print(f"[SKIP] {path.name} (stub already exists)")
        return
    cmd = ["stubgen", str(path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"[OK] {path.name}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {path.name}")
        print(f"  {e.stderr}")


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".py"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(0)
    mpf(process_file, files)
    stubless = []
    for f in files:
        stubpath = f.with_suffix(".pyi")
        if not stubpath.exists():
            stubless.append(f)
    if stubless:
        print("\nFiles without generated stubs:")
        for k in stubless:
            print(f" - {k.name}")


if __name__ == "__main__":
    raise SystemExit(main())
