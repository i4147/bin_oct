#!/data/data/com.termux/files/usr/bin/env python
"""Create a self-contained prompt that instructs an AI coding agent to write a Python script which strips comments and docstrings from Python source files, preserving certain special comments, using libcst, with parallel processing via multiprocessing, and with error handling and CLI usage. Output only the prompt.

Write a complete, self-contained Python command-line script that removes comments and docstrings from Python source files while preserving specific directive comments, using the libcst library for concrete syntax tree transformation and multiprocessing for parallel batch processing. The script must be runnable under Termux on Android (shebang line pointing to the Termux Python path), and should be written for Python 3.10+ with `from __future__ import annotations`.

**Purpose and behavior**
- Accept one or more input paths on the command line. Each path may be a single `.py` file or a directory, which should be searched recursively for `.py` files.
- For each Python file, parse the source with libcst, apply a transformer that strips comments and docstrings, and write the result back to the same file (in-place) or to an output location, depending on the CLI options.
- Provide an argument parser (argparse) with options for: the input paths (positional, one or more), an optional output directory or a dry-run/check mode that reports which files would change without modifying them, and an optional worker count (default 8, capped at a constant MAX_WORKERS of 8).

**Comment preservation rules**
- Define a module-level constant tuple of prefixes that must always be kept: `#!` (shebang), `# type:` (type comments), and `# fmt:` (formatter directives).
- Define a module-level frozenset of exact comments that must be kept: `# fmt: skip`, `# fmt: on`, `# fmt: off`.
- A helper function takes a comment's text, strips surrounding whitespace, and returns True if it starts with any preserved prefix or exactly equals a preserved exact string.
- All other comments are removed.

**Transformer logic (libcst)**
- Implement a subclass of `cst.CSTTransformer`.
- In a `leave_Comment` method, return the updated node if the comment should be preserved; otherwise return `cst.RemovalSentinel.REMOVE`.
- Implement a static helper that inspects a sequence of statements in a module, class, or function body and, if the first statement is a simple statement line containing exactly one `cst.Expr` whose value is a string literal (a docstring), removes it. Apply this to module bodies, class bodies, and function bodies (including async functions). Ensure that if removing the docstring would leave the body empty, a `pass` statement is inserted so the code remains syntactically valid.
- Be careful to handle the case where the first statement is a docstring that also carries leading comments or where an indented block would otherwise become empty.

**Processing pipeline**
- For each file: read the source as UTF-8 (fall back gracefully on decode errors by reporting and skipping the file), parse it with `cst.parse_module`, catch and report.g., syntax errors) without crashing the whole run, apply the transformer via `module.visit(...)`, and generate the new code with `module.code`.
- Only write the file if the content actually changed; in check mode, just report changed files and set a non-zero exit code if any would change.
- Preserve the original file's line endings and trailing newline behavior as far as libcst allows.

**Parallelism**
- Use `multiprocessing.Pool` to process files concurrently. The number of workers is `min(requested_workers, MAX_WORKERS)` and at least 1. Use `imap_unordered` or `apply_async` with `AsyncResult` to collect results, and ensure per-file exceptions are caught in the worker function and returned as status messages rather than crashing the pool.
- Guard the entry point with `if __name__ == "__main__":` so multiprocessing works correctly.
- Sort or deterministically order the reported results for stable output.

**Error handling and edge cases**
- Skip non-existent paths with a warning to stderr.
- Skip non-`.py` files when given explicitly as files, or ignore them during directory traversal.
- Skip directories such as `__pycache__`, `.git`, and virtual environment folders during recursive search.
- Handle `KeyboardInterrupt` gracefully by terminating the pool and exiting with status 130.
- Return exit code 0 on success, 1 if any file failed to process or (in check mode) would change, and 2 for argument errors.
- Empty files and files containing only comments should be handled without crashing.

**Output and usage**
- Print a concise per-file status line for changed, unchanged, and failed files, and a final summary with counts.
- Include a module docstring at the top describing usage examples.
- Use only the standard library plus `libcst` as the third-party dependency; import `libcst` as `cst`.
- Include type annotations throughout, using `Final` for constants and `TYPE_CHECKING` guards for type-only imports such as `Sequence` and `AsyncResult`.

Deliver the complete script in a single file with all imports, constants, the transformer class, the worker function, the argument parsing, and the `main` entry point.
---"""

from __future__ import annotations

import argparse
import ast
import sys
from multiprocessing import Pool
from pathlib import Path
from typing import TYPE_CHECKING, Final

import libcst as cst

if TYPE_CHECKING:
    from collections.abc import Sequence
    from multiprocessing.pool import AsyncResult
