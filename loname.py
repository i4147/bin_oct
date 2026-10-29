#!/data/data/com.termux/files/usr/bin/env python
from __future__ import annotations

import argparse
import re
import string
import sys
from pathlib import Path
from typing import Iterator, Optional, Sequence

from rignore import walk

SKIP_DIRS: frozenset[str] = frozenset({
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    ".idea",
    ".vscode",
})

_CYAN: str = "\033[36m"
_RESET: str = "\033[0m"

_PUNCT_TO_REMOVE: str = string.punctuation.replace("_", "").replace("-", "").replace(":", "")
_TRANSLATE_TABLE = str.maketrans({c: None for c in _PUNCT_TO_REMOVE} | {" ": "_"})
_COLLAPSE_RE = re.compile(r"[_:\-]+")


def normalize_name(name: str) -> str:
    path = Path(name)
    stem = path.stem
    suffix = path.suffix
    stem = stem.lower()
    stem = stem.translate(_TRANSLATE_TABLE)
    stem = _COLLAPSE_RE.sub("_", stem)
    stem = stem.strip("_")
    if not stem:
        stem = "unnamed"
    return stem + suffix.lower()


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    parent = path.parent
    stem = path.stem
    suffix = path.suffix
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def process_file(path: Path | str, *, dry_run: bool = False) -> Optional[str]:
    path = Path(path)
    if not path.exists():
        lowered = Path(str(path).lower())
        if not lowered.exists():
            return None
        path = lowered
    if not path.is_file():
        return None
    new_name = normalize_name(path.name)
    if new_name == path.name:
        return None
    new_path = path.with_name(new_name)
    if new_path.exists() and new_path.resolve() != path.resolve():
        new_path = unique_path(new_path)
    if not dry_run:
        path.rename(new_path)
    prefix = "[dry-run] " if dry_run else ""
    return f"{prefix}{path.name} -> {_CYAN}{new_path.name}{_RESET}"


def iter_files(root: Path, *, recursive: bool) -> Iterator[Path]:
    root = root.resolve()
    for entry in walk(root):
        path = Path(entry)
        if path.is_symlink() or not path.is_file():
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if not recursive and len(rel.parts) > 1:
            continue
        yield path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize filenames: lowercase, strip punctuation, spaces→_, collapse _-:"
    )
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("-r", "--recursive", action="store_true")
    parser.add_argument("-n", "--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    cwd = Path.cwd()

    def iter_inputs() -> Iterator[Path]:
        if not args.paths:
            yield from iter_files(cwd, recursive=args.recursive)
            return
        for p in args.paths:
            p = p if p.is_absolute() else cwd / p
            if p.is_dir():
                yield from iter_files(p, recursive=args.recursive)
            elif p.is_file() and not p.is_symlink():
                yield p

    for path in iter_inputs():
        msg = process_file(path, dry_run=args.dry_run)
        if msg:
            print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
