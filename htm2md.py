#!/data/data/com.termux/files/usr/bin/env python
"""Build a self-contained Python 3 command-line script (Termux-style, shebang pointing to `/data/data/com.termux/files/usr/bin/env python`) that converts HTML files to Markdown. Requirements:

**Purpose:** Batch-convert `.html` and `.htm` files to `.md` files using an external command-line converter named `rhtml2md`. Each HTML file `name.html` (or `name.htm`) produces `name.md` in the same directory, with the same stem. Non-HTML files are ignored.

**Dependencies:**
- Use `from __future__ import annotations` for type hints.
- Standard library: `sys`, `pathlib.Path`.
- Three helpers imported from a local module named `dh`:
  - `get_files(directory)`: returns an iterable of file paths found in a directory (assumed to recurse or list files; treat as a black box).
  - `mpf(func, files)`: runs `func` over the list of files, typically in parallel (multi-process/thread mapping); treat as a black box.
  - `runcmd(argv_list, show_output=False)`: runs an external command given as a list of arguments and returns a 3-tuple whose middle element is the command's text output.

**Inputs (command line):**
- No arguments: process all files returned by `get_files` on the current working directory.
- One or more arguments: each argument is a path. If it is an existing file, add it to the work list. If it is an existing directory, extend the work list with `get_files(directory)`. Paths that are neither are silently skipped.

**Per-file processing (`process_file(path)`):**
- Convert the input to a `Path`.
- Check the suffix case-insensitively against `.html` and `.htm`. For any other suffix, return `(path, False)` immediately without any work.
- For HTML files, compute the target as the same path with suffix changed to `.md`.
- Call `runcmd(["rhtml2md", str(path)], show_output=False)` and take the middle element of the returned tuple as the Markdown text.
- Write that text to the target file with UTF-8 encoding.
- On success, print `✓ Converted: <input filename> -> <output filename>` to standard output and return `(md_file_path, True)`.
- On any exception, print `✗ Unexpected error converting <path>: <error>` to standard error and return `(path, False)`. Do not re-raise, so one failure does not stop the batch.

**Main flow:**
- Build the file list as described above, then call `mpf(process_file, files)`. The script does not itself collect or report the returned results.
- Run `main()` under the `if __name__ == "__main__":` guard, and exit via `raise SystemExit(main())`, so the process exits with status 0 when `main` returns `None`.

**Edge cases to honor:**
- Empty directories or directories with no matching files produce no output and no error.
- Arguments that do not exist are silently ignored.
- Uppercase extensions such as `.HTML` or `.Htm` are accepted.
- Non-HTML files passed explicitly are skipped without messages.
- Encoding errors in writing are caught by the general exception handler.
- Output file names are derived from the input stem, so an existing `.md` file with the same stem will be overwritten.

**Execution:** Run directly as an executable with the Termux Python interpreter, or invoke with `python <script>` followed by optional files or directories. Requires the `rhtml2md` executable on PATH and the `dh` helper module importable from the script's directory or the Python path.
---"""

from __future__ import annotations

import sys
from pathlib import Path

from dh import get_files, mpf, runcmd


def process_file(path) -> tuple[Path, bool]:
    path = Path(path)
    if path.suffix.lower() in {".html", ".htm"}:
        md_file = path.with_suffix(".md")
    else:
        return (path, False)
    try:
        _, txt, _ = runcmd(["rhtml2md", str(path)], show_output=False)
        md_file.write_text(txt, encoding="utf-8")
        print(f"✓ Converted: {path.name} -> {md_file.name}")
        return (md_file, True)
    except Exception as e:
        print(f"✗ Unexpected error converting {path}: {e}", file=sys.stderr)
        return (path, False)


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = []
    if args:
        for arg in args:
            p = Path(arg)
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(get_files(p))
    else:
        files = get_files(cwd)
    mpf(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
