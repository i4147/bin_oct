#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that removes comments from JavaScript and TypeScript source files (.js, .jsx, .ts, .tsx) while preserving the code exactly as written otherwise. The tool should accept one or more file or directory paths as input, recursively discover supported source files within directories, and process them in parallel using a bounded pool of worker processes to keep throughput high on large codebases.
For each file, the script should parse the source with a language-aware syntax parser that matches the file's dialect (plain JavaScript, TypeScript, or TSX/JSX), so that comment-like text inside string literals, template literals, and regular expressions is never mistakenly altered. Only genuine comments (single-line and multi-line) should be removed. Before writing any changes, the tool must verify that the file parsed cleanly; if the parser reports syntax errors, the file should be left untouched and a warning should be logged instead of risking corruption of the code.
Output behavior: modify files in place by default, with an option to write results to a separate output directory or to perform a dry run that only reports which files would change. The script should preserve original line endings and file encoding where possible, avoid rewriting files whose content would not change, and produce a concise summary at the end listing how many files were scanned, modified, skipped, and failed.
Provide a clear command-line interface with help text, sensible defaults, and proper exit codes (non-zero if any file failed to process). Use structured logging for progress and errors, handle missing paths and unreadable files gracefully, and make the core comment-stripping logic reusable as a function that takes source text and a file extension and returns the cleaned text.
---"""

from __future__ import annotations
from multiprocessing.pool import Pool
from pathlib import Path
import sys
from typing import Final
from loguru import logger
import tree_sitter
from tree_sitter import Language, Parser
import tree_sitter_javascript
import tree_sitter_typescript

MAX_WORKERS: Final[int] = 8
SUPPORTED_EXTENSIONS: Final[tuple[str, ...]] = (".js", ".ts", ".jsx", ".tsx")
_JS_LANGUAGE: Final[Language] = Language(tree_sitter_javascript.language())
_TS_LANGUAGE: Final[Language] = Language(tree_sitter_typescript.language_typescript())
_TSX_LANGUAGE: Final[Language] = Language(tree_sitter_typescript.language_tsx())
_LANGUAGE_BY_EXTENSION: Final[dict[str, Language]] = {
    ".js": _JS_LANGUAGE,
    ".jsx": _JS_LANGUAGE,
    ".ts": _TS_LANGUAGE,
    ".tsx": _TSX_LANGUAGE,
}


def _collect_comment_ranges(node: tree_sitter.Node, out: list[tuple[int, int]]) -> None:
    if node.type == "comment":
        out.append((node.start_byte, node.end_byte))
        return
    for child in node.children:
        _collect_comment_ranges(child, out)


def _has_error(node: tree_sitter.Node) -> bool:
    if node.is_error or node.is_missing:
        return True
    return any(_has_error(child) for child in node.children)


def _remove_ranges(source: bytes, ranges: list[tuple[int, int]]) -> bytes:
    ranges.sort()
    parts: list[bytes] = []
    prev: int = 0
    for start, end in ranges:
        parts.append(source[prev:start])
        newline_count: int = source[start:end].count(b"\n")
        parts.append(b"\n" * newline_count)
        prev = end
    parts.append(source[prev:])
    return b"".join(parts)


def process_file(file_path: Path) -> str | None:
    try:
        language: Language | None = _LANGUAGE_BY_EXTENSION.get(file_path.suffix)
        if language is None:
            return f"Unsupported extension: {file_path}"
        source: bytes = file_path.read_bytes()
        parser: Parser = Parser(language)
        original_tree: tree_sitter.Tree = parser.parse(source)
        if _has_error(original_tree.root_node):
            return f"Error: original file {file_path} contains syntax errors"
        ranges: list[tuple[int, int]] = []
        _collect_comment_ranges(original_tree.root_node, ranges)
        if not ranges:
            return None
        cleaned: bytes = _remove_ranges(source, ranges)
        cleaned_tree: tree_sitter.Tree = parser.parse(cleaned)
        if _has_error(cleaned_tree.root_node):
            return f"Error: cleaned result for {file_path} contains syntax errors"
        file_path.write_bytes(cleaned)
        return None
    except Exception as e:
        return f"Error processing {file_path}: {e}"


def _gather_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            if path.suffix in SUPPORTED_EXTENSIONS:
                files.append(path)
        elif path.is_dir():
            for ext in SUPPORTED_EXTENSIONS:
                files.extend(path.rglob(f"*{ext}"))
    return files


def main() -> None:
    if len(sys.argv) > 1:
        paths: list[Path] = [Path(arg) for arg in sys.argv[1:]]
    else:
        paths = [Path.cwd()]
    files_to_process: list[Path] = _gather_files(paths)
    if not files_to_process:
        logger.info("No files to process")
        return
    with Pool(processes=MAX_WORKERS) as pool:
        results: list[str | None] = list(pool.imap_unordered(process_file, files_to_process))
    errors: list[str] = [r for r in results if r is not None]
    if errors:
        for error in errors:
            logger.error(error)
        sys.exit(1)
    logger.info("Processed {} file(s)", len(files_to_process))


if __name__ == "__main__":
    raise SystemExit(main())
