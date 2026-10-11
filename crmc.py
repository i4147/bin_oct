#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python command-line tool that bulk-upgrades Python source files to target Python 3.12 syntax using LibCST and Loguru, with an 8-worker multiprocessing pool, bounded async submission, directory walking with default excludes, and in-place or check/diff modes. Describe the required behavior, inputs, outputs, dependencies, error handling, and edge cases, without any code or code snippets.

Reproduce a command-line tool that bulk-modernizes Python source files to Python 3.12 syntax. It is designed to run under Termux on Android (shebang targets `/data/data/com.termux/files/usr/bin/env python`) but should be portable to any POSIX system.

**Purpose**
The tool takes one or more file or directory paths, finds Python source files (`.py`, `.pyw`, `.pyi`), and rewrites them in place (or reports what would change) using a set of syntax-modernization transforms targeting Python 3.12. Transforms are implemented with LibCST so that formatting, comments, and layout are preserved as far as possible. Logging goes through Loguru.

**Dependencies**
- Standard library only beyond the following: `libcst` (for concrete-syntax-tree rewriting) and `loguru` (for logging).
- Use `argparse` for the CLI, `multiprocessing` (`Pool`, `AsyncResult`) for parallelism, `tokenize`/`ast`/`codecs` for source detection and validation, `difflib` for unified diffs, `signal` for interrupt handling, `tempfile` plus `shutil` for atomic writes, `pathlib` for paths, `enum` for mode/result types, `dataclasses` for result records, and `functools`/`collections.deque` as needed.
- Use `typing.Final`, `Literal`, and `get_args` for constants and type hints.

**Constants (must be exactly these)**
- Exactly 8 worker processes (`NUM_WORKERS = 8`, a hard requirement).
- `CHUNKSIZE = 16` for map-like pool calls.
- `MAX_IN_FLIGHT = NUM_WORKERS * 8` as the bound on outstanding `apply_async` tasks to cap memory use.
- Target Python version string `"3.12"` and tuple `(3, 12)`.
- Python source suffixes: `.py`, `.pyw`, `.pyi`.
- Default directory excludes (never descended into during directory walks): `.git`, `.hg`, `.svn`, `.tox`, `.nox`, `.venv`, `venv`, `.eggs`, `__pycache__`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `node_modules`.

**CLI behavior**
- Positional arguments: one or more paths (files or directories). Directories are walked recursively, skipping default excludes and any extra user-supplied exclude patterns.
- Support a mode selector with a `Literal`/enum-backed set of choices so the transform set can be selected or the default used; the set of valid mode values must be derived from typing `get_args` on a `Literal` type rather than hard-coded in the parser.
- Provide flags for: check-only mode (exit non-zero if any file would change, without writing), diff output (print unified diffs via `difflib`), in-place write (default on), an explicit worker count override only if it does not violate the 8-worker hard requirement (the 8 count is fixed), extra exclude patterns, and verbosity controlling Loguru level.
- Exit codes: 0 when everything is clean or successfully rewritten; non-zero when check mode finds changes, when any file fails to parse, or when an unrecoverable error occurs. Use distinct, documented codes for these categories.

**Processing pipeline**
1. Expand inputs: resolve each path; for directories, walk with `pathlib`, filter by suffix and excludes, and produce a deterministic (sorted) ordering.
2. Detect encoding for each file using `tokenize.detect_encoding` (falling back to UTF-8 on failure) and decode accordingly; preserve the original line endings and any BOM where possible.
3. Parse the source with LibCST. If parsing fails, record an error for that file, log it via Loguru, and continue with the remaining files rather than aborting the whole run.
4. Apply the transform visitors/transformers (LibCST-based) for the selected mode. Transforms should be conservative: only rewrite constructs where the rewrite is provably equivalent for Python 3.12 semantics.
5. Validate output: confirm the rewritten code still parses via `ast.parse` (and compile-check against the target version if feasible). If validation fails, leave the original file untouched and report the failure.
6. If content changed: in check mode, record it; in diff mode, print a unified diff; in write mode, write atomically by writing to a temporary file in the same directory (via `tempfile`) and then `shutil`/`os` replacing the original, preserving file permissions where possible.

