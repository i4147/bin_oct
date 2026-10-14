#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that cleans up source code by stripping documentation and comments from every Python file within a given directory tree, while preserving the program's runtime behavior and syntactic validity.
The tool should accept a root folder (or a list of files) and recursively discover all Python source files beneath it. For each file, it should parse the source into a concrete syntax tree that preserves formatting, then remove docstrings from modules, classes, and functions, and strip ordinary comments from the code. Whenever removing a docstring or comment would leave a function, class, or block with an empty body, the tool should insert a minimal placeholder statement so the code remains valid.
Processing should be parallelized across a fixed pool of worker processes so that large codebases are handled efficiently. Each file should be handled independently, and a failure on one file (such as a syntax error or unreadable file) must not stop the rest of the batch; the failure should be logged and the file reported as skipped.
Provide an option to run in a dry-run or report-only mode that shows what would change without modifying any files. By default, changed files should be rewritten in place only when their content actually differs from the original, and unchanged files should be left untouched.
At the end of the run, produce a concise summary that reports, for each processed file, how many docstrings were removed, how many comments were removed, how many placeholder statements were inserted, and whether the file was written or skipped, along with overall totals. Use structured, readable logging throughout so the user can follow progress and diagnose problems.
The script should be runnable from the command line, accept the target path as an argument, and exit with a non-zero status if any file could not be processed.
---"""

from __future__ import annotations
import ast
from dataclasses import dataclass
import multiprocessing as mp
from pathlib import Path
import sys
from typing import Sequence
import libcst as cst
from loguru import logger

WORKERS: int = 8


@dataclass(slots=True)
class FileReport:
    path: Path
    docstrings_removed: int = 0
    comments_removed: int = 0
    pass_inserted: int = 0
    written: bool = False
    skipped: bool = False


def _pass_stmt() -> cst.SimpleStatementLine:
    return cst.SimpleStatementLine(body=[cst.Pass()])


def _is_docstring_small(stmt: cst.BaseSmallStatement) -> bool:
    return isinstance(stmt, cst.Expr) and isinstance(stmt.value, (cst.SimpleString, cst.ConcatenatedString))


def _is_docstring_stmt(stmt: cst.BaseStatement) -> bool:
    return isinstance(stmt, cst.SimpleStatementLine) and len(stmt.body) == 1 and _is_docstring_small(stmt.body[0])


def _strip_first_docstring(
    stmts: Sequence[cst.BaseStatement],
    counters: dict[str, int],
    *,
    ensure_body: bool = False,
) -> Sequence[cst.BaseStatement]:
    new = list(stmts)
    if new and _is_docstring_stmt(new[0]):
        new = new[1:]
        counters["docstrings"] += 1
    if ensure_body and not new:
        new = [_pass_stmt()]
        counters["passes"] += 1
    return new


def _strip_suite(body: cst.BaseSuite, counters: dict[str, int]) -> cst.BaseSuite:
    if isinstance(body, cst.IndentedBlock):
        new_inner = _strip_first_docstring(body.body, counters, ensure_body=True)
        return body.with_changes(body=new_inner)
    if isinstance(body, cst.SimpleStatementSuite):
        inner = list(body.body)
        if inner and _is_docstring_small(inner[0]):
            inner = inner[1:]
            counters["docstrings"] += 1
        if not inner:
            inner = [cst.Pass()]
            counters["passes"] += 1
        return body.with_changes(body=inner)
    return body


class StripTransformer(cst.CSTTransformer):
    def __init__(self) -> None:
        super().__init__()
        self.counters: dict[str, int] = {
            "docstrings": 0,
            "comments": 0,
            "passes": 0,
        }

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        return updated_node.with_changes(body=_strip_first_docstring(updated_node.body, self.counters))

    def _strip_callable(
        self,
        updated_node: cst.FunctionDef | cst.AsyncFunctionDef | cst.ClassDef,
    ) -> cst.FunctionDef | cst.AsyncFunctionDef | cst.ClassDef:
        new_body = _strip_suite(updated_node.body, self.counters)
        if new_body is updated_node.body:
            return updated_node
        return updated_node.with_changes(body=new_body)

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        result = self._strip_callable(updated_node)
        assert isinstance(result, cst.FunctionDef)
        return result

    def leave_AsyncFunctionDef(
        self,
        original_node: cst.AsyncFunctionDef,
        updated_node: cst.AsyncFunctionDef,
    ) -> cst.AsyncFunctionDef:
        result = self._strip_callable(updated_node)
        assert isinstance(result, cst.AsyncFunctionDef)
        return result

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        result = self._strip_callable(updated_node)
        assert isinstance(result, cst.ClassDef)
        return result

    def leave_TrailingWhitespace(
        self,
        original_node: cst.TrailingWhitespace,
        updated_node: cst.TrailingWhitespace,
    ) -> cst.TrailingWhitespace:
        if updated_node.comment is not None:
            self.counters["comments"] += 1
            return updated_node.with_changes(comment=None)
        return updated_node

    def leave_EmptyLine(self, original_node: cst.EmptyLine, updated_node: cst.EmptyLine) -> cst.EmptyLine:
        if updated_node.comment is not None:
            self.counters["comments"] += 1
            return updated_node.with_changes(comment=None)
        return updated_node


def process_file(path: Path) -> FileReport:
    report = FileReport(path=path)
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        logger.error("skip (not utf-8) {}: {}", path, exc)
        report.skipped = True
        return report
    except OSError as exc:
        logger.error("skip (read error) {}: {}", path, exc)
        report.skipped = True
        return report
    try:
        module = cst.parse_module(source)
    except cst.ParserSyntaxError as exc:
        logger.error("skip (parse error) {}: {}", path, exc)
        report.skipped = True
        return report
    transformer = StripTransformer()
    try:
        new_module = module.visit(transformer)
    except Exception as exc:
        logger.exception("transformer crashed on {}: {}", path, exc)
        report.skipped = True
        return report
    report.docstrings_removed = transformer.counters["docstrings"]
    report.comments_removed = transformer.counters["comments"]
    report.pass_inserted = transformer.counters["passes"]
    new_code = new_module.code
    if new_code == source:
        logger.debug("unchanged {}", path)
        return report
    try:
        ast.parse(new_code)
    except SyntaxError as exc:
        logger.error("skip (invalid output, not writing) {}: {}", path, exc)
        report.skipped = True
        return report
    try:
        cst.parse_module(new_code)
    except cst.ParserSyntaxError as exc:
        logger.error("skip (libcst rejects output, not writing) {}: {}", path, exc)
        report.skipped = True
        return report
    try:
        path.write_text(new_code, encoding="utf-8")
    except OSError as exc:
        logger.error("skip (write error) {}: {}", path, exc)
        report.skipped = True
        return report
    report.written = True
    print(f"{path} | {report.docstrings_removed}| {report.comments_removed} | {report.pass_inserted}\n")
    return report


def _collect_python_files(inputs: Sequence[Path]) -> list[Path]:
    seen: set[Path] = set()
    collected: list[Path] = []
    for raw in inputs:
        path = raw.expanduser()
        if path.is_file():
            if path.suffix == ".py":
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    collected.append(resolved)
            else:
                logger.warning("ignoring non-Python file: {}", path)
        elif path.is_dir():
            for candidate in path.rglob("*.py"):
                resolved = candidate.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    collected.append(resolved)
        else:
            logger.warning("path does not exist: {}", path)
    collected.sort()
    return collected


def _configure_logger() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format=(
            "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{process.name}</cyan> | {message}"
        ),
        enqueue=True,
    )


def main(argv: Sequence[str] | None = None) -> int:
    _configure_logger()
    raw_args = list(sys.argv[1:] if argv is None else argv)
    inputs = [Path(a) for a in raw_args] if raw_args else [Path()]
    files = _collect_python_files(inputs)
    if not files:
        logger.warning(
            "no Python files found in: {}",
            ", ".join(str(p) for p in inputs),
        )
        return 0
    chunksize = max(1, len(files) // (WORKERS * 4))
    try:
        with mp.Pool(processes=WORKERS) as pool:
            results: list[FileReport] = pool.starmap(
                process_file,
                ((f,) for f in files),
                chunksize=chunksize,
            )
    except KeyboardInterrupt:
        logger.warning("interrupted by user")
        return 130
    written = sum(1 for r in results if r.written)
    skipped = sum(1 for r in results if r.skipped)
    docstrings = sum(r.docstrings_removed for r in results)
    comments = sum(r.comments_removed for r in results)
    passes = sum(r.pass_inserted for r in results)
    return 0 if skipped == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
