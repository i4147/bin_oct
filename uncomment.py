#!/data/data/com.termux/files/usr/bin/env python
"""Write a prompt for an AI coding agent to generate a Python 3.12 command-line tool (designed to run under Termux on Android, with the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that strips comments from source code files across a codebase using `tree-sitter` for accurate, language-aware parsing.

The tool must meet the following requirements:

**Purpose**
A CLI utility that recursively scans a directory (or specific files) for source code files in multiple programming languages, parses each file with the appropriate `tree-sitter` grammar, and removes comment nodes (and optionally other non-essential nodes like plain text in template languages) while preserving code semantics — except it must *not* strip comments that look important (e.g., license/copyright headers, SPDX identifiers, auto-generated markers, linter directives like `# noqa`, `# type: ignore`, `# pragma`, shebangs) unless explicitly forced to.

**Inputs**
- Positional arguments: one or more file or directory paths to process.
- Options to control behavior: recursive directory traversal with configurable skip-directories (default skip set should include common VCS/build/cache folders like `.git`, `node_modules`, `__pycache__`, `dist`, `build`, `.venv`, etc.), include/exclude glob or extension filters, a dry-run mode that reports what would change without writing, an option to force-remove "protected" comments (license headers, SPDX, generated markers, linter pragmas) that are normally preserved via a built-in regex of common protected-comment patterns (covering keywords like "copyright", "(c)", "©", "spdx-", "all rights reserved", "licensed under/to", "@license", "@preserve", "@generated", "auto-generated", "do not edit", etc.), options to control parallelism (number of worker processes and which `multiprocessing.Pool` dispatch method to use — e.g. `imap_unordered`, `imap`, `map`, `starmap`, `apply_async`, `apply`), an option to also strip stray whitespace-only text nodes in markup/template languages, backup creation before modifying files, and verbosity/logging controls (via `loguru`).
- Should auto-detect language per file via file extension mapping to the correct tree-sitter grammar/parser, dynamically loading compiled language grammars (building them if needed/available).

**Processing behavior**
- For each file: read bytes, parse with tree-sitter, walk the syntax tree to find comment nodes (and relevant text nodes depending on language/config), filter out nodes whose content matches the "protected" regex unless force mode is enabled, compute the new file content with comments removed while keeping correct byte offsets (process removals in a way that doesn't corrupt positions, e.g., sorting/removing from the end), and only write back if content actually changed.
- Must support multiprocessing to process many files concurrently across worker processes, with the selected pool dispatch method configurable.
- Must classify and report the result of each file as one of: `stripped` (comments removed), `unchanged` (no comments found or nothing removable), `skipped` (e.g., binary file, unsupported language, protected-only content, excluded by filters), or `error` (parse/read/write failure), aggregating counts into a final summary printed/logged at the end.
- Should use caching (e.g., `functools.cache`) where appropriate to avoid redundant work such as repeated language-loading or regex compilation.
- Should handle errors per-file gracefully (catching exceptions so one bad file doesn't crash the whole batch) and log them with `loguru` at appropriate levels.
- Should support safe temporary file writes (e.g., via `tempfile`) and atomic replacement of the original file, optionally keeping a `.bak` backup copy via `shutil`.

**Outputs**
- Modifies source files in place (removing comments) unless running in dry-run mode, in which case it only reports what would be changed.
- Prints/logs a per-file status and a final summary table/counts (number stripped/unchanged/skipped/errored).
- Exits with an appropriate process exit code reflecting whether errors occurred.

Implement this as a single, well-structured Python script using `argparse` for the CLI, `dataclasses` and `NamedTuple`/`Literal` types for clear internal data modeling, type hints throughout (`from __future__ import annotations`), and idiomatic use of `tree_sitter.Language`, `tree_sitter.Parser`, and `tree_sitter.Node` for parsing and tree traversal.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/XCnhgqRWPMWGwdjCXMVWpD"""