**Parallelism**
- Use a `multiprocessing` pool with exactly 8 workers. Use `imap`/`map`-style calls with `CHUNKSIZE` for bulk work, or `apply_async` when streaming results, but when using `apply_async` cap the number of outstanding `AsyncResult` objects at `MAX_IN_FLIGHT` using a `deque` as a sliding window, draining results in submission order.
- Each worker processes one file and returns a dataclass-based result record (path, status enum, changed flag, error message, and optional diff text). Results must be picklable.
- Worker initialization should configure signal handling so that `SIGINT` is handled gracefully in the parent: the parent catches KeyboardInterrupt, terminates the pool cleanly, logs the interruption, and exits with a distinct interrupted exit code. Workers should ignore `SIGINT` so only the parent handles it.
- Guard the entry point with `if __name__ == "__main__":` and set the multiprocessing start method safely (for example, `spawn` or `fork` as appropriate for the platform) before creating the pool.

**Error handling**
- Per-file errors (decode failure, parse failure, validation failure, I/O error on write) must not crash the run; they are logged and counted in the summary.
- Unreadable directories or nonexistent input paths: log an error and continue; if no valid inputs remain, exit with the usage/error code.
- Never leave temporary files behind on failure; clean them up in `finally`.
- Catch `OSError` and `UnicodeDecodeError` specifically where relevant.

**Logging and output**
- Use Loguru for all diagnostics (no bare `print` for log-type messages). Diff output and the final summary may go to stdout.
- Final summary: counts of files scanned, changed, unchanged, failed, and skipped, plus the list of failures.

**Edge cases to handle**
- Empty files and files with only comments or whitespace.
- Files that are already modernized (no change; should report unchanged, no write).
- Symlinks: do not follow symlinked directories during the walk to avoid cycles; decide consistently for symlinked files and document the choice.
- Files with CRLF line endings, mixed endings, a UTF-8 BOM, or non-UTF-8 encodings declared in a coding cookie.
- Very large files: the pipeline should not hold more than the bounded number of in-flight tasks at once.
- Read-only files: fail that file with a clear error rather than crashing.
- Duplicate paths given on the command line should be processed once.
- Non-Python files passed explicitly on the command line: skip with a logged warning unless they have a recognized suffix.

**Usage and execution**
- Run as an executable script with the Termux-style shebang; also invocable via `python` with the file path.
- Provide `--help` with descriptive text for every option.
- Ensure the code is structured with a `main(argv)` function returning an integer exit code, invoked via `sys.exit(main())` under the `__main__` guard.

