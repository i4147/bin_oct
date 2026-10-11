#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script which recursively scans a directory for TOML files, strips comments from them using a tree-sitter parser, and reports results in parallel. Here is the prompt:

---

Create a Python 3 command-line script (intended to run under Termux on Android, so use a `#!/data/data/com.termux/files/usr/bin/env python` shebang) that processes TOML files in parallel and reports the size difference after stripping comments.

**Purpose:** Given one or more file or directory paths, locate every TOML file, remove all comments from each file's content using a concrete syntax tree parser, and report per-file and total size statistics, showing how many bytes comment removal saves.

**Module header:** Begin with `from __future__ import annotations`. Use only the standard library plus two third-party components: `tree_sitter_toml` (provides the TOML grammar via a `language()` function) and `tree_sitter` (provides `Language` and `Parser`). Also import a helper `fsz` from a local module named `dh` that formats a byte count into a human-readable string (e.g., KB/MB). Import `sys`, `time`, `Path` from `pathlib`, `Pool` from `multiprocessing`, and `Any`, `Final`, `Optional` from `typing`.

**Constants and lazy parser:**
- A module-level `_WORKERS` constant set to 8 (number of worker processes).
- A module-level `_NAME_WIDTH` constant set to 50 (column width used when printing file names).
- A module-level `_parser` variable initialized to `None`. Implement `_get_parser()` that lazily creates a single `Parser` configured with `Language(tree_sitter_toml.language())` the first time it is called and caches it in the global. Each worker process must create its own parser this way (parsers are not shared across processes).

**`remove_toml_comments(content: str) -> str`:**
1. Encode the content to UTF-8 bytes and parse it with the parser.
2. Walk the syntax tree iteratively (using an explicit stack, not recursion) and collect the byte ranges `(start_byte, end_byte)` of every node whose type is `"comment"`.
3. If no comment ranges are found, return the original string unchanged.
4. Otherwise copy the source bytes into a `bytearray`. Process ranges in reverse-sorted order so earlier offsets remain valid. For each range, also consume any immediately preceding spaces or tabs (0x20, 0x09) so that trailing whitespace before a comment is removed along with it. Delete the slice.
5. Decode the bytearray back to a UTF-8 string and return it.

**`process_file(path: Path) -> tuple[str, int, int]` (or similar tuple of name, original size, new size):**
- Read the file as text (UTF-8), run `remove_toml_comments`, and return the file's display name, its original byte size, and the byte size of the stripped result. Handle the worker's per-file errors gracefully so one bad file does not abort the whole run: catch exceptions per file, report the failing path with the error message in the output, and continue with the remaining files.

**Main logic (`main()` with `if __name__ == "__main__":` guard):**
- Accept one or more paths from `sys.argv[1:]`. If none are given, print a usage message to stderr and exit with a nonzero status.
- For each argument, if it is a file ending in `.toml`, include it; if it is a directory, recursively collect all `*.toml` files beneath it. Skip or warn about nonexistent paths. Deduplicate and sort the collected list.
- If no TOML files are found, print a message saying so and exit cleanly.
- Use `multiprocessing.Pool(_WORKERS)` with `imap_unordered` (or equivalent) to process files concurrently, and display progress as results arrive.
- Print each file's name left-aligned/padded to `_NAME_WIDTH` characters, followed by the original size, the new size, and the bytes saved (formatted with `fsz`). Truncate or handle names longer than the width gracefully.
- Track and print totals at the end: number of files processed, number of errors, total original size, total new size, total saved, and the elapsed time measured with `time.perf_counter()` (or `time.time()`) formatted to a sensible precision.
- Ensure the pool is properly closed and joined (use a `with` block or explicit `close()`/`join()`), and that the process works correctly under the `spawn`/`fork` start methods, meaning all worker functions must be defined at module top level.

