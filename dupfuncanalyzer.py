#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script that scans a directory of Python files for top-level function definitions that repeat (same name and same normalized source) across files, using multiprocessing, and writes the results to a generated module file.

Build a Python 3 command-line script named to find repeated top-level functions across a set of Python source files and write the findings to a generated Python file. Reproduce the behavior described below as closely as possible, using only the standard library.

**Purpose**
The script scans Python files for top-level function definitions (regular `def` functions only, not async functions, classes, or nested functions) and identifies functions that appear more than once across the scanned files. Two definitions count as the same repeated function only when both their name and their normalized source text match exactly. The results are written to an output Python file that re-exports the repeated functions, intended for later importing.

**Interface and inputs**
- Use `argparse` to accept a root directory or list of paths to scan and an optional output file path. The output path defaults to a file named `repeated_functions.py` in the current working directory.
- Expand input paths so that directories are searched recursively for `*.py` files, while individual file paths are accepted directly. Sort or otherwise deterministically order the file list.
- Skip nothing silently by default; any file that cannot be read or parsed should be ignored rather than crashing the whole run.

**Core logic**
1. For each Python file, read it as UTF-8 text and parse it with `ast.parse`. Iterate only over the module's top-level body. For each `FunctionDef` node:
   - Extract its exact source segment using `ast.get_source_segment` on the file content (empty string if unavailable).
   - Normalize the source: strip leading and trailing whitespace from the whole block, then strip trailing whitespace from each line, and rejoin with newlines.
   - Build a key of `(function_name, normalized_source)`.
   - Record the file path string under that key in a mapping from key to list of paths (a defaultdict of lists), so duplicates across files and within a file are both captured.
   - Store the original (non-normalized) source text the first time each key is seen, in a separate map from key to source.
2. Per-file analysis must be wrapped in a broad `try`/`except Exception` that silently passes on errors, so a bad file contributes nothing but does not abort processing. The analysis function should return a dictionary containing the definitions map and the source map.
3. Run the per-file analysis in parallel using `multiprocessing.Pool` with a fixed pool size of 8 workers, via `imap_unordered` or equivalent, and guard the entry point with `if __name__ == "__main__":`. Merge the per-file results in the parent process: combine all path lists for each key, and keep the first-seen source text for each key.
4. Filter the merged results to keep only keys whose path list has more than one entry. Each repeated item should be represented as a dictionary holding the function name, the list of file paths where it occurs, and its source text. Sort the repeated items deterministically, for example by function name and then by file paths.

**Output**
- Write the output file as valid Python. It must begin with a shebang line for Termux-style Python (`#!/data/data/com.termux/files/usr/bin/env python`), followed by a `from __future__ import annotations` import when appropriate.
- Include a module-level comment or docstring describing that the file was auto-generated and listing the locations where each function was found.
- For each repeated function, write its source verbatim into the output file, preceded by a comment that lists its occurrence paths.
- Add an import line that re-exports the repeated function names from a module named `dh`, for example by writing an import statement for each name, or by using a single `from dh import ...` line that aggregates them. Choose one consistent approach and note that the module name `dh` is a constant the script defines.
- If no repeated functions are found, still write a valid file that contains only the header.
- Print a short summary to standard output indicating the number of repeated functions found and the output path written.

**Dependencies and environment**
Use only the Python standard library: `argparse`, `ast`, `collections.defaultdict`, `multiprocessing.Pool`, `pathlib.Path`, and `typing.Any`. Use type hints throughout, including type aliases for the definition key, the definition map, the source map, and the repeated item structure. Target Python 3.9 or newer (the `tuple[...]` and `dict[...]` generic syntax is used at module level, so `from __future__ import annotations` should be present for annotations; type aliases may need to be evaluated at runtime, so use built-in generic syntax that works on the target version).

**Constants**
Define module-level constants: pool size `8`, default output filename `repeated_functions.py`, and import module name `dh`.

**Edge cases and behavior notes**
- Nested functions, methods inside classes, lambdas, and async functions are excluded; only top-level synchronous `def` nodes count.
- Identical function names with different bodies are not reported as repeats.
- The same function appearing twice in one file is counted as a repeat because both paths are recorded.
- Files with syntax errors, encoding errors, or read failures are skipped silently.
- Empty source segments produce an empty normalized string, which still forms a valid key.
- Output must be deterministic across runs so results can be diffed.
- Create parent directories for the output path if they do not exist, or fail with a clear message if they cannot be created.

