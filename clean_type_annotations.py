#!/data/data/com.termux/files/usr/bin/env python
"""Create a self-contained prompt that instructs an AI coding agent to write a Python script with the following specification:

Write a single Python executable script (Termux-style shebang pointing to the Termux Python interpreter, with `from __future__ import annotations` at the top) whose purpose is to strip type annotations from Python source files in place, converting annotated code into valid unannotated Python while preserving formatting, comments, and runtime behavior as much as possible.

Core requirements:

1. Purpose and approach: Use the libCST library to parse each target `.py` file into a concrete syntax tree and apply a custom transformer that removes type information. The transformer must:
   - Remove annotations from function parameters (including those on parameters of all kinds) by setting the annotation to none, leaving the default values intact.
   - Remove return annotations from function definitions.
   - Remove PEP 695 type parameter lists from functions and classes when present, guarded with attribute checks so older libCST versions do not crash.
   - Convert annotated assignments: if an annotated assignment has no value, remove the statement entirely; if it has a value, rewrite it as a plain assignment to the same target, preserving the value and whitespace/semicolon structure as much as practical.
   - Handle any other annotation-only constructs (such as a type alias statement, if present in the libCST version) appropriately, dropping or simplifying them so the output remains valid Python.
   - Leave nodes unchanged when there is nothing to remove, returning the original updated node.

2. Inputs and outputs: The script accepts one or more file or directory paths on the command line (or a sensible default such as the current directory if none is given). For directories, it recursively finds all `.py` files, skipping any directory named `__pycache__`. Each file is processed and overwritten in place only if the transformed source differs from the original. It should report a summary (counts of files processed, changed, skipped, and failed) to stdout, and per-file errors to stderr.

3. Parallelism: Process files concurrently using the `multiprocessing` module with a fixed worker pool of 8 processes. Use a top-level worker function so it is picklable. Collect results as they complete and aggregate them in the parent process. Guard the entry point with the standard main-module check. Handle the case where there are few files by not spawning more workers than files.

4. Robustness and error handling:
   - Read files with proper encoding detection: honor PEP 263 encoding declarations via the `tokenize` module's `detect_encoding`, falling back to UTF-8 on failure, and preserve the original encoding and line endings when writing back.
   - Catch libCST parse errors and other exceptions per file so one bad file does not abort the run; record them as failures.
   - Suppress unwanted stdout noise from libraries inside workers using `contextlib.redirect_stdout` or similar with an `io.StringIO` buffer where appropriate.
   - Write files atomically where feasible (write to a temporary file in the same directory, then replace) to avoid corruption if interrupted.
   - Gracefully handle nonexistent paths, unreadable files, and permission errors by reporting them and continuing.
   - Use `pathlib.Path` throughout.

5. Dependencies: Python standard library (`contextlib`, `io`, `multiprocessing`, `os`, `sys`, `tokenize`, `pathlib`, `typing`) and the third-party `libcst` package. Use `TYPE_CHECKING` guards for type-only imports such as `collections.abc` iterables and sequences.

6. Execution details: Run as `python script.py [paths...]`. Exit with status 0 when all files succeed and a nonzero status if any file failed. Keep constants such as worker count and skipped directory names as module-level constants.

7. Edge cases: empty files, files with no annotations (must not be rewritten), files with syntax errors, files with BOMs or non-UTF-8 encodings, symlinks (do not follow directory symlink loops), and deeply nested directories.

Deliver the complete script in a single file, with clear structure, concise docstrings, and no unnecessary dependencies.
---"""

from __future__ import annotations

import contextlib
import io
import multiprocessing as mp
import os
import sys
import tokenize
from pathlib import Path
from typing import TYPE_CHECKING

import libcst as cst

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
WORKERS = 8
SKIP_DIR_NAMES = frozenset({"__pycache__"})


