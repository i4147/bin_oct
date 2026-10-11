#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python command-line tool with the following specification:

Build a Python 3 command-line utility that strips comments from Bash/shell scripts while preserving the scripts' runtime behavior, using a tree-sitter-based parser for accurate comment detection. Make the script self-contained in a single file with an executable shebang line for Termux on Android (`#!/data/data/com.termux/files/usr/bin/env python`), and include `from __future__ import annotations` at the top.

**Dependencies:** Use the standard library modules `argparse`, `multiprocessing`, `os`, `re`, `sys`, and `pathlib.Path`, plus `typing.TYPE_CHECKING` (importing `collections.abc.Generator` and `Iterable` only under that guard). Third-party dependencies are `tree_sitter_bash` (which provides `language()`) and `tree_sitter` (providing `Language`, `Node`, and `Parser`). Construct a module-level Bash `Language` from `tree_sitter_bash.language()` and a module-level `Parser` bound to it, with type annotations.

**Module-level constants:**
- `SHEBANG_PREFIXES`: a tuple of byte-string shebang prefixes recognized as shell scripts, covering `/bin/bash`, `/bin/sh`, `/usr/bin/env bash`, `/usr/bin/env sh`, `/bin/env bash`, `/bin/env sh`, `/usr/bin/env zsh`, and `/bin/zsh`.
- A compiled regex operating on bytes that matches runs of three or more blank lines (lines containing only spaces/tabs followed by newline), used to collapse excess blank lines after comment removal.

**Function `is_bash_file(path: Path) -> bool`:** Return True if the file suffix (case-insensitive) is `.sh` or `.bash`. Otherwise open the file in binary mode, read its first line, and return True if it starts with any shebang prefix. On `OSError` while opening or reading, return False.

**Function `find_comment_ranges(source: bytes) -> list[tuple[int, int, bool]]`:** Parse the source bytes with the tree-sitter parser and walk the syntax tree recursively to find nodes of type `comment`. Skip a comment that begins at byte 0 when the source starts with `#!` (preserve the shebang). For each retained comment, determine the start of its line (scanning backward for a newline byte) and whether the comment is the only non-whitespace content on its line, returning each as a tuple of (start byte, end byte, whether it is a full-line comment). Also include the description of further logic: the rest of the walk recurses into child nodes. Preserve ordering of ranges as encountered.

**Expected remaining behavior (to implement fully):**
- A function to strip comments from source bytes: remove each identified comment range; for full-line comments remove the whole line including its trailing newline; for inline comments remove only the comment text and any whitespace immediately preceding it on that line. Apply removals from the end of the file backward so offsets remain valid. Then collapse runs of three or more blank lines using the blank-run regex into a single blank line, and ensure the output keeps the shebang intact.
- A per-file processing function that reads the file bytes, checks whether it is a Bash file, strips comments, and writes the result back only if content changed. Support a dry-run mode that reports without writing, and a mode that writes to a separate output path or prints a summary. Handle `OSError` and tree-sitter parse issues per file by reporting an error to stderr and continuing; never abort the whole run because one file failed.
- A file discovery generator that accepts paths: for a file, yield it if it is a bash file; for a directory, recursively walk it (using `os.walk` or `Path.rglob`), skip hidden directories and common non-source directories such as `.git`, and yield bash files only. Skip nonexistent paths with a warning to stderr.
- A `main()` function using `argparse` with positional paths (one or more), options for dry-run (`--dry-run` / `-n`), a verbose flag (`--verbose` / `-v`), and a jobs count option (`--jobs` / `-j`, default to CPU count via `os.cpu_count()`), using `multiprocessing.Pool` (or `ProcessPoolExecutor`-style logic) to process files in parallel, with `jobs=1` running sequentially in-process. Print a final summary line with counts of files scanned, modified, and errors. Return exit code 0 on success, 1 if any errors occurred, and 2 for usage problems.
- Guard the entry point with `if __name__ == "__main__":` and call `sys.exit(main())`.

**Execution and usage:** Run as `python script.py [options] PATH...`. Requires `pip install tree-sitter tree-sitter-bash`. Designed to run under Termux; file operations use binary I/O throughout. Use `from __future__ import annotations` for postponed annotations.

**Edge cases to handle:** empty files, files with only a shebang, files with no comments (leave unchanged, do not rewrite), comments inside strings (must not be removed, relying on the parser to distinguish comment nodes), trailing whitespace before inline comments, CRLF line endings preserved where possible, unreadable files, and non-UTF-8 content (operate on bytes, never decode).

