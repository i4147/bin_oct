#!/usr/bin/env python3
"""Report module / function / class docstring coverage for a tree of scripts.

Used throughout the docstring task to decide what still needed work and to
confirm the final numbers before committing.

Usage
    python3 arena/doc_coverage.py [--tree DIR] [--list-missing] [--public-only]

``--tree`` defaults to ``documented/``. Files that do not parse are reported
separately; they are never counted as covered.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def dunder(name: str) -> bool:
    """Return True for dunder names such as ``__init__``."""
    return name.startswith("__") and name.endswith("__")


def scan_file(path: Path, public_only: bool) -> tuple[dict[str, int], list[str]]:
    """Return per-file docstring counts and the names still undocumented."""
    counts = {"module": 0, "function": 0, "class": 0}
    missing: list[str] = []

    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return counts, ["<unparsable>"]

    if ast.get_docstring(tree):
        counts["module"] = 1
    else:
        missing.append("<module>")

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if public_only and (node.name.startswith("_") or dunder(node.name)):
                continue
            if ast.get_docstring(node):
                counts["function"] += 1
            else:
                missing.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if public_only and node.name.startswith("_"):
                continue
            if ast.get_docstring(node):
                counts["class"] += 1
            else:
                missing.append(node.name)

    return counts, missing


def main(argv: list[str] | None = None) -> int:
    """Scan the tree and print a coverage summary."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", type=Path, default=ROOT / "documented", help="tree to scan")
    parser.add_argument("--list-missing", action="store_true", help="list names per file")
    parser.add_argument(
        "--public-only", action="store_true", help="ignore private helpers and dunders"
    )
    args = parser.parse_args(argv)

    files = sorted(args.tree.glob("*.py"))
    if not files:
        print(f"no Python files under {args.tree}", file=sys.stderr)
        return 1

    totals = {"module": 0, "function": 0, "class": 0}
    undocumented = 0
    unparsable: list[str] = []

    for path in files:
        counts, missing = scan_file(path, args.public_only)
        if missing == ["<unparsable>"]:
            unparsable.append(path.name)
            continue
        for key, value in counts.items():
            totals[key] += value
        undocumented += len(missing)
        if args.list_missing and missing:
            print(f"{path.name}: {', '.join(missing[:12])}")

    print(
        f"files: {len(files)} | module docstrings: {totals['module']} "
        f"| function docstrings: {totals['function']} "
        f"| class docstrings: {totals['class']} "
        f"| undocumented names: {undocumented}"
    )
    if unparsable:
        print(f"unparsable ({len(unparsable)}): {', '.join(unparsable)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