from __future__ import annotations
import argparse
from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from functools import cache
import hashlib
import importlib
import importlib.util
import multiprocessing as mp
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import TYPE_CHECKING, Final, Literal, NamedTuple

from loguru import logger
from tree_sitter import Language, Node, Parser


if TYPE_CHECKING:
    from multiprocessing.pool import Pool


Status = Literal["stripped", "unchanged", "skipped", "error"]
PoolMethod = Literal["imap_unordered", "imap", "map", "starmap", "apply_async", "apply"]
Veto = Callable[[Node, bytes], bool]
POOL_METHODS: Final[tuple[PoolMethod, ...]] = (
    "imap_unordered",
    "imap",
    "map",
    "starmap",
    "apply_async",
    "apply",
)
DEFAULT_SKIP_DIRS: Final[frozenset[str]] = frozenset({
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".tox",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".cache",
    "target",
    "dist",
    "build",
})
COMMENT_TYPES: Final[frozenset[str]] = frozenset({"comment", "line_comment", "block_comment", "Comment"})
TEXT_TYPES: Final[frozenset[str]] = frozenset({"text", "CharData"})
_COMMON: Final[str] = (
    r"copyright|\(c\)\s*\d|\u00a9|spdx-|all rights reserved|permission is hereby granted"
    r"|licensed (?:under|to)|@license|@preserve|@generated|code generated|auto-?generated"
    r"|do not (?:remove|delete|edit|modify)|nosec|noqa|nolint|\bvim?:|-\*-|coding[:=]"
)
_C_FAMILY: Final[str] = r"\A/\*!|clang-format|clang-tidy|NOLINT|coverity|fallthrough|-Wno-|\bpragma\b"
_JS_FAMILY: Final[str] = (
    r"\A/\*!|\A///\s*<|@cc_on|eslint|@ts-|tslint|jshint|biome-ignore|prettier-ignore"
    r"|istanbul|c8 ignore|v8 ignore|webpack(?:Chunk|Mode|Prefetch|Preload)"
    r"|sourceMappingURL|sourceURL|@jsx|@flow|@vite-ignore|[@#]__(?:PURE|NO_SIDE_EFFECTS)__"
)
_SHELL_FAMILY: Final[str] = r"\A#!|shellcheck|shfmt"


class SkipFile(Exception): ...


class ValidationError(Exception): ...


def _is_cgo_preamble(node: Node, src: bytes) -> bool:
    sibling = node.next_sibling
    while sibling is not None and sibling.type in COMMENT_TYPES:
        sibling = sibling.next_sibling
    return (
        sibling is not None
        and sibling.type == "import_declaration"
        and b'"C"' in src[sibling.start_byte : sibling.end_byte]
    )


@dataclass(frozen=True, slots=True)
class LangSpec:
    module: str
    factory: str
    suffixes: frozenset[str]
    keep: re.Pattern[str]
    veto: Veto | None = None


def _spec(
    module: str,
    factory: str,
    suffixes: str,
    extra: str = "",
    veto: Veto | None = None,
) -> LangSpec:
    pattern = "|".join(part for part in (_COMMON, extra) if part)
    return LangSpec(
        module=module,
        factory=factory,
        suffixes=frozenset(suffixes.split()),
        keep=re.compile(pattern, re.IGNORECASE | re.DOTALL),
        veto=veto,
    )


