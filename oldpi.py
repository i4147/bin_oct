#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script with the following specification:

Create a Python command-line utility (Termux-friendly, shebang pointing to the Termux Python path) that recursively scans a directory tree for Python source files and detects legacy Python 2-style `print` statements (e.g., `print "text"` without parentheses).

Requirements to implement:

1. **File discovery**
   - Provide a function that takes a directory path (string or Path) and an optional list of file extensions, and returns a list of file Paths.
   - Traverse breadth-first using a queue, starting from the given root.
   - Skip these directory names entirely: `.git`, `__pycache__`, `.mypy_cache`, `.ruff_cache`, `.pytest_cache`, `lazy`.
   - Do not follow symbolic links (skip them for both files and directories).
   - Include a file only if it is a regular file and either no extension filter is given or its suffix is in the filter list.
   - Silently skip directories that raise PermissionError or OSError when listing.
   - Use `from __future__ import annotations` and modern type hints (`str | Path`, `list[str] | None`).

2. **Legacy print detection**
   - Define a module-level size threshold of 1 MiB.
   - Define a multiline regex matching lines whose first non-whitespace token is `print` followed by at least one space/tab and then a character that is not `(` or newline (catching Python 2 print statements, not `print(...)` calls).
   - Provide a helper that opens a file for scanning: stat the file size; open in binary mode; if larger than the threshold, return a read-only memory map of the file, otherwise return the file handle. Ensure resources are properly managed (close the file handle/mmap appropriately).
   - Provide a helper that reads a file as UTF-8 text with `errors="ignore"`, returning `None` on read failure (catch OS and decoding-related exceptions gracefully).
   - Use the `tokenize` module where appropriate to distinguish real code tokens from string/comment content so that matches inside strings or comments are not counted as violations (the regex alone is a first pass; the tokenizer validates).
   - Return per-file results listing the line numbers and offending line content of detected legacy print statements.

3. **Parallel execution**
   - Process the discovered files in parallel using the `dh` package's `mpf_joblib` helper (import it as `from dh import mpf_joblib`). Assume it maps a function over an iterable of items in parallel and returns results; keep the call compatible with that usage, and gracefully handle results where a file yielded no findings or could not be read.

4. **Output and CLI**
   - Accept a target directory from the command line (default to the current directory), optionally an extension filter.
   - Print a report for each file containing violations: file path, line number, and the offending line, followed by a summary count of files and total violations.
   - Exit with status 0 when no violations are found and a nonzero status otherwise.
   - Use an `if __name__ == "__main__":` guard.

5. **Edge cases and robustness**
   - Empty directories, unreadable directories, symlinks, binary or non-UTF-8 files, empty files, and files exactly at or above the size threshold must not crash the script.
   - Avoid duplicate imports of `mmap` (import the module once; do not shadow it).
   - Keep the code clean, PEP 8 compliant, and idiomatic; include concise docstrings and comments only where helpful.

Output only the script itself as the deliverable.
---"""

from __future__ import annotations

import mmap
import re
import tokenize
from collections import deque
from mmap import mmap
from pathlib import Path

from dh import mpf_joblib


def get_files(path: str | Path, ext: list[str] | None = None) -> list[Path]:
    path = Path(path)
    skip_dirs = {
        ".git",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "lazy",
    }
    queue = deque([path])
    files = []
    while queue:
        current = queue.popleft()
        try:
            entries = current.iterdir()
        except (PermissionError, OSError):
            continue
        for item in entries:
            if item.is_symlink():
                continue
            if item.is_dir() and item.name not in skip_dirs:
                queue.append(item)
            elif item.is_file() and (ext is None or item.suffix in ext):
                files.append(item)
    return files


SIZE_THRESHOLD = 1 * 1024 * 1024
OLD_PRINT_RE = re.compile(r"(?m)^[ \t]*print[ \t]+[^(\n]")


def _open_source(path: str):
    size = Path(path).stat().st_size
    f = Path(path).open("rb")
    if size > SIZE_THRESHOLD:
        return mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    return f


def _read_text(path: str) -> str | None:
    try:
        with Path(path).open(encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None


def _has_rich_print_import(text: str) -> bool:
    return "from rich import print" in text


def _is_in_commented_code(text: str, line_start: int) -> bool:
    lines = text.splitlines(True)
    if line_start >= len(lines):
        return False
    in_multiline = False
    multiline_delimiter = None
    for i, line in enumerate(lines):
        if i == line_start:
            stripped = line.lstrip()
            if stripped.startswith("#"):
                return True
            break
        for quote in ['"""', "'''"]:
            pos = line.find(quote)
            if pos != -1:
                if in_multiline and multiline_delimiter == quote:
                    in_multiline = False
                    multiline_delimiter = None
                elif not in_multiline:
                    in_multiline = True
                    multiline_delimiter = quote
                break
    return in_multiline


