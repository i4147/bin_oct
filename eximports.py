#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a given directory (or a set of Python files) for Python source files, parses each file's syntax tree, and collects every top-level import statement (both plain imports and "from ... import" statements). The script should process files in parallel using a small worker pool to keep things fast on large codebases.
For each file, the script should extract the raw text of each top-level import statement and then normalize the collected module names into a deduplicated, sorted list. It should distinguish between standard library modules and third-party packages, using the interpreter's knowledge of standard library module names where available, and should attempt to identify which third-party packages are installed in the current environment so that they can be reported accordingly.
The main output should be a plain-text report written to a file (named "importz.txt" by default), listing the discovered imports grouped into sections such as standard library, installed third-party packages, and unknown or uninstalled packages. The script should also log its progress and any errors (such as unreadable or unparseable files) using a logging library, without crashing on individual file failures.
The script should accept a command-line path argument for the target directory or file, should skip non-Python files, and should produce a clear summary at the end indicating how many files were scanned and how many unique imports were found. Use only well-structured, idiomatic Python with a `main` entry point and make sure the program runs correctly when executed directly from the command line.
---"""

from __future__ import annotations
from importlib.metadata import distributions
from multiprocessing import Pool
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Final
from loguru import logger
from tree_sitter import Language, Parser
import tree_sitter_python as tsp

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