class TypeAnnotationRemover(cst.CSTTransformer):
    def leave_Param(self, original_node, updated_node):
        if updated_node.annotation is None:
            return updated_node
        return updated_node.with_changes(annotation=None)

    def leave_FunctionDef(self, original_node, updated_node):
        changes = {}
        if updated_node.returns is not None:
            changes["returns"] = None
        if getattr(updated_node, "type_parameters", None) is not None:
            changes["type_parameters"] = None
        if not changes:
            return updated_node
        return updated_node.with_changes(**changes)

    def leave_ClassDef(self, original_node, updated_node):
        if getattr(updated_node, "type_parameters", None) is not None:
            return updated_node.with_changes(type_parameters=None)
        return updated_node

    def leave_AnnAssign(self, original_node, updated_node):
        if updated_node.value is None:
            return cst.RemoveFromParent()
        return cst.Assign(
            targets=[cst.AssignTarget(target=updated_node.target)],
            value=updated_node.value,
            semicolon=updated_node.semicolon,
        )

    def leave_SimpleStatementLine(self, original_node, updated_node):
        if not updated_node.body:
            return cst.RemoveFromParent()
        return updated_node

    def leave_SimpleStatementSuite(self, original_node, updated_node):
        if not updated_node.body:
            return updated_node.with_changes(body=[cst.Pass()])
        return updated_node

    def leave_IndentedBlock(self, original_node, updated_node):
        if not updated_node.body:
            return updated_node.with_changes(body=[cst.SimpleStatementLine(body=[cst.Pass()])])
        return updated_node


def _read_source(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
    return raw.decode(encoding), encoding


def _atomic_write(path: Path, text: str, encoding: str) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(text, encoding=encoding)
        with contextlib.suppress(OSError):
            os.chmod(tmp, path.stat().st_mode)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            with contextlib.suppress(OSError):
                tmp.unlink()


def process_file(path_str: str) -> tuple[str, str | None, bool]:
    path = Path(path_str)
    try:
        source, encoding = _read_source(path)
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        return path_str, f"read failed: {exc}", False
    try:
        module = cst.parse_module(source)
    except cst.ParserSyntaxError as exc:
        return path_str, f"parse failed: {exc}", False
    except Exception as exc:
        return path_str, f"parse failed: {exc!r}", False
    try:
        new_code = module.visit(TypeAnnotationRemover()).code
    except Exception as exc:
        return path_str, f"transform failed: {exc!r}", False
    if new_code == source:
        return path_str, None, False
    try:
        compile(new_code, str(path), "exec")
    except (SyntaxError, ValueError) as exc:
        return path_str, f"validation failed: {exc}", False
    try:
        _atomic_write(path, new_code, encoding)
    except OSError as exc:
        return path_str, f"write failed: {exc}", False
    return path_str, None, True


def _iter_python_files(root: Path) -> Iterable[Path]:
    for candidate in root.rglob("*.py"):
        if not candidate.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in candidate.parts):
            continue
        yield candidate


def collect_files(inputs: Sequence[str]) -> list[Path]:
    roots: list[Path] = [Path(p) for p in inputs] if inputs else [Path.cwd()]
    seen: set[Path] = set()
    files: list[Path] = []
    for root in roots:
        if root.is_dir():
            candidates: Iterable[Path] = _iter_python_files(root)
        elif root.is_file():
            if root.suffix != ".py":
                print(f"warning: not a .py file: {root}", file=sys.stderr)
                continue
            candidates = (root,)
        else:
            print(f"warning: path not found: {root}", file=sys.stderr)
            continue
        for path in candidates:
            try:
                key = path.resolve()
            except OSError:
                key = path
            if key in seen:
                continue
            seen.add(key)
            files.append(path)
    files.sort(key=str)
    return files


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    files = collect_files(args)
    if not files:
        print("No Python files to process.", file=sys.stderr)
        return 0
    print(
        f"Processing {len(files)} file(s) with {WORKERS} worker(s)...",
        file=sys.stderr,
    )
    tasks = [(str(p),) for p in files]
    chunksize = max(1, len(tasks) // (WORKERS * 4))
    with mp.Pool(processes=WORKERS) as pool:
        results = pool.starmap(process_file, tasks, chunksize=chunksize)
    changed = 0
    unchanged = 0
    errors = 0
    for path_str, error, was_changed in results:
        if error is not None:
            errors += 1
            print(f"ERROR {path_str}: {error}", file=sys.stderr)
        elif was_changed:
            changed += 1
        else:
            unchanged += 1
    print(
        f"Done: {changed} modified, {unchanged} unchanged, {errors} error(s).",
        file=sys.stderr,
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