LANGS: Final[dict[str, LangSpec]] = {
    "bash": _spec("tree_sitter_bash", "language", ".sh .bash", _SHELL_FAMILY),
    "zsh": _spec("tree_sitter_zsh", "language", ".zsh", _SHELL_FAMILY),
    "c": _spec("tree_sitter_c", "language", ".c .h", _C_FAMILY),
    "cpp": _spec("tree_sitter_cpp", "language", ".cc .cpp .cxx .hpp .hh .hxx", _C_FAMILY),
    "css": _spec(
        "tree_sitter_css",
        "language",
        ".css",
        r"\A/\*!|sourceMappingURL|@charset|prettier-ignore|stylelint",
    ),
    "go": _spec(
        "tree_sitter_go",
        "language",
        ".go",
        r"\A//go:|\A//\s*\+build|\A//line |\A//export |#cgo|lint:ignore|\A//\s*Code generated",
        veto=_is_cgo_preamble,
    ),
    "html": _spec(
        "tree_sitter_html",
        "language",
        ".html .htm",
        r"\A<!--\s*\[if|\[endif\]|\A<!--!|prettier-ignore"
        r"|\A<!--\s*#(?:include|exec|echo|config|set|if|else|endif)",
    ),
    "javascript": _spec("tree_sitter_javascript", "language", ".js .mjs .cjs .jsx", _JS_FAMILY),
    "typescript": _spec("tree_sitter_typescript", "language_typescript", ".ts .mts .cts", _JS_FAMILY),
    "tsx": _spec("tree_sitter_typescript", "language_tsx", ".tsx", _JS_FAMILY),
    "json": _spec("tree_sitter_json", "language", ".json .jsonc"),
    "lua": _spec(
        "tree_sitter_lua",
        "language",
        ".lua",
        r"\A---\s*@|luacheck|stylua|selene|luacov|@diagnostic",
    ),
    "php": _spec(
        "tree_sitter_php",
        "language_php",
        ".php .phtml",
        r"\A#!|phpcs|phpstan|psalm|php-cs-fixer|noinspection|@var|@codeCoverageIgnore",
    ),
    "ruby": _spec(
        "tree_sitter_ruby",
        "language",
        ".rb .rake .gemspec",
        r"\A#!|frozen_string_literal|rubocop|:nodoc:|:nocov:|typed:|sorbet|steep:"
        r"|shareable_constant_value|warn_indent",
    ),
    "rust": _spec(
        "tree_sitter_rust",
        "language",
        ".rs",
        r"rustfmt|clippy|SAFETY:|cbindgen",
    ),
    "toml": _spec("tree_sitter_toml", "language", ".toml", r"taplo|\A#:schema|:schema"),
    "xml": _spec(
        "tree_sitter_xml",
        "language_xml",
        ".xml .xsd .xsl .xslt .svg",
        r"\A<!--!|\A<!--\s*\[if|noinspection|xmllint",
    ),
    "vim": _spec("tree_sitter_vim", "language", ".vim"),
}
AVAILABLE: Final[dict[str, LangSpec]] = {
    name: spec for name, spec in LANGS.items() if importlib.util.find_spec(spec.module) is not None
}
SUFFIX_TO_LANG: Final[dict[str, str]] = {suffix: name for name, spec in AVAILABLE.items() for suffix in spec.suffixes}


class Task(NamedTuple):
    path: Path
    backup: bool
    max_size: int
    dry_run: bool


@dataclass(frozen=True, slots=True)
class Outcome:
    path: str
    status: Status
    before: int = 0
    after: int = 0
    detail: str = ""

    @property
    def saved(self) -> int:
        return self.before - self.after


@dataclass(slots=True)
class Summary:
    counts: Counter[str] = field(default_factory=Counter)
    freed: int = 0
    stripped_before: int = 0

    def record(self, outcome: Outcome) -> None:
        self.counts[outcome.status] += 1
        if outcome.status == "stripped":
            self.freed += outcome.saved
            self.stripped_before += outcome.before