Produce clean, typed, idiomatic Python with docstrings where helpful, consistent with the style of the surrounding code.
---"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import tree_sitter_bash
from tree_sitter import Language, Node, Parser

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable
BASH_LANGUAGE: Language = Language(tree_sitter_bash.language())
PARSER: Parser = Parser(BASH_LANGUAGE)
SHEBANG_PREFIXES: tuple[bytes, ...] = (
    b"#!/bin/bash",
    b"#!/bin/sh",
    b"#!/usr/bin/env bash",
    b"#!/usr/bin/env sh",
    b"#!/bin/env bash",
    b"#!/bin/env sh",
    b"#!/usr/bin/env zsh",
    b"#!/bin/zsh",
)
_BLANK_RUN_RE = re.compile(rb"(?:[ \t]*\n){3,}")


def is_bash_file(path: Path) -> bool:
    if path.suffix.lower() in (".sh", ".bash"):
        return True
    try:
        with path.open("rb") as fh:
            first_line = fh.readline()
    except OSError:
        return False
    return any(first_line.startswith(p) for p in SHEBANG_PREFIXES)


def find_comment_ranges(source: bytes) -> list[tuple[int, int, bool]]:
    tree = PARSER.parse(source)
    out: list[tuple[int, int, bool]] = []

    def walk(node: Node) -> None:
        if node.type == "comment":
            start, end = node.start_byte, node.end_byte
            if not (start == 0 and source.startswith(b"#!")):
                line_start = source.rfind(b"\n", 0, start) + 1
                prefix = source[line_start:start]
                is_inline = bool(prefix.strip())
                out.append((start, end, is_inline))
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    out.sort(key=lambda r: r[0])
    return out


def strip_comments(source: bytes) -> tuple[bytes, int]:
    ranges = find_comment_ranges(source)
    if not ranges:
        return source, 0
    out = bytearray()
    last = 0
    for start, end, is_inline in ranges:
        out.extend(source[last:start])
        if is_inline:
            while out and out[-1:] in (b" ", b"\t"):
                out.pop()
        last = end
    out.extend(source[last:])
    return bytes(out), len(ranges)


def normalize_blank_lines(source: bytes) -> bytes:
    return _BLANK_RUN_RE.sub(b"\n\n", source)


def validate_bash_source(source: bytes) -> bool:
    tree = PARSER.parse(source)

    def has_error(node: Node) -> bool:
        if node.type == "ERROR" or node.is_missing:
            return True
        return any(has_error(child) for child in node.children)

    return not has_error(tree.root_node)


def process_file(path: Path) -> tuple[str, int, str]:
    rel = os.path.relpath(path)
    try:
        source = path.read_bytes()
    except OSError as e:
        return rel, 0, f"read error: {e}"
    stripped, count = strip_comments(source)
    if count == 0:
        return rel, 0, ""
    normalized = normalize_blank_lines(stripped)
    if not validate_bash_source(normalized):
        return rel, 0, "validation error: result is not valid bash, skipped"
    try:
        path.write_bytes(normalized)
    except OSError as e:
        return rel, 0, f"write error: {e}"
    return rel, count, ""


def iter_targets(targets: Iterable[Path]) -> Generator[Path, None, None]:
    seen: set[Path] = set()
    for target in targets:
        try:
            target = target.resolve()
        except OSError:
            continue
        if target.is_file():
            if is_bash_file(target) and target not in seen:
                seen.add(target)
                yield target
        elif target.is_dir():
            for p in sorted(target.rglob("*")):
                if p.is_file() and is_bash_file(p) and p not in seen:
                    seen.add(p)
                    yield p


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Remove comments from bash scripts in place (tree-sitter powered).",
    )
    ap.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or directories to process. Defaults to the current directory.",
    )
    args = ap.parse_args()
    targets: list[Path] = args.paths or [Path.cwd()]
    files = list(iter_targets(targets))
    if not files:
        print("no bash scripts found", file=sys.stderr)
        return 1
    total_removed = 0
    files_touched = 0
    errors = 0
    with mp.Pool(processes=8) as pool:
        results = [pool.apply_async(process_file, (f,)) for f in files]
        for res in results:
            rel, count, err = res.get()
            if err:
                errors += 1
                print(f"{rel}: {err}", file=sys.stderr)
            else:
                if count:
                    files_touched += 1
                total_removed += count
                print(f"{rel}: {count} comment(s) removed")
    print(
        f"\nDone: {files_touched}/{len(files)} file(s) modified, {total_removed} comment(s) removed, {errors} error(s)."
    )
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    raise SystemExit(main())