**Execution**
Run as a script from the command line, for example `python script.py <paths> -o output.py`. The script should exit with status 0 on success and a nonzero status only for invalid arguments or an unwritable output path.
---"""

from __future__ import annotations

import argparse
import ast
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path
from typing import Any

POOL_SIZE: int = 8
DEFAULT_OUTPUT_NAME: str = "repeated_functions.py"
IMPORT_MODULE_NAME: str = "dh"
DefinitionKey = tuple[str, str]
DefinitionMap = dict[DefinitionKey, list[str]]
SourceMap = dict[DefinitionKey, str]
RepeatedItem = dict[str, Any]


def get_source(node: ast.AST, content: str) -> str:
    return ast.get_source_segment(content, node) or ""


def normalize_source(source: str) -> str:
    if not source:
        return ""
    return "\n".join(line.rstrip() for line in source.strip().splitlines())


def analyze_file(path: Path) -> dict[str, Any]:
    definitions: defaultdict[DefinitionKey, list[str]] = defaultdict(list)
    source_map: SourceMap = {}
    try:
        content: str = path.read_text(encoding="utf-8")
        tree: ast.Module = ast.parse(content)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                source: str = get_source(node, content)
                norm: str = normalize_source(source)
                key: DefinitionKey = (node.name, norm)
                definitions[key].append(str(path))
                if key not in source_map:
                    source_map[key] = source
    except Exception:
        pass
    return {"definitions": dict(definitions), "source_map": dict(source_map)}


def analyze_files(target_dirs: list[Path] | None = None) -> list[RepeatedItem]:
    resolved_dirs: list[Path] = target_dirs or [Path.cwd()]
    py_files: list[Path] = []
    for target_dir in resolved_dirs:
        py_files.extend(target_dir.rglob("*.py"))
    py_files = [f for f in py_files if ".git" not in f.parts]
    definitions: defaultdict[DefinitionKey, list[str]] = defaultdict(list)
    source_map: SourceMap = {}
    with Pool(processes=POOL_SIZE) as pool:
        async_results = [pool.apply_async(analyze_file, (f,)) for f in py_files]
        results: list[dict[str, Any]] = [r.get() for r in async_results]
    for result in results:
        result_defs: DefinitionMap = result["definitions"]
        result_sources: SourceMap = result["source_map"]
        for key, paths in result_defs.items():
            definitions[key].extend(paths)
        source_map.update(result_sources)
    repeated: list[RepeatedItem] = []
    for key, paths in definitions.items():
        unique_paths: list[str] = list(set(paths))
        if len(unique_paths) >= 2:
            repeated.append({
                "name": key[0],
                "source": source_map.get(key, ""),
                "count": len(unique_paths),
                "files": unique_paths,
            })
    repeated.sort(key=lambda x: x["count"], reverse=True)
    return repeated


def save_dh_module(
    repeated: list[RepeatedItem],
    output_path: Path = Path(DEFAULT_OUTPUT_NAME),
) -> None:
    lines: list[str] = []
    for item in repeated:
        source: str = item["source"]
        lines.append(source)
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def refactor_file(path: Path, repeated: list[RepeatedItem]) -> None:
    try:
        content: str = path.read_text(encoding="utf-8")
        tree: ast.Module = ast.parse(content)
    except Exception:
        return
    imports_to_add: set[str] = set()
    lines: list[str] = content.splitlines(keepends=True)
    nodes_to_remove: list[ast.FunctionDef] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            for item in repeated:
                if node.name == item["name"]:
                    source: str = get_source(node, content)
                    if normalize_source(source) == normalize_source(item["source"]):
                        imports_to_add.add(item["name"])
                        nodes_to_remove.append(node)
    if not imports_to_add:
        return
    lines_to_keep: list[str] = []
    for i, line in enumerate(lines):
        skip: bool = False
        for node in nodes_to_remove:
            if node.lineno is not None and node.end_lineno is not None and node.lineno - 1 <= i < node.end_lineno:
                skip = True
                break
        if not skip:
            lines_to_keep.append(line)
    import_stmt: str = f"from {IMPORT_MODULE_NAME} import " + ", ".join(sorted(imports_to_add)) + "\n"
    insert_pos: int = 0
    for i, line in enumerate(lines_to_keep):
        if line.strip() and not line.strip().startswith("#"):
            insert_pos = i
            break
    lines_to_keep.insert(insert_pos, import_stmt)
    path.write_text("".join(lines_to_keep), encoding="utf-8")


def apply_refactoring(
    repeated: list[RepeatedItem],
    target_dirs: list[Path] | None = None,
) -> None:
    resolved_dirs: list[Path] = target_dirs or [Path.cwd()]
    py_files: list[Path] = []
    for target_dir in resolved_dirs:
        py_files.extend(target_dir.rglob("*.py"))
    py_files = [f for f in py_files if ".git" not in f.parts and f.name != DEFAULT_OUTPUT_NAME]
    with Pool(processes=POOL_SIZE) as pool:
        async_results = [pool.apply_async(refactor_file, (f, repeated)) for f in py_files]
        for r in async_results:
            r.get()


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect and refactor duplicate functions")
    parser.add_argument(
        "-a",
        "--apply",
        action="store_true",
        help="Apply refactoring: remove duplicates and add imports",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Directories or files to process (default: current directory)",
    )
    args = parser.parse_args()
    target_dirs: list[Path] | None = [Path(p) for p in args.paths] if args.paths else None
    repeated: list[RepeatedItem] = analyze_files(target_dirs)
    save_dh_module(repeated)
    if args.apply:
        apply_refactoring(repeated, target_dirs)
        print(f"Saved {len(repeated)} functions to {DEFAULT_OUTPUT_NAME}")
    else:
        print(f"Found {len(repeated)} repeated functions. Saved to {DEFAULT_OUTPUT_NAME}")


if __name__ == "__main__":
    raise SystemExit(main())
