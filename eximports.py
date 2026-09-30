#!/data/data/com.termux/files/home/.local/bin/python
"""
Generate a Python CLI script that scans a directory tree for Python files,
extracts every top-level import statement using tree-sitter, filters out
imports that belong to the standard library or to already-installed packages,
and writes the remaining third-party module names to "importz.txt".

The generated script should:
- Recursively discover "*.py" files under the current working directory.
- Parse each file with tree_sitter_python and collect the text of any
  top-level node whose type is "import_statement" or "import_from_statement".
- Normalize each import (lowercase, strip "as" aliases, drop dotted subpaths,
  skip relative and private modules) and exclude anything in
  sys.stdlib_module_names or in the set of installed packages (via
  importlib.metadata).
- Process files concurrently with multiprocessing.Pool.imap_unordered using
  a fixed pool of 8 workers (no CLI flag controls parallelism).
- Log progress with loguru and write the sorted result to "importz.txt".
- Include complete type hints and docstrings throughout.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from importlib.metadata import distributions
from multiprocessing import Pool
from pathlib import Path
from typing import Final

import tree_sitter_python as tsp
from loguru import logger
from tree_sitter import Language, Parser

POOL_SIZE: Final[int] = 8
OUTPUT_FILE: Final[str] = "importz.txt"
VALID_NODE_TYPES: Final[frozenset[str]] = frozenset(
    {"import_statement", "import_from_statement"}
)
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
        except Exception:  # noqa: BLE001
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
