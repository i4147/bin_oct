#!/data/data/com.termux/files/home/.local/bin/python
"""
Refactor MicroPython .py sources to standard Python.

Two transformations are applied:

1. Filenames
   Strip a leading 'u' from a .py filename when the remainder is a
   standard-library module name (e.g. ``uos.py`` -> ``os.py``).

2. Content
   Replace identifiers of the form ``u<name>`` (word-boundary matched)
   with ``<name>`` whenever ``<name>`` is a standard-library module
   name (e.g. ``import utime`` -> ``import time``, ``uos.path`` ->
   ``os.path``).

Usage:
    python refactor_micropython.py [path ...] [-n]

If no path is given, the current directory ('.') is processed
recursively. Every path may be a file or a directory; directories are
walked recursively for ``*.py`` files.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Standard library detection
# ---------------------------------------------------------------------------
# ``sys.stdlib_module_names`` is a frozenset available on Python >= 3.10.
# On older interpreters we fall back to importlib.util.find_spec, which is
# slower but sufficient for this script's purposes.

if sys.version_info >= (3, 10):
    _STDLIB: set[str] | None = set(sys.stdlib_module_names)
else:  # pragma: no cover - fallback for older interpreters
    import importlib.util

    _STDLIB = None


def is_stdlib(name: str) -> bool:
    """Return True if ``name`` resolves to a standard-library module.

    Uses the fast path (``sys.stdlib_module_names``) when available and
    otherwise falls back to ``importlib.util.find_spec``.
    """
    if _STDLIB is not None:
        return name in _STDLIB
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# Content refactoring
# ---------------------------------------------------------------------------

# Matches a word-boundary 'u' followed by a Python identifier.
# group(1) is the candidate stdlib module name (the part *after* the 'u').
# Using \b on both sides avoids matching things like 'hour' or 'gui'
# (no 'u' at a word boundary) as well as 'utime2' (trailing digits are
# part of the identifier, so 'time2' is checked instead of 'time').
_U_PREFIX_RE = re.compile(r"\bu([A-Za-z_][A-Za-z0-9_]*)\b")


def refactor_content(text: str) -> str:
    """Return ``text`` with ``u<mod>`` identifiers replaced where safe.

    Only rewrites when the candidate (the part after the leading ``u``)
    is an actual standard-library module name. Anything else is left
    untouched, so identifiers like ``user``, ``unittest`` or ``url`` are
    preserved.
    """

    def repl(match: re.Match[str]) -> str:
        candidate = match.group(1)
        if is_stdlib(candidate):
            return candidate
        return match.group(0)

    return _U_PREFIX_RE.sub(repl, text)


# ---------------------------------------------------------------------------
# File-level refactoring
# ---------------------------------------------------------------------------


def _rename_target(path: Path) -> Path | None:
    """Return the new Path if the filename should be renamed, else None.

    A rename is suggested only when the stem starts with ``u``, has more
    characters after it, and the remainder is a stdlib module name.
    """
    stem = path.stem
    if len(stem) > 1 and stem.startswith("u") and is_stdlib(stem[1:]):
        return path.with_name(stem[1:] + path.suffix)
    return None


def refactor_file(path: Path, dry_run: bool = False) -> tuple[bool, bool]:
    """Refactor a single ``.py`` file.

    Performs two independent operations:

    * rewrite ``u<mod>`` identifiers in the source text;
    * rename the file if its name looks like ``u<mod>.py``.

    Returns a tuple ``(content_changed, name_changed)``. When
    ``dry_run`` is True, the file is inspected but never modified.
    """
    content_changed = False
    name_changed = False

    # ---- content ----------------------------------------------------------
    original = path.read_text(encoding="utf-8")
    updated = refactor_content(original)
    if updated != original:
        content_changed = True
        if not dry_run:
            path.write_text(updated, encoding="utf-8")

    # ---- filename ---------------------------------------------------------
    new_path = _rename_target(path)
    if new_path is not None:
        name_changed = True
        if not dry_run:
            if new_path.exists():
                # Never clobber an existing file; report and skip.
                print(f"  ! not renaming {path.name}: {new_path.name} already exists")
            else:
                path.rename(new_path)

    return content_changed, name_changed


# ---------------------------------------------------------------------------
# Path iteration
# ---------------------------------------------------------------------------


def _iter_py_files(root: Path):
    """Yield ``.py`` files under ``root``.

    If ``root`` is a file, it is yielded when it has a ``.py`` suffix.
    If it is a directory, the tree is walked recursively.
    """
    if root.is_file():
        if root.suffix == ".py":
            yield root
    elif root.is_dir():
        yield from root.rglob("*.py")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Refactor MicroPython .py files to standard Python.",
    )
    ap.add_argument(
        "paths",
        nargs="*",  # zero or more: default handled below
        type=Path,
        default=[Path(".")],  # no args -> recurse from current directory
        help="Files or directories to refactor (recursively). "
        "Defaults to '.' if omitted.",
    )
    ap.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Only report what would be changed; touch nothing.",
    )
    args = ap.parse_args(argv)

    # ``nargs='*'`` with a ``default`` gives us an empty list when nothing
    # is supplied, so normalise that to ['.'] explicitly.
    roots = args.paths or [Path(".")]

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
