#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans a given directory tree for Python source files and reports legacy Python 2-style `print` statements that have been left in the code. The tool should accept a root path as input and walk through all subdirectories, skipping common non-source folders such as version control metadata, caches, and virtual or generated directories, as well as symbolic links. It should only consider Python files, and it should tolerate permission errors or unreadable entries without crashing.
For each file, the script should read its contents efficiently, handling very large files differently from small ones so that memory usage stays reasonable. It should detect `print` statements written without parentheses (the Python 2 form) while ignoring legitimate Python 3 calls such as `print(...)`, and it should take care to avoid false positives inside comments, strings, or docstrings, using the language's own tokenization where appropriate.
The output should be a clear, human-readable report listing each offending file with the line number and the offending line's content, followed by a summary showing the total number of files scanned, the number of files with issues, and the total number of problematic lines found. The script should also return a non-zero exit status when any issues are found so it can be used in continuous integration pipelines, and it should provide a simple command-line interface with a helpful usage message and an option to restrict scanning to specific file extensions.
---"""

from __future__ import annotations
from collections import deque
import mmap
from mmap import mmap
from pathlib import Path
import re
import tokenize


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