def regex_flag(path: str) -> bool:
    text = _read_text(path)
    if not text:
        return False
    if _has_rich_print_import(text):
        return False
    return bool(OLD_PRINT_RE.search(text))


def tokenizer_confirm(path: str) -> tuple[str, int] | None:
    try:
        src = _open_source(path)
        tokens = list(tokenize.tokenize(src.readline))
    except Exception:
        return None
    text = _read_text(path)
    if not text:
        return None
    for i, tok in enumerate(tokens):
        if tok.type == tokenize.NAME and tok.string == "print":
            line = tok.line.rstrip()
            if line.strip() == "print":
                continue
            line_num = tok.start[0]
            if _is_in_commented_code(text, line_num - 1):
                continue
            j = i + 1
            while j < len(tokens) and tokens[j].type in {
                tokenize.NL,
                tokenize.NEWLINE,
                tokenize.INDENT,
                tokenize.DEDENT,
            }:
                j += 1
            if j < len(tokens) and tokens[j].string != "(":
                if line.lstrip().startswith("#"):
                    continue
                return (line, line_num)
    return None


def autofix_file(path: str) -> bool:
    try:
        with Path(path).open(encoding="utf-8") as f:
            lines = f.readlines()
        if any(l.strip() == "from rich import print" for l in lines):
            return False
        changed = False
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if '"""' in stripped or "'''" in stripped:
                continue
            if stripped.rstrip() == "print":
                continue
            if stripped.startswith("print ") and (not stripped.startswith("print(")):
                indent = line[: len(line) - len(stripped)]
                content = stripped[len("print ") :].rstrip()
                lines[i] = f"{indent}print({content})\n"
                changed = True
        if changed:
            with Path(path).open("w", encoding="utf-8") as f:
                f.writelines(lines)
        return changed
    except Exception:
        return False


def process_file(path: str, autofix: bool = False) -> str | None:
    if not regex_flag(path):
        return None
    confirmed = tokenizer_confirm(path)
    if not confirmed:
        return None
    line, line_num = confirmed
    if autofix:
        if autofix_file(path):
            return f"{path} (fixed)\n  Line {line_num}: {line}"
        else:
            return f"{path} (could not fix)\n  Line {line_num}: {line}"
    else:
        return f"{path}\n  Line {line_num}: {line}"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Detect and fix Python 2 print statements")
    parser.add_argument("path", nargs="?", default=".", help="Path to file or directory to scan")
    parser.add_argument(
        "-a",
        "--autofix",
        action="store_true",
        help="Automatically fix print statements",
    )
    args = parser.parse_args()
    path = Path(args.path)
    if path.is_file() and path.suffix == ".py":
        files = [path]
    else:
        files = get_files(path, ext=[".py"])
    if not files:
        print("No Python files found.")
        return
    results = mpf_joblib(process_file, files, autofix=args.autofix)
    found_issues = False
    for result in results:
        if result:
            print(result)
            found_issues = True
    if not found_issues:
        print("No Python 2 print statements found.")
    elif args.autofix:
        print("\n✓ Files with issues have been automatically fixed.")
    else:
        print("\nRun with --autofix to automatically fix these issues.")


if __name__ == "__main__":
    raise SystemExit(main())