Produce the complete script that satisfies all of the above.
---"""

import argparse
import ast
import codecs
import difflib
import enum
import functools
import io
import multiprocessing as mp
import os
import re
import shutil
import signal
import sys
import tempfile
import tokenize
from collections import deque
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from multiprocessing.pool import AsyncResult, Pool
from pathlib import Path
from typing import Final, Literal, get_args

import libcst as cst
from loguru import logger

NUM_WORKERS: Final[int] = 8
"""Exact number of worker processes in the pool (a hard requirement)."""

CHUNKSIZE: Final[int] = 16
"""Chunk size for map-like pool methods; amortises IPC overhead on big trees."""

MAX_IN_FLIGHT: Final[int] = NUM_WORKERS * 8
"""Upper bound of outstanding tasks for ``apply_async`` (bounds memory use)."""

TARGET_PYTHON: Final[str] = "3.12"
TARGET_VERSION: Final[tuple[int, int]] = (3, 12)

PY_SUFFIXES: Final[frozenset[str]] = frozenset({".py", ".pyw", ".pyi"})
"""Extensions picked up while walking directories."""

DEFAULT_EXCLUDES: Final[frozenset[str]] = frozenset({
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".nox",
    ".venv",
    "venv",
    ".eggs",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
})
"""Directory names that are never descended into while walking a directory."""

PoolMethod = Literal["map", "imap", "imap_unordered", "apply", "apply_async", "starmap"]
POOL_METHODS: Final[tuple[str, ...]] = get_args(PoolMethod)

_PRESERVED_COMMENT: Final[re.Pattern[str]] = re.compile(r"#\s*(?:type|fmt):")
_UTF8_COMPATIBLE: Final[frozenset[str]] = frozenset({"utf-8", "utf-8-sig", "ascii", "us-ascii"})


class Status(enum.StrEnum):
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Options:
    dry_run: bool = False
    backup: bool = False
    want_diff: bool = False
    fallback_encoding: str | None = None


@dataclass(frozen=True, slots=True)
class FileResult:
    path: Path
    status: Status
    bytes_before: int = 0
    bytes_after: int = 0
    comments_removed: int = 0
    docstrings_removed: int = 0
    diff: str = ""
    message: str = ""

    @property
    def bytes_saved(self) -> int:
        return self.bytes_before - self.bytes_after


@dataclass(slots=True)
class Summary:
    scanned: int = 0
    changed: int = 0
    unchanged: int = 0
    skipped: int = 0
    failed: int = 0
    missing: int = 0
    bytes_processed: int = 0
    bytes_saved: int = 0
    comments: int = 0
    docstrings: int = 0

    def add(self, result: FileResult) -> None:
        self.scanned += 1
        match result.status:
            case Status.CHANGED:
                self.changed += 1
                self.bytes_saved += result.bytes_saved
                self.comments += result.comments_removed
                self.docstrings += result.docstrings_removed
                self.bytes_processed += result.bytes_before
            case Status.UNCHANGED:
                self.unchanged += 1
                self.bytes_processed += result.bytes_before
            case Status.SKIPPED:
                self.skipped += 1
            case Status.FAILED:
                self.failed += 1


class SkipFile(Exception):
    pass


def _is_preserved(comment: str) -> bool:
    return _PRESERVED_COMMENT.match(comment) is not None


def _is_plain_string(expr: cst.BaseExpression) -> bool:
    if isinstance(expr, cst.SimpleString):
        return "b" not in expr.prefix.lower()
    if isinstance(expr, cst.ConcatenatedString):
        return _is_plain_string(expr.left) and _is_plain_string(expr.right)
    return False


def _is_docstring_statement(stmt: cst.BaseSmallStatement) -> bool:
    return isinstance(stmt, cst.Expr) and _is_plain_string(stmt.value)


class StripCommentsAndDocstrings(cst.CSTTransformer):
    def __init__(self, *, has_shebang: bool) -> None:
        super().__init__()
        self.comments_removed: int = 0
        self.docstrings_removed: int = 0
        self._shebang_pending: bool = has_shebang

    def leave_EmptyLine(
        self, original_node: cst.EmptyLine, updated_node: cst.EmptyLine
    ) -> cst.EmptyLine | cst.RemovalSentinel:
        comment = updated_node.comment
        if self._shebang_pending:
            self._shebang_pending = False
            if comment is not None and comment.value.startswith("#!"):
                return updated_node
        if comment is None or _is_preserved(comment.value):
            return updated_node
        self.comments_removed += 1
        return cst.RemoveFromParent()

    def leave_TrailingWhitespace(
        self,
        original_node: cst.TrailingWhitespace,
        updated_node: cst.TrailingWhitespace,
    ) -> cst.TrailingWhitespace:
        comment = updated_node.comment
        if comment is None or _is_preserved(comment.value):
            return updated_node
        self.comments_removed += 1
        return updated_node.with_changes(comment=None, whitespace=cst.SimpleWhitespace(""))

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        return updated_node.with_changes(body=self._strip_docstring(updated_node.body))

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        return updated_node.with_changes(body=self._strip_docstring(updated_node.body))

    def _strip_docstring(self, body: cst.BaseSuite) -> cst.BaseSuite:
        if isinstance(body, cst.SimpleStatementSuite):
            small = body.body
            if not small or not _is_docstring_statement(small[0]):
                return body
            self.docstrings_removed += 1
            rest = small[1:]
            return body.with_changes(body=rest if rest else [cst.Pass()])

        if not isinstance(body, cst.IndentedBlock) or not body.body:
            return body
        first = body.body[0]
        if (
            not isinstance(first, cst.SimpleStatementLine)
            or not first.body
            or not _is_docstring_statement(first.body[0])
        ):
            return body

        self.docstrings_removed += 1
        rest_of_line = first.body[1:]
        rest_of_block = body.body[1:]
        if rest_of_line:
            new_first = first.with_changes(body=rest_of_line)
            return body.with_changes(body=(new_first, *rest_of_block))
        if rest_of_block:
            return body.with_changes(body=rest_of_block)
        return body.with_changes(body=(first.with_changes(body=[cst.Pass()]),))


def _check_declared_encoding(raw: bytes) -> None:
    try:
        declared, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
    except (SyntaxError, LookupError):
        return
    if declared.lower() not in _UTF8_COMPATIBLE:
        raise SkipFile(f"declares non-UTF-8 source encoding {declared!r}")


def _decode_source(raw: bytes, fallback: str | None) -> tuple[str, str, bytes]:
    if b"\x00" in raw:
        raise SkipFile("binary or non-text content (NUL bytes)")
    _check_declared_encoding(raw)

    bom = b""
    if raw.startswith(codecs.BOM_UTF8):
        bom, raw = codecs.BOM_UTF8, raw[len(codecs.BOM_UTF8) :]
    try:
        return raw.decode("utf-8"), "utf-8", bom
    except UnicodeDecodeError as exc:
        utf8_error = exc

    if fallback is None or bom:
        raise SkipFile(
            f"not valid UTF-8 ({utf8_error.reason} at byte {utf8_error.start}); use --fallback-encoding to process it"
        ) from utf8_error
    try:
        return raw.decode(fallback), fallback, b""
    except UnicodeDecodeError as exc:
        raise SkipFile(f"cannot decode as UTF-8 or {fallback}: {exc.reason}") from exc


def strip_source(source: str) -> tuple[str, int, int]:
    module = cst.parse_module(source, config=cst.PartialParserConfig(python_version=TARGET_PYTHON))
    transformer = StripCommentsAndDocstrings(has_shebang=source.startswith("#!"))
    new_module = module.visit(transformer)
    return new_module.code, transformer.comments_removed, transformer.docstrings_removed


def _make_diff(path: Path, old: str, new: str) -> str:
    diff = "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )
    return diff if not diff or diff.endswith("\n") else diff + "\n"


def _make_backup(path: Path) -> None:
    backup = path.with_name(path.name + ".bak")
    if backup.exists():
        raise FileExistsError(f"backup already exists: {backup}")
    shutil.copy2(path, backup)


def _atomic_write(path: Path, data: bytes) -> None:
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with tmp.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        shutil.copymode(path, tmp)
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def _process_file(path: Path, options: Options) -> FileResult:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return FileResult(path, Status.FAILED, message=f"cannot read file: {exc}")

    try:
        source, encoding, bom = _decode_source(raw, options.fallback_encoding)
    except SkipFile as exc:
        return FileResult(path, Status.SKIPPED, message=str(exc))

    try:
        new_source, n_comments, n_docstrings = strip_source(source)
    except cst.ParserSyntaxError:
        return FileResult(path, Status.SKIPPED, message=f"not valid Python {TARGET_PYTHON} source")

    if new_source == source:
        return FileResult(path, Status.UNCHANGED, bytes_before=len(raw), bytes_after=len(raw))

    try:
        ast.parse(new_source, filename=str(path), feature_version=TARGET_VERSION)
    except (SyntaxError, ValueError, RecursionError) as exc:
        return FileResult(
            path,
            Status.FAILED,
            message=f"transformed code failed validation, file untouched: {exc}",
        )

    new_raw = bom + new_source.encode(encoding)
    diff = _make_diff(path, source, new_source) if options.want_diff else ""
    changed = FileResult(
        path,
        Status.CHANGED,
        bytes_before=len(raw),
        bytes_after=len(new_raw),
        comments_removed=n_comments,
        docstrings_removed=n_docstrings,
        diff=diff,
    )
    if options.dry_run:
        return changed

    if not os.access(path, os.W_OK):
        return FileResult(path, Status.FAILED, message="file is not writable (permission denied)")
    try:
        if options.backup:
            _make_backup(path)
        _atomic_write(path, new_raw)
    except OSError as exc:
        return FileResult(path, Status.FAILED, message=f"cannot write file: {exc}")
    return changed


def process_file(path: Path, options: Options) -> FileResult:
    try:
        return _process_file(path, options)
    except Exception as exc:
        return FileResult(path, Status.FAILED, message=f"unexpected {type(exc).__name__}: {exc}")


def _init_worker() -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def _looks_like_python_script(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            first_line = handle.readline(256)
    except OSError:
        return False
    return first_line.startswith(b"#!") and b"python" in first_line


def _log_walk_error(error: OSError) -> None:
    logger.warning("Cannot traverse {}: {}", error.filename, error.strerror or error)


def iter_python_files(targets: Iterable[Path], excludes: frozenset[str]) -> Iterator[Path]:
    seen: set[Path] = set()
    for target in targets:
        resolved = target.resolve()
        if resolved.is_file():
            if resolved not in seen:
                seen.add(resolved)
                yield resolved
            continue
        for root, dirnames, filenames in resolved.walk(on_error=_log_walk_error):
            dirnames[:] = sorted(d for d in dirnames if d not in excludes and not d.endswith(".egg-info"))
            for name in sorted(filenames):
                candidate = root / name
                if candidate.is_symlink():
                    continue
                if candidate.suffix in PY_SUFFIXES or (not candidate.suffix and _looks_like_python_script(candidate)):
                    if candidate not in seen:
                        seen.add(candidate)
                        yield candidate


def iter_results(pool: Pool, method: PoolMethod, paths: Iterable[Path], options: Options) -> Iterator[FileResult]:
    worker = functools.partial(process_file, options=options)
    match method:
        case "map":
            yield from pool.map(worker, list(paths), chunksize=CHUNKSIZE)
        case "starmap":
            yield from pool.starmap(process_file, [(path, options) for path in paths], chunksize=CHUNKSIZE)
        case "imap":
            yield from pool.imap(worker, paths, chunksize=CHUNKSIZE)
        case "imap_unordered":
            yield from pool.imap_unordered(worker, paths, chunksize=CHUNKSIZE)
        case "apply":
            for path in paths:
                yield pool.apply(process_file, (path, options))
        case "apply_async":
            pending: deque[AsyncResult[FileResult]] = deque()
            for path in paths:
                pending.append(pool.apply_async(process_file, (path, options)))
                if len(pending) >= MAX_IN_FLIGHT:
                    yield pending.popleft().get()
            while pending:
                yield pending.popleft().get()


def report_result(result: FileResult, *, stats: bool, options: Options) -> None:
    match result.status:
        case Status.CHANGED:
            tag = "[dry-run] " if options.dry_run else ""
            if stats:
                detail = f"{result.comments_removed:,} comments, {result.docstrings_removed:,} docstrings removed"
            else:
                detail = f"{result.bytes_saved:,} bytes reduced ({result.bytes_before:,} -> {result.bytes_after:,})"
            print(f"{tag}{result.path.name}: {detail}")
            if result.diff:
                sys.stdout.write(result.diff)
        case Status.UNCHANGED:
            logger.debug("Unchanged: {}", result.path)
        case Status.SKIPPED:
            logger.warning("Skipped {}: {}", result.path, result.message)
        case Status.FAILED:
            logger.error("Failed {}: {}", result.path, result.message)


def print_summary(summary: Summary, *, options: Options, interrupted: bool = False) -> None:
    verb = "would be saved" if options.dry_run else "saved"
    pct = (summary.bytes_saved / summary.bytes_processed * 100) if summary.bytes_processed else 0.0
    print()
    if interrupted:
        print("Interrupted - partial results:")
    print(
        f"Files: {summary.scanned} scanned, {summary.changed} changed, "
        f"{summary.unchanged} unchanged, {summary.skipped} skipped, "
        f"{summary.failed} failed, {summary.missing} missing"
    )
    print(f"Removed: {summary.comments:,} comments and {summary.docstrings:,} docstrings")
    print(f"Total space {verb}: {summary.bytes_saved:,} bytes ({pct:.1f}% of {summary.bytes_processed:,})")


def _codec_name(value: str) -> str:
    try:
        codecs.lookup(value)
    except LookupError as exc:
        raise argparse.ArgumentTypeError(f"unknown encoding: {value!r}") from exc
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="strip_comments",
        description="Strip comments and docstrings from Python files in place (libcst).",
        epilog="Kept: shebang, module docstring, '# type:' and '# fmt:' comments.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="files or directories to process recursively (default: current directory)",
    )
    parser.add_argument(
        "--pool-method",
        choices=POOL_METHODS,
        default="imap_unordered",
        help="multiprocessing.Pool dispatch method (default: %(default)s)",
    )
    parser.add_argument(
        "-n",
        "--stats",
        action="store_true",
        help="report the number of comments and docstrings removed per file",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="show what would change without writing anything",
    )
    parser.add_argument("--diff", action="store_true", help="print a unified diff of every change")
    parser.add_argument(
        "--backup",
        action="store_true",
        help="copy each file to '<name>.bak' before modifying it (never overwrites a .bak)",
    )
    parser.add_argument(
        "--fallback-encoding",
        type=_codec_name,
        metavar="ENCODING",
        help="decode files that are not valid UTF-8 with ENCODING (e.g. cp1252) and "
        "write them back in that encoding; by default such files are skipped",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="DIRNAME",
        help="extra directory name to skip while walking (repeatable)",
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    verbosity.add_argument("-q", "--quiet", action="store_true", help="only log errors")
    return parser


def configure_logging(*, verbose: bool, quiet: bool) -> None:
    logger.remove()
    level = "DEBUG" if verbose else "ERROR" if quiet else "INFO"
    logger.add(sys.stderr, level=level, format="<level>{level: <8}</level> | {message}")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose, quiet=args.quiet)

    options = Options(
        dry_run=args.dry_run,
        backup=args.backup,
        want_diff=args.diff,
        fallback_encoding=args.fallback_encoding,
    )
    summary = Summary()

    targets: list[Path] = []
    for raw_target in args.paths or [Path.cwd()]:
        if raw_target.exists():
            targets.append(raw_target)
        else:
            logger.error("Path does not exist: {}", raw_target)
            summary.missing += 1

    excludes = DEFAULT_EXCLUDES | frozenset(args.exclude)
    logger.info(
        "Processing {} target(s) with {} workers (method={}{})",
        len(targets),
        NUM_WORKERS,
        args.pool_method,
        ", dry-run" if options.dry_run else "",
    )

    interrupted = False
    try:
        with mp.Pool(processes=NUM_WORKERS, initializer=_init_worker) as pool:
            paths = iter_python_files(targets, excludes)
            for result in iter_results(pool, args.pool_method, paths, options):
                summary.add(result)
                report_result(result, stats=args.stats, options=options)
            pool.close()
            pool.join()
    except KeyboardInterrupt:
        interrupted = True
        logger.warning("Interrupted; files are written atomically so none are corrupted")

    if summary.scanned == 0 and not interrupted:
        logger.warning("No Python files found")
    print_summary(summary, options=options, interrupted=interrupted)

    if interrupted:
        return 130
    return 1 if (summary.failed or summary.missing) else 0


if __name__ == "__main__":
    if sys.version_info < (3, 12):
        sys.exit("strip_comments requires Python 3.12 or newer")
    raise SystemExit(main())
