#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script which recursively scans a directory tree for Python files, parses each file's top-level import statements using a tree-sitter-based parser, runs the processing in parallel with a fixed-size worker pool, normalizes and filters the collected import lines (separating standard library from third-party modules), and writes the results to an output text file while logging progress with a logging library. Include dependencies, key behaviors, error handling, edge cases, and how to run it, without any code.

Note: the provided source is truncated mid-function in `normalize_import`, so the prompt below describes the normalization behavior inferred from the visible portion and the constants it uses.

---

Create a self-contained Python 3 command-line script that scans Python source files, extracts their top-level import statements, normalizes them to module names, and writes a sorted, de-duplicated report of third-party and standard-library dependencies to a text file.

**Target runtime:** Termux on Android. The script begins with a shebang pointing to the Termux Python interpreter path (`/data/data/com.termux/files/usr/bin/env python`) and must use `from __future__ import annotations` for modern type-hint syntax. Use `typing.Final` for module-level constants and `TYPE_CHECKING`-guarded imports for type-only names such as `collections.abc.Iterable`.

**Dependencies:**
- `tree-sitter` (the `Parser` and `Language` classes) together with the `tree_sitter_python` grammar package, which exposes a `language()` function returning the grammar handle.
- `loguru` for logging (use its default `logger`).
- Standard library only otherwise: `sys`, `pathlib.Path`, `multiprocessing.Pool`, `importlib.metadata.distributions`.

**Constants (declare as `Final`):**
- `POOL_SIZE` = 8 worker processes.
- `OUTPUT_FILE` = `"importz.txt"`.
- `VALID_NODE_TYPES` = frozenset containing `"import_statement"` and `"import_from_statement"`.
- `STDLIB` = frozenset built from `sys.stdlib_module_names` (use an empty tuple fallback via `getattr` so it works on interpreters lacking that attribute).

**Functions to implement:**

1. `_make_parser()` — creates a tree-sitter `Parser`, sets its language to a `Language` built from the Python grammar's language handle, and returns it. Create a fresh parser per call so each worker process has its own.

2. `process_file(path)` — accepts a `Path` (convert it to a `Path` defensively), reads the file as raw bytes, parses it with a fresh parser, and iterates over the root node's direct children. For each child whose type is in `VALID_NODE_TYPES`, extract the exact source byte slice (start_byte to end_byte) and decode it as UTF-8 to a string. Return the list of these statement strings. Only top-level statements are considered; nested imports inside functions or classes are ignored.

3. `normalize_import(import_line)` — takes one raw import statement string, lowercases and strips it, then reduces it to a root module name:
   - For `import x` lines: remove the `import ` prefix, drop any ` as alias` suffix, and handle comma-separated multiple modules (each should be normalized separately by the caller).
   - For `from x import y` lines: take the module part between `from ` and ` import `, ignore relative imports that begin with dots (they are local, not dependencies), and keep only the top-level package (text before the first dot).
   - Return the root module name string, or `None` if the line is not recognized or is a relative import.

   The visible source is truncated, so design this function sensibly around these rules and make it robust to malformed input by returning `None` rather than raising.

4. A classifier step (implement as a helper) that separates each root module name into standard library (membership in `STDLIB`) versus third-party. Optionally, use `importlib.metadata.distributions()` to map installed distribution names to top-level module names so that third-party results can be annotated with their installed package/version, falling back to the bare module name when no distribution matches.

5. `main()` — the entry point:
   - Accept a target directory from the first command-line argument (`sys.argv[1]`), defaulting to the current working directory when absent. Validate that it exists and is a directory; if not, log an error via loguru and exit with a non-zero status.
   - Recursively collect all `*.py` files under that directory using `Path.rglob`. Optionally skip common non-source directories such as virtual environments, `.git`, `__pycache__`, and `site-packages`.
   - Process files in parallel using `multiprocessing.Pool(POOL_SIZE)`, mapping `process_file` across the file list (use `imap_unordered` or `map` with a chunksize). Wrap the pool usage in a context manager and guard the whole entry point with `if __name__ == "__main__":` so multiprocessing works correctly on spawn-based platforms.
   - Flatten the per-file results, normalize every statement (splitting comma-separated `import a, b` forms), discard `None` values, and collect unique root module names into a set.
   - Separate stdlib from third-party modules, sort each group alphabetically, and write the results to `OUTPUT_FILE` in the current working directory, with a clear heading for each section (standard library, third-party) and one entry per line. Use UTF-8 encoding.
   - Log progress with loguru: number of files found, number of unique modules by category, and the output path written.

