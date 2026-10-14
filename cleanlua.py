#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that removes ordinary comments from Lua source files while preserving documentation comments, designed to run efficiently over large codebases.
The tool should accept one or more file or directory paths as input and recursively locate Lua source files (with the `.lua` extension). For each Lua file, it should parse the source using a robust syntax-aware approach so that only true comments are identified, never text inside string literals or other code. Ordinary comments, both single-line and multi-line block comments, should be removed from the code, while documentation-style comments that begin with triple dashes (`---`) must be kept intact, since they carry API documentation meaning.
The script should preserve everything else byte-for-byte, including code formatting, indentation, and line structure as much as possible, so that the resulting code remains functionally identical. It should support a dry-run or preview mode that reports what would change without modifying files, a option to write changes in place or to a specified output location, and a summary report showing how many files were processed, modified, and skipped, along with any parse errors encountered.
Use multiprocessing or another parallelization strategy so that large numbers of files can be processed quickly, and make sure a failure in one file does not stop the processing of others. Provide clear logging of progress and errors, handle encoding issues gracefully, and offer command-line options with helpful help text. The script should exit with a meaningful status code indicating success, partial failure, or total failure.
---"""

from __future__ import annotations
import argparse
import multiprocessing as mp
from pathlib import Path
from typing import TYPE_CHECKING
from loguru import logger
from tree_sitter import Language, Node, Parser
import tree_sitter_lua

if TYPE_CHECKING:
    from collections.abc import Iterator
LUA_LANGUAGE: Language = Language(tree_sitter_lua.language())
LUA_EXTS: set[str] = {".lua"}
_PARSER: Parser | None = None


def get_parser() -> Parser:
    global _PARSER
    if _PARSER is None:
        _PARSER = Parser(LUA_LANGUAGE)
    return _PARSER


def collect_comment_ranges(root: Node, content: bytes) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    stack: list[Node] = [root]
    while stack:
        node: Node = stack.pop()
        if node.type == "comment":
            text: bytes = content[node.start_byte : node.end_byte]
            if not text.startswith(b"---"):
                ranges.append((node.start_byte, node.end_byte))
            continue
        for child in reversed(node.children):
            stack.append(child)
    return ranges


def strip_comments(content: bytes) -> tuple[bytes, int]:
    parser: Parser = get_parser()
    tree = parser.parse(content)
    ranges: list[tuple[int, int]] = collect_comment_ranges(tree.root_node, content)
    if not ranges:
        return content, 0
    ranges.sort(key=lambda r: r[0])
    out: bytearray = bytearray()
    last: int = 0
    for start, end in ranges:
        out.extend(content[last:start])
        last = end
    out.extend(content[last:])
    return bytes(out), len(ranges)


def process_file_worker(args: tuple[Path, Path]) -> tuple[str, int, str]:
    path, base = args
    try:
        content: bytes = path.read_bytes()
        new_content, count = strip_comments(content)
        if new_content != content:
            path.write_bytes(new_content)
        try:
            rel: str = str(path.relative_to(base))
        except ValueError:
            rel = str(path)
        return rel, count, ""
    except Exception as exc:
        return str(path), 0, str(exc)


def iter_lua_files(paths: list[Path]) -> Iterator[Path]:
    seen: set[Path] = set()
    for p in paths:
        if p.is_file() and p.suffix.lower() in LUA_EXTS:
            rp: Path = p.resolve()
            if rp not in seen:
                seen.add(rp)
                yield p
        elif p.is_dir():
            for f in sorted(p.rglob("*.lua")):
                rp = f.resolve()
                if rp not in seen:
                    seen.add(rp)
                    yield f


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Remove comments from Lua files in place, preserving '---' annotations (tree-sitter powered)."
    )
    ap.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or directories. Defaults to current directory recursively.",
    )
    args: argparse.Namespace = ap.parse_args()
    inputs: list[Path] = list(args.paths) if args.paths else [Path()]
    files: list[Path] = list(iter_lua_files(inputs))
    if not files:
        logger.error("No Lua files to process.")
        return 1
    base: Path = Path.cwd()
    total_comments: int = 0
    files_changed: int = 0
    errors: int = 0
    tasks: list[tuple[Path, Path]] = [(p, base) for p in files]
    with mp.Pool(processes=8) as pool:
        for rel, count, err in pool.imap(process_file_worker, tasks):
            if err:
                errors += 1
                logger.error(f"{rel}: ERROR: {err}")
                continue
            total_comments += count
            if count > 0:
                files_changed += 1
                print(f"{rel}: {count} comment(s) removed")
    print(
        f"Summary: {files_changed}/{len(files)} file(s) changed, "
        f"{total_comments} comment(s) removed, {errors} error(s)."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
