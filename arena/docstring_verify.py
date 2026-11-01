#!/usr/bin/env python3
"""Prove that ``documented/*.py`` differ from the originals only by docstrings.

Used to gate the docstring task before it was committed. For every file it
checks that:

1. the documented copy compiles wherever the original does;
2. the AST with every docstring removed is identical to the original's;
3. every original source line survives, in order (junk placeholder docstrings
   such as ``\"\"\"(No content in stream)`` are deliberately replaced, not kept);
4. every line the documentation added is <= 88 columns.

Usage
    python3 arena/docstring_verify.py [--src DIR] [--out DIR] [--max-cols N]
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def strip_docstrings(tree: ast.AST) -> str:
    """Return the AST dump with every docstring expression removed."""
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        body = node.body
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            node.body = body[1:] or [ast.Pass()]
    return ast.dump(tree)


def is_placeholder(line: str) -> bool:
    """Return True for the junk docstrings the task replaced on purpose."""
    stripped = line.lstrip()
    return stripped.startswith('"""') or stripped.startswith('---"""')


def check_file(src: Path, out: Path, max_cols: int) -> tuple[list[str], int, int]:
    """Return ``(failures, new_docstrings, added_lines)`` for one file."""
    if not out.exists():
        return [f"{src.name}: missing documented copy"], 0, 0

    src_text = src.read_text(encoding="utf-8", errors="replace")
    out_text = out.read_text(encoding="utf-8", errors="replace")

    try:
        src_tree = ast.parse(src_text)
    except SyntaxError:
        if src_text != out_text:
            return [f"{src.name}: unparsable original was modified"], 0, 0
        return [], 0, 0

    try:
        out_tree = ast.parse(out_text)
    except SyntaxError as exc:
        return [f"{src.name}: documented copy does not parse ({exc})"], 0, 0

    if strip_docstrings(src_tree) != strip_docstrings(out_tree):
        return [f"{src.name}: AST changed beyond docstrings"], 0, 0

    src_lines = src_text.splitlines()
    out_lines = out_text.splitlines()
    failures: list[str] = []
    position = 0
    for line in src_lines:
        if is_placeholder(line):
            continue
        while position < len(out_lines) and out_lines[position] != line:
            position += 1
        if position == len(out_lines):
            failures.append(f"{src.name}: original line lost: {line[:60]!r}")
            break

    src_set = set(src_lines)
    added = [line for line in out_lines if line not in src_set]
    new_docs = sum(1 for line in added if '"""' in line)
    for line in added:
        if len(line) > max_cols:
            failures.append(f"{src.name}: added line exceeds {max_cols} cols: {line[:70]!r}")
            break
    return failures, new_docs, len(added)


def main(argv: list[str] | None = None) -> int:
    """Run every check and print a summary line."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--src", type=Path, default=ROOT, help="original tree")
    parser.add_argument("--out", type=Path, default=ROOT / "documented", help="documented tree")
    parser.add_argument("--max-cols", type=int, default=88, help="added-line width limit")
    args = parser.parse_args(argv)

    failures: list[str] = []
    missing: list[str] = []
    new_docs = 0
    added_lines = 0
    originals = sorted(args.src.glob("*.py"))

    for src in originals:
        out = args.out / src.name
        if not out.exists():
            missing.append(src.name)
            continue
        file_failures, file_docs, file_added = check_file(src, out, args.max_cols)
        failures.extend(file_failures)
        new_docs += file_docs
        added_lines += file_added

    print(
        f"checked {len(originals)} files | failures: {len(failures)} "
        f"| missing: {len(missing)} | new docstrings: {new_docs} "
        f"| added lines: {added_lines}"
    )
    for line in failures[:40]:
        print("FAIL", line)
    for name in missing[:40]:
        print("MISSING", name)
    return 1 if failures or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