**Edge cases to handle:**
- Empty files (should produce zero savings and not crash).
- Files with no comments (returned unchanged).
- Comments at the very start of a line, after values, and multiple consecutive comments.
- Files that are not valid UTF-8 (report as an error for that file, don't crash).
- Nonexistent paths and unreadable files.
- Symlinks and hidden directories may be followed or skipped; document the choice in a comment.
- Keep the code free of unnecessary dependencies and avoid recursion depth issues.

**Style:** Use type hints throughout (including `# type: ignore[import-untyped]` on the tree-sitter imports), concise docstrings, and a clean, flat module structure. Output only the complete script.
---"""

from __future__ import annotations

import sys
import time
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Final, Optional

from dh import fsz

_parser: Optional[Any] = None
_WORKERS: Final[int] = 8
_NAME_WIDTH: Final[int] = 50


def _get_parser() -> Any:
    global _parser
    if _parser is None:
        import tree_sitter_toml as tstoml  # type: ignore[import-untyped]
        from tree_sitter import Language  # type: ignore[import-untyped]
        from tree_sitter import Parser

        _parser = Parser(Language(tstoml.language()))
    return _parser


def remove_toml_comments(content: str) -> str:
    parser: Any = _get_parser()
    source: bytes = content.encode("utf-8")
    tree: Any = parser.parse(source)
    ranges: list[tuple[int, int]] = []
    stack: list[Any] = [tree.root_node]
    while stack:
        node: Any = stack.pop()
        if node.type == "comment":
            ranges.append((node.start_byte, node.end_byte))
        else:
            stack.extend(node.children)
    if not ranges:
        return content
    result: bytearray = bytearray(source)
    for start, end in sorted(ranges, reverse=True):
        s: int = start
        while s > 0 and result[s - 1] in (0x20, 0x09):
            s -= 1
        del result[s:end]
    return result.decode("utf-8")


def process_file(path: Path) -> tuple[str, float, int, int]:
    start_time: float = time.perf_counter()
    try:
        with open(path, encoding="utf-8") as f:
            content: str = f.read()
        before_size: int = len(content.encode("utf-8"))
        cleaned_content: str = remove_toml_comments(content)
        with open(path, "w", encoding="utf-8") as f:
            f.write(cleaned_content)
        after_size: int = len(cleaned_content.encode("utf-8"))
        time_taken: float = (time.perf_counter() - start_time) * 1000.0
        return (str(path), time_taken, before_size, after_size)
    except Exception as e:
        print(f"Error processing {path}: {e}", file=sys.stderr)
        time_taken = (time.perf_counter() - start_time) * 1000.0
        return (str(path), time_taken, 0, 0)


def collect_toml_files(paths: list[Path]) -> list[Path]:
    toml_files: list[Path] = []
    for path in paths:
        if path.is_file():
            if path.suffix.lower() == ".toml":
                toml_files.append(path)
        elif path.is_dir():
            toml_files.extend(path.rglob("*.toml"))
    return toml_files


def main() -> int:
    paths: list[Path]
    if len(sys.argv) > 1:
        paths = [Path(arg) for arg in sys.argv[1:]]
    else:
        paths = [Path.cwd()]
    toml_files: list[Path] = collect_toml_files(paths)
    if not toml_files:
        print("No .toml files found to process.")
        return 0
    print(f"Found {len(toml_files)} TOML file(s) to process...")
    print("-" * 40)
    print(f"{'Filename':<50} {'Time (ms)':<10} {'Before':<12} {'After':<12} {'Ratio':<8}")
    print("-" * 40)
    results: list[tuple[str, float, int, int]] = []
    with Pool(processes=_WORKERS) as pool:
        for result in pool.imap_unordered(process_file, toml_files):
            results.append(result)
            filename, time_taken, before_size, after_size = result
            ratio: float = after_size / before_size * 100.0 if before_size > 0 else 0.0
            display_name: str = filename if len(filename) <= _NAME_WIDTH - 2 else "..." + filename[-(_NAME_WIDTH - 3) :]
            print(
                f"{display_name:<{_NAME_WIDTH}} {time_taken:>8.2f}  "
                f"{fsz(before_size):<12} {fsz(after_size):<12} {ratio:>6.1f}%"
            )
    print("-" * 40)
    total_before: int = sum(r[2] for r in results)
    total_after: int = sum(r[3] for r in results)
    total_ratio: float = total_after / total_before * 100.0 if total_before > 0 else 0.0
    total_time: float = sum(r[1] for r in results)
    print(f"Total: {len(results)} file(s) processed in {total_time:.2f} ms")
    print(f"Size reduction: {fsz(total_before)} -> {fsz(total_after)} ({total_ratio:.1f}% of original)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