**Error handling and edge cases:**
- Unreadable files or files with decode errors must not crash the whole run: catch exceptions per file inside `process_file` (or in a wrapper), log a warning with the path and error, and return an empty list for that file.
- Files with syntax errors still parse (tree-sitter is error-tolerant); skip any ERROR nodes gracefully.
- Empty files, files with no imports, and symlinks (resolve or skip consistently) must produce no crash.
- Non-UTF-8 source bytes inside import statements should be decoded with replacement rather than raising.
- Handle `KeyboardInterrupt` by terminating the pool cleanly and exiting.
- If no import statements are found at all, still write the output file with empty sections and log that nothing was found.

**Execution:** Run as `python <script>.py [target_directory]` from Termux. The script should make the output file path relative to the current working directory, not the scanned directory. Keep the code idiomatic, with type hints on all function signatures, concise docstrings, and no external dependencies beyond the listed ones.
---"""

from __future__ import annotations

import sys
from importlib.metadata import distributions
from multiprocessing import Pool
from pathlib import Path
from typing import TYPE_CHECKING, Final

import tree_sitter_python as tsp
from loguru import logger
from tree_sitter import Language, Parser

if TYPE_CHECKING:
    from collections.abc import Iterable
POOL_SIZE: Final[int] = 8
OUTPUT_FILE: Final[str] = "importz.txt"
VALID_NODE_TYPES: Final[frozenset[str]] = frozenset({"import_statement", "import_from_statement"})
STDLIB: Final[frozenset[str]] = frozenset(getattr(sys, "stdlib_module_names", ()))


def _make_parser() -> Parser:
    parser: Parser = Parser()
    parser.language = Language(tsp.language())
    return parser


def process_file(path: Path) -> list[str]:
    file_path: Path = Path(path)
    src: bytes = file_path.read_bytes()
    parser: Parser = _make_parser()
    tree = parser.parse(src)
    root = tree.root_node
    results: list[str] = []
    child = None
    for child in root.children:
        if child.type in VALID_NODE_TYPES:
            results.append(src[child.start_byte : child.end_byte].decode())
    return results


def normalize_import(import_line: str) -> str | None:
    line: str = import_line.lower().strip()
    if line.startswith("import "):
        module: str = line[7:]
        if " as " in module:
            module = module[: module.index(" as ")]
        if "." in module:
            module = module[: module.index(".")]
        return module if module and not module.startswith("_") else None
    if line.startswith("from "):
        module = line[5:]
        if module.startswith("."):
            return None
        if " import" in module:
            module = module[: module.index(" import")]
        if " as " in module:
            module = module[: module.index(" as ")]
        if "." in module:
            module = module[: module.index(".")]
        return module if module and not module.startswith("_") else None
    return None


def _get_installed_pkgs() -> set[str]:
    pkgs: set[str] = set()
    dist = None
    for dist in distributions():
        name: str | None = None
        try:
            name = dist.metadata["Name"]
        except Exception:
            name = None
        if name:
            pkgs.add(name.replace("-", "_").lower())
    return pkgs


def process_files_parallel(files: list[Path]) -> set[str]:
    all_imports: set[str] = set()
    if not files:
        return all_imports
    with Pool(processes=POOL_SIZE) as pool:
        result: list[str]
        for result in pool.imap_unordered(process_file, files):
            all_imports.update(result)
    return all_imports


def filter_imports(imports: set[str]) -> list[str]:
    installed_pkgs: set[str] = _get_installed_pkgs()
    excluded: set[str] = set(STDLIB) | installed_pkgs
    filtered: list[str] = []
    imp: str
    for imp in imports:
        normalized: str | None = normalize_import(imp)
        if normalized and normalized not in excluded:
            filtered.append(normalized + "\n")
    return sorted(set(filtered))


def get_pyfiles(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if p.is_file()]


def main(argv: Iterable[str] | None = None) -> int:
    _ = list(argv) if argv is not None else sys.argv[1:]
    outfile: Path = Path(OUTPUT_FILE)
    cwd: Path = Path.cwd()
    pyfiles: list[Path] = get_pyfiles(cwd)
    logger.info("{} python files found", len(pyfiles))
    all_imports: set[str] = process_files_parallel(pyfiles)
    filtered_imports: list[str] = filter_imports(all_imports)
    outfile.write_text("".join(filtered_imports), encoding="utf-8")
    imp: str
    for imp in filtered_imports:
        logger.info("{}", imp.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
