#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python 3 command-line script with the following specification:

Build a Python 3 command-line utility that batch-formats source files using the clang-format tool, with the LLVM style, and reports the change in disk usage. It is intended for a Termux (Android) environment, so the shebang line should point to the Termux Python interpreter path (/data/data/com.termux/files/usr/bin/env python).

Requirements to implement:

**Imports and dependencies**
- Use `from __future__ import annotations` at the top.
- Use the standard library `sys` and `pathlib.Path`.
- Import these helpers from a local module named `dh`: `cprint` (colored console printing), `fsz` (format a byte count as a human-readable size string), `get_files` (recursively collect files under a directory filtered by extension), `gsz` (get the size in bytes of a file or directory), `mpf` (run a function over a list of items in parallel, e.g., a multiprocess map), `rrs` (report or record the size change for a single file given its before and after sizes), and `runcmd` (run an external command, with a `show_output` flag controlling whether its output is displayed).
- The external dependency is the `clang-format` executable, which must be on PATH.

**Configuration**
- A module-level list of file extensions to process: `.java`, `.c`, `.cpp`, `.cxx`, `.cc`, `.h`, `.hh`, `.hpp`, `.hxx`, `.js`, `.json`.

**process_file(path)**
- Convert the argument to a `Path`.
- Record the file size before formatting using `gsz`.
- Run `clang-format -i --style=LLVM <path>` via `runcmd` with output suppressed.
- On success, record the size after formatting and pass both sizes to `rrs` along with the path.
- Free the local size variables, then return. Any exception raised during the process (including the external command failing) must be silently swallowed so that one bad file does not stop the batch; the function returns `None` in all cases.

**main()**
- Build the file list: if command-line arguments are given (excluding the script name), convert each to a `Path`; otherwise recursively gather files from the current working directory filtered by the extension list via `get_files`.
- Record the total size of the current working directory before processing using `gsz`.
- Print the count with `cprint` as "N files found" in cyan.
- If exactly one file is found, process it directly with `process_file` and exit with status code 1 (note: this exit code is intentional in the original behavior).
- Otherwise, process all files in parallel via `mpf(process_file, files)`.
- Re-measure the current working directory size, compute the difference as before minus after, and print `space change: ` followed by the value formatted with `fsz` (a negative value indicates the directory grew).
- When run as the main program, call `main()` and raise `SystemExit` with its return value.

**Behavior and edge cases to preserve**
- Files that are passed explicitly on the command line are processed regardless of extension.
- Zero files found: the count prints as 0, and the script proceeds to the parallel step with an empty list and then prints the space change.
- Single-file mode always exits with status 1 even on success, and does not print the space change line.
- Failures in individual formatting operations are ignored silently.
- Use short variable names and minimal comments in the same terse style; the code is intended as a compact utility script.

Deliver the complete script as a single file with the Termux shebang and no additional commentary.
---"""

from __future__ import annotations

import sys
from pathlib import Path

from dh import cprint, fsz, get_files, gsz, mpf, rrs, runcmd

EXT = [
    ".java",
    ".c",
    ".cpp",
    ".cxx",
    ".cc",
    ".h",
    ".hh",
    ".hpp",
    ".hxx",
    ".js",
    ".json",
]


def process_file(path):
    path = Path(path)
    before = gsz(path)
    try:
        runcmd(["clang-format", "-i", "--style=LLVM", str(path)], show_output=False)
        after = gsz(path)
        rrs(path, before, after)
        del before, after
        return
    except:
        del before, after
        return


def main() -> None:
    files: list = []
    cwd = Path.cwd()
    before = gsz(cwd)
    args = sys.argv[1:]
    files = [Path(arg) for arg in args] if args else get_files(cwd, ext=EXT)
    all_count = len(files)
    cprint(f"{all_count} files found", "cyan")
    if all_count == 1:
        process_file(files[0])
        sys.exit(1)
    mpf(process_file, files)
    after = gsz(cwd)
    dsz = before - after
    print(f"space change: {fsz(dsz)}")


if __name__ == "__main__":
    raise SystemExit(main())
