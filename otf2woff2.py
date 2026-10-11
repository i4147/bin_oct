#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python script that converts font files to WOFF2 format. Requirements:

**Purpose:** A command-line utility that converts font files (primarily OpenType `.otf` files) into WOFF2 web font format, saving each output alongside the input file with the same base name and a `.woff2` extension.

**Target environment:** Termux on Android. The script begins with a shebang pointing to the Termux Python interpreter path (`/data/data/com.termux/files/usr/bin/env python`). Use `from __future__ import annotations` for forward-compatible type hints.

**Dependencies:**
- The standard library modules `sys` and `pathlib`.
- `fontTools.ttLib.TTFont` from the fontTools package, used to load fonts and save them with the WOFF2 flavor. WOFF2 output requires the Brotli compression library to be available alongside fontTools.
- A local helper module named `dh` providing four utilities: `cprint` (colored/console-styled printing used for error messages), `get_files` (collects files in a directory filtered by extension list), `mpf` (multiprocess-style parallel mapping of a function over a list of items), and `unique_path` (returns a non-colliding path by altering the filename when the target already exists). Reproduce these imports exactly as named.

**Behavior and logic:**

1. Capture the current working directory at module load time as a module-level variable.

2. `process_file(path)` takes a single file path:
   - Coerce the argument to a `Path`.
   - Compute the target path by replacing the suffix with `.woff2`.
   - If a target already exists and is non-empty (size greater than zero), replace the target with a unique alternative path returned by `unique_path`. An existing empty file is overwritten rather than renamed.
   - Inside a try block, load the font with `TTFont`, set its `flavor` attribute to `"woff2"`, and save it to the target path.
   - On success, print a message in the form `<filename> converted.` using the original file's name (not the full path).
   - On any exception (use a bare except), call `cprint` with a message in the form `error convering <filename>` (preserve the original misspelling "convering" exactly). Do not re-raise; failures are reported and processing continues.

3. `main()` handles command-line dispatch:
   - Read arguments from `sys.argv[1:]`.
   - If arguments are provided, convert each to a `Path`. If none are provided, call `get_files` on the current working directory filtered to `.otf` extensions.
   - If exactly one file is in the list, process it directly with `process_file` and then exit with status code 1 via `sys.exit(1)`. Note this exit happens regardless of success or failure, and is an intentional quirk to preserve.
   - Otherwise (zero or multiple files), run `process_file` over the entire list using `mpf` for parallel execution.
   - If the list is empty, the call to `mpf` with an empty list should be allowed to proceed naturally without special handling.

4. The `__main__` guard invokes `main()` and wraps it in `raise SystemExit(...)`, so the return value of `main` (None) is passed through the exit mechanism.

**Edge cases to honor:**
- No arguments and no `.otf` files in the working directory: produces no conversions.
- Arguments that point to non-existent or non-font files: the bare except catches the failure and prints the error message.
- Output name collisions: handled by the non-empty existence check and `unique_path`.
- Single-file invocation exits with code 1 even on success; multi-file invocation exits normally.

**Output and I/O:** Only console output. Success lines go to standard output via `print`; error lines go through `cprint`. Converted `.woff2` files are written next to the source files (or to the unique alternative path). No other files are modified.

**Style:** Keep the script concise, with type-annotated function signatures (`-> None`, `path: Path`), short docstring-free functions, and a blank-line-separated layout consistent with a small utility script.
---"""

from __future__ import annotations

import sys
from pathlib import Path

from dh import cprint, get_files, mpf, unique_path
from fontTools.ttLib import TTFont

cwd = Path.cwd()


def process_file(path: Path) -> None:
    path = Path(path)
    woff2_path = path.with_suffix(".woff2")
    if woff2_path.exists() and woff2_path.stat().st_size:
        woff2_path = unique_path(woff2_path)
    try:
        font = TTFont(path)
        font.flavor = "woff2"
        font.save(woff2_path)
        print(f"{path.name} converted.")
    except:
        cprint(f"error convering {path.name}")


def main() -> None:
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".otf"])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(1)
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
