#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line refactoring tool for cleaning up files whose names or contents carry an unwanted "u" prefix on standard library module names. The tool should accept one or more file or directory paths (with directories processed recursively for Python source files) and a dry-run option that reports intended changes without modifying anything.
For each Python file it processes, the tool should:
- Detect identifiers in the text that begin with a lowercase "u" immediately followed by the name of a Python standard library module, and rewrite them to drop the leading "u", while leaving any other identifiers untouched. Matching must respect word boundaries so that unrelated words are not altered.
- Determine whether a given module name belongs to the standard library in a way that works across Python versions, preferring an official list when available and falling back to a module-lookup check otherwise.
- Rename files whose stem starts with "u" followed by a standard library module name, dropping the leading "u" from the filename while preserving the extension, and avoid overwriting any existing file with the target name.
- Save content changes only when the text actually differs, and report a clear summary of each file that was modified or renamed, including counts of changed files and renamed files at the end.
- Handle errors gracefully (unreadable files, encoding issues, permission problems) by logging a message and continuing with the remaining files, returning a nonzero exit status if any failures occurred.
The output should be a self-contained, well-structured command-line utility with helpful usage text, clear console reporting, and safe default behavior that never silently destroys data.
---"""

from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

if sys.version_info >= (3, 10):
    _STDLIB: set[str] | None = set(sys.stdlib_module_names)
else:
    import importlib.util

    _STDLIB = None


def is_stdlib(name: str) -> bool:
    if _STDLIB is not None:
        return name in _STDLIB
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError, AttributeError):
        return False


_U_PREFIX_RE = re.compile(r"\bu([A-Za-z_][A-Za-z0-9_]*)\b")


def refactor_content(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        candidate = match.group(1)
        if is_stdlib(candidate):
            return candidate
        return match.group(0)

    return _U_PREFIX_RE.sub(repl, text)


def _rename_target(path: Path) -> Path | None:
    stem = path.stem
    if len(stem) > 1 and stem.startswith("u") and is_stdlib(stem[1:]):
        return path.with_name(stem[1:] + path.suffix)
    return None


def refactor_file(path: Path, dry_run: bool = False) -> tuple[bool, bool]:
    content_changed = False
    name_changed = False
    original = path.read_text(encoding="utf-8")
    updated = refactor_content(original)
    if updated != original:
        content_changed = True
        if not dry_run:
            path.write_text(updated, encoding="utf-8")
    new_path = _rename_target(path)
    if new_path is not None:
        name_changed = True
        if not dry_run:
            if new_path.exists():
                print(f"  ! not renaming {path.name}: {new_path.name} already exists")
            else:
                path.rename(new_path)
    return content_changed, name_changed


def _iter_py_files(root: Path):
    if root.is_file():
        if root.suffix == ".py":
            yield root
    elif root.is_dir():
        yield from root.rglob("*.py")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Refactor MicroPython .py files to standard Python.",
    )
    ap.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path()],
        help="Files or directories to refactor (recursively). Defaults to '.' if omitted.",
    )
    ap.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Only report what would be changed; touch nothing.",
    )
    args = ap.parse_args(argv)
    roots = args.paths or [Path()]
    total = 0
    for root in roots:
        for f in _iter_py_files(root):
            content_changed, name_changed = refactor_file(f, dry_run=args.dry_run)
            if content_changed or name_changed:
                total += 1
                tags = []
                if content_changed:
                    tags.append("content")
                if name_changed:
                    tags.append("rename")
                print(f"{f}: {', '.join(tags)}")
    if total == 0:
        print("Nothing to do.")
    else:
        verb = "Would refactor" if args.dry_run else "Refactored"
        print(f"{verb} {total} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