MAX_WORKERS: Final[int] = 8
PRESERVE_PREFIXES: Final[tuple[str, ...]] = ("#!", "# type:", "# fmt:")
PRESERVE_EXACT: Final[frozenset[str]] = frozenset({"# fmt: skip", "# fmt: on", "# fmt: off"})


def should_preserve_comment(comment_text: str) -> bool:
    stripped: str = comment_text.strip()
    return stripped.startswith(PRESERVE_PREFIXES) or stripped in PRESERVE_EXACT


class StripTransformer(cst.CSTTransformer):
    def leave_Comment(
        self, original_node: cst.Comment, updated_node: cst.Comment
    ) -> cst.BaseLeaf | cst.RemovalSentinel:
        if should_preserve_comment(updated_node.value):
            return updated_node
        return cst.RemovalSentinel.REMOVE

    @staticmethod
    def _strip_leading_string(
        body: Sequence[cst.BaseStatement],
    ) -> tuple[cst.BaseStatement, ...]:
        if not body:
            return tuple(body)
        first: cst.BaseStatement = body[0]
        if (
            isinstance(first, cst.SimpleStatementLine)
            and len(first.body) == 1
            and isinstance(first.body[0], cst.Expr)
            and isinstance(first.body[0].value, cst.SimpleString)
        ):
            return tuple(body[1:])
        return tuple(body)

    def _strip_suite(self, suite: cst.BaseSuite) -> cst.BaseSuite:
        if isinstance(suite, cst.IndentedBlock):
            new_body: tuple[cst.BaseStatement, ...] = self._strip_leading_string(suite.body)
            if not new_body:
                new_body = (cst.SimpleStatementLine(body=[cst.Pass()]),)
            return suite.with_changes(body=new_body)
        if isinstance(suite, cst.SimpleStatementSuite):
            new_body: tuple[cst.BaseStatement, ...] = self._strip_leading_string(suite.body)
            if not new_body:
                new_body = (cst.Pass(),)
            return suite.with_changes(body=new_body)
        return suite

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        new_body: tuple[cst.BaseStatement, ...] = self._strip_leading_string(updated_node.body)
        return updated_node.with_changes(body=new_body)

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        return updated_node.with_changes(body=self._strip_suite(updated_node.body))

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        return updated_node.with_changes(body=self._strip_suite(updated_node.body))


def process_file(file_path: Path) -> str:
    try:
        source: str = file_path.read_text(encoding="utf-8")
    except Exception as exc:
        return f"[ERROR] Failed to read {file_path}: {exc}"
    try:
        module: cst.Module = cst.parse_module(source)
    except cst.ParserSyntaxError as exc:
        return f"[ERROR] Failed to parse {file_path}: {exc}"
    try:
        transformer: StripTransformer = StripTransformer()
        new_module: cst.Module = module.visit(transformer)
    except Exception as exc:
        return f"[ERROR] Transformation failed for {file_path}: {exc}"
    final_code: str = new_module.code
    if final_code == source:
        return f"[SKIPPED] No structural modifications needed for {file_path}"
    try:
        ast.parse(final_code, filename=str(file_path))
    except SyntaxError as exc:
        return f"[WARNING] Validation failed for {file_path} (Changes rejected): {exc}"
    try:
        file_path.write_text(final_code, encoding="utf-8")
        return f"[SUCCESS] Processed and stripped: {file_path}"
    except Exception as exc:
        return f"[ERROR] Failed to save updates to {file_path}: {exc}"


def gather_files(inputs: list[str]) -> list[Path]:
    files: set[Path] = set()
    if not inputs:
        files.update(Path().rglob("*.py"))
        return sorted(files)
    for item in inputs:
        p: Path = Path(item)
        if p.is_file() and p.suffix == ".py":
            files.add(p)
        elif p.is_dir():
            files.update(p.rglob("*.py"))
    return sorted(files)


def main() -> None:
    parser = argparse.ArgumentParser(description="Strip comments and docstrings using libcst safely.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Target files or directories to process. Defaults to '.' if empty.",
    )
    args: argparse.Namespace = parser.parse_args()
    targets: list[Path] = gather_files(args.paths)
    if not targets:
        print("No target Python source files detected.")
        sys.exit(0)
    print(f"Queue loaded. Processing {len(targets)} target files via Parallel Pipeline...")
    with Pool(processes=MAX_WORKERS) as pool:
        async_results: list[AsyncResult[str]] = [pool.apply_async(process_file, (target,)) for target in targets]
        for async_res in async_results:
            result_string: str = async_res.get()
            print(result_string)


if __name__ == "__main__":
    raise SystemExit(main())