def human(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(value) < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    raise AssertionError


def iter_files(root: Path, skip_dirs: frozenset[str]) -> Iterator[Path]:
    stack: list[Path] = [root]
    while stack:
        current = stack.pop()
        try:
            for entry in current.iterdir():
                if entry.is_symlink():
                    continue
                if entry.is_dir():
                    if entry.name not in skip_dirs:
                        stack.append(entry)
                elif entry.is_file() and entry.suffix.lower() in SUFFIX_TO_LANG:
                    yield entry
        except OSError as exc:
            logger.error("{} | cannot list directory: {}", current, exc)


@cache
def _parser(name: str) -> Parser:
    spec = AVAILABLE[name]
    module = importlib.import_module(spec.module)
    return Parser(Language(getattr(module, spec.factory)()))


def walk(root: Node) -> Iterator[Node]:
    stack: list[Node] = [root]
    while stack:
        node = stack.pop()
        yield node
        if node.type not in COMMENT_TYPES:
            stack.extend(reversed(node.children))


def _flush(digest: hashlib._Hash, pending: list[bytes]) -> None:
    if pending:
        digest.update(b"T\0" + b" ".join(b"".join(pending).split()) + b"\0")
        pending.clear()


def fingerprint(root: Node, src: bytes) -> bytes:
    digest = hashlib.blake2b(digest_size=16)
    pending: list[bytes] = []
    for node in walk(root):
        if node.type in COMMENT_TYPES or node.child_count:
            continue
        chunk = src[node.start_byte : node.end_byte]
        if node.type in TEXT_TYPES:
            pending.append(chunk)
            continue
        _flush(digest, pending)
        digest.update(node.type.encode() + b"\0" + chunk + b"\0")
    _flush(digest, pending)
    return digest.digest()


def _expand(src: bytes, start: int, end: int) -> tuple[int, int]:
    line_start = src.rfind(b"\n", 0, start) + 1
    newline = src.find(b"\n", end)
    line_end = len(src) if newline == -1 else newline
    head = src[line_start:start]
    tail = src[end:line_end]
    if tail.strip():
        return start, end
    if head.strip():
        return start - (len(head) - len(head.rstrip())), end
    return line_start, min(line_end + 1, len(src))


def removal_spans(root: Node, src: bytes, spec: LangSpec) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    floor = 0
    for node in walk(root):
        if node.type not in COMMENT_TYPES:
            continue
        start, end = node.start_byte, node.end_byte
        while end > start and src[end - 1] in b"\r\n":
            end -= 1
        text = src[start:end].decode("utf-8", "replace")
        if spec.keep.search(text) or (spec.veto is not None and spec.veto(node, src)):
            continue
        start, end = _expand(src, start, end)
        start = max(start, floor)
        if start >= end:
            continue
        spans.append((start, end))
        floor = end
    return spans


def strip_comments(data: bytes, lang: str) -> bytes:
    spec = AVAILABLE[lang]
    parser = _parser(lang)
    root = parser.parse(data).root_node
    if root.has_error:
        msg = "source has syntax errors"
        raise SkipFile(msg)
    spans = removal_spans(root, data, spec)
    if not spans:
        return data
    view = memoryview(data)
    parts: list[memoryview] = []
    cursor = 0
    for start, end in spans:
        parts.append(view[cursor:start])
        cursor = end
    parts.append(view[cursor:])
    result = b"".join(parts)
    new_root = parser.parse(result).root_node
    if new_root.has_error:
        msg = "stripped result has syntax errors"
        raise ValidationError(msg)
    if fingerprint(new_root, result) != fingerprint(root, data):
        msg = "stripped result changed the token stream"
        raise ValidationError(msg)
    return result


def commit(path: Path, payload: bytes, backup: bool, ref: os.stat_result) -> None:
    current = path.stat()
    if (current.st_mtime_ns, current.st_size) != (ref.st_mtime_ns, ref.st_size):
        msg = "file modified concurrently"
        raise SkipFile(msg)
    if backup:
        shutil.copy2(path, path.with_name(f"{path.name}.bak"))
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
        shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def process_file(path: Path, backup: bool, max_size: int, dry_run: bool) -> Outcome:
    name = str(path)
    try:
        if path.is_symlink():
            msg = "symlink"
            raise SkipFile(msg)
        lang = SUFFIX_TO_LANG[path.suffix.lower()]
        ref = path.stat()
        if not 0 < ref.st_size <= max_size:
            msg = f"size {ref.st_size} outside accepted range"
            raise SkipFile(msg)
        data = path.read_bytes()
        if b"\0" in data:
            msg = "binary content"
            raise SkipFile(msg)
        result = strip_comments(data, lang)
        if result == data:
            return Outcome(name, "unchanged", len(data), len(data))
        if not dry_run:
            commit(path, result, backup, ref)
        return Outcome(name, "stripped", len(data), len(result))
    except SkipFile as exc:
        return Outcome(name, "skipped", detail=str(exc))
    except Exception as exc:
        return Outcome(name, "error", detail=f"{type(exc).__name__}: {exc}")


def _worker(task: Task) -> Outcome:
    return process_file(*task)


def run_pool(pool: Pool, method: PoolMethod, tasks: Iterable[Task], chunksize: int) -> Iterator[Outcome]:
    match method:
        case "imap_unordered":
            yield from pool.imap_unordered(_worker, tasks, chunksize)
        case "imap":
            yield from pool.imap(_worker, tasks, chunksize)
        case "map":
            yield from pool.map(_worker, tasks, chunksize)
        case "starmap":
            yield from pool.starmap(process_file, tasks, chunksize)
        case "apply_async":
            pending = [pool.apply_async(process_file, task) for task in tasks]
            for result in pending:
                yield result.get()
        case "apply":
            for task in tasks:
                yield pool.apply(process_file, task)
        case _:
            msg = f"unknown pool method: {method}"
            raise ValueError(msg)


def report(outcome: Outcome) -> None:
    match outcome:
        case Outcome(status="stripped"):
            logger.info(
                "{} | -{} B ({} -> {} B)",
                outcome.path,
                outcome.saved,
                outcome.before,
                outcome.after,
            )
        case Outcome(status="skipped"):
            logger.debug("{} | skipped: {}", outcome.path, outcome.detail)
        case Outcome(status="error"):
            logger.error("{} | {}", outcome.path, outcome.detail)
        case _:
            logger.debug("{} | unchanged", outcome.path)


def configure_logging(verbose: bool, log_file: Path | None) -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level="DEBUG" if verbose else "INFO",
        format="{time:HH:mm:ss} | {level: <8} | {message}",
    )
    if log_file is not None:
        logger.add(log_file, level="DEBUG", rotation="10 MB", encoding="utf-8")


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="strip_comments")
    parser.add_argument("root", nargs="?", type=Path, default=Path())
    parser.add_argument("-b", "--backup", action="store_true")
    parser.add_argument("-n", "--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--pool-method", choices=POOL_METHODS, default="imap_unordered")
    parser.add_argument("--chunksize", type=int, default=8)
    parser.add_argument("--max-size", type=int, default=5 * 1024 * 1024)
    parser.add_argument("--skip-dir", action="append", default=[])
    parser.add_argument("--log-file", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose, args.log_file)
    root: Path = args.root.resolve()
    if not root.is_dir():
        logger.error("{} is not a directory", root)
        return 2
    skip_dirs = DEFAULT_SKIP_DIRS | frozenset(args.skip_dir)
    logger.info("languages: {}", ", ".join(sorted(AVAILABLE)) or "none")
    tasks = (Task(path, args.backup, args.max_size, args.dry_run) for path in iter_files(root, skip_dirs))
    summary = Summary()
    with mp.Pool(processes=max(1, args.jobs)) as pool:
        for outcome in run_pool(pool, args.pool_method, tasks, args.chunksize):
            report(outcome)
            summary.record(outcome)
    logger.info(
        "stripped={} unchanged={} skipped={} errors={}",
        summary.counts["stripped"],
        summary.counts["unchanged"],
        summary.counts["skipped"],
        summary.counts["error"],
    )
    logger.info(
        "{}freed {} of {} in stripped files",
        "[dry-run] would have " if args.dry_run else "",
        human(summary.freed),
        human(summary.stripped_before),
    )
    return int(summary.counts["error"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
