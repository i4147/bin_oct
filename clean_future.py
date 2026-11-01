#!/data/data/com.termux/files/usr/bin/env python
"""Recursively strip `from __future__ import annotations` from Python files."""

import re
import sys
from pathlib import Path
from typing import Iterable, Iterator, Union

import rignore

from dh import atomic_write


SKIP_DIRS = frozenset({
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".nox",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".eggs",
    ".idea",
    ".vscode",
})

# Matches a whole line importing *only* `annotations` from __future__.
# Will NOT match `from __future__ import annotations, generator_stop`.
FUTURE_ANNOTATIONS_RE = re.compile(
    r"""^[ \t]*
        from[ \t]+__future__[ \t]+import[ \t]+
        (?:\(\s*annotations\s*\)|annotations)
        [ \t]*
        (?:\#[^\n]*)?
        \r?\n""",
    re.VERBOSE | re.MULTILINE,
)


def _has_python_shebang(path: Path) -> bool:
    """True if the file's first line is a Python shebang."""
    try:
        with path.open("rb") as f:
            first = f.readline(256)
    except OSError:
        return False
    if not first.startswith(b"#!"):
        return False
    low = first.lower()
    return b"python" in low or b"pypy" in low


def is_python_file(path: Union[str, Path]) -> bool:
    path = Path(path)
    if path.suffix == ".py":
        return True
    if path.suffix == "":  # extensionless — check for shebang
        return _has_python_shebang(path)
    return False


def walk_python_files(root_dir: Union[str, Path]) -> Iterator[Path]:
    """Generator yielding Python files under *root_dir*, respecting rignore."""
    root = Path(root_dir).resolve()
    for entry in rignore.walk(root):
        path = Path(entry)
        # Skip symlinks (rignore may not follow them, but be defensive).
        if path.is_symlink():
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if not path.is_file():
            continue
        if is_python_file(path):
            yield path


def strip_future_annotations(text: str) -> str:
    return FUTURE_ANNOTATIONS_RE.sub("", text)


def process_file(path: Path) -> bool:
    """Return True if the file was modified."""
    try:
        original = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"skip   {path.name}: {exc}", file=sys.stderr)
        return False

    updated = strip_future_annotations(original)
    if updated == original:
        return False

    try:
        atomic_write(path, updated)
    except Exception as exc:  # noqa: BLE001
        print(f"error  {path.name}: {exc}", file=sys.stderr)
        return False
    return True


def main(argv: Iterable[str]) -> int:
    args = list(argv)
    root = args[1] if len(args) > 1 else "."

    scanned = changed = 0
    for path in walk_python_files(root):
        scanned += 1
        if process_file(path):
            changed += 1
            print(f"update {path.name}")

    print(f"scanned {scanned} python files, modified {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
