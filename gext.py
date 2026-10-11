#!/data/data/com.termux/files/usr/bin/env python
"""Create a self-contained prompt that instructs an AI coding agent to build a Python command-line tool with the following specification:

**Purpose:** Build a Python 3 static-analysis extraction tool that scans Python source files and splits their contents into three categories: classes, top-level functions, and module-level constants. Each extracted item is written to its own output file, and the tool runs in parallel across files.

**Target environment:** The script is intended to run under Termux on Android, so it should use the shebang `#!/data/data/com.termux/files/usr/bin/env python`. It should work with only the Python standard library (no third-party packages), and it should begin with `from __future__ import annotations` so type hints like `list[str]` work on older interpreters.

**Inputs:**
- Command-line arguments: one or more file or directory paths. Any argument that is a file is checked to see whether it is a Python script; any argument that is a directory is walked recursively.
- Python script detection: a file counts as a Python script if its name ends in `.py`, or if its first line starts with `#!` and contains the word "python" (case-insensitive). Read files with UTF-8 encoding, ignoring decoding errors. Any read failure during detection means the file is not treated as a script; do not crash.
- Directory traversal must skip any subdirectory whose name is one of: `test`, `tests`, `examples`, `output`. Prune these in place during `os.walk` so they are not descended into.

**Outputs:**
- All results are written under a fixed `output/` directory relative to the current working directory, with three subdirectories: `output/classes`, `output/functions`, and `output/const`. Create them if they do not exist.
- Each extracted class, function, or constant is written to a separate file in the appropriate subdirectory, with the source text of that definition.
- Constant files are named after the constant identifier; the tool should detect constant names by the convention of being all-uppercase identifiers (with underscores and digits allowed), and should ignore names that do not match.
- Name collisions across different source files should be handled deterministically (for example by prefixing or suffixing with the source module name) so that no output is silently overwritten.
- The tool should print a brief progress or summary message to stdout indicating how many files were processed and how many items of each kind were extracted.

**Core logic:**
- Parse each Python file with the standard `ast` module. Before analysis, annotate every AST node with a reference to its parent node (via a recursive walk setting a private attribute), so that nested definitions can be distinguished from top-level ones.
- Only top-level classes and top-level functions (including async functions) are extracted; nested definitions inside functions or classes are not extracted as separate items.
- Only module-level assignments are considered for constants: examine plain assignments and annotated assignments whose target is a simple name matching the all-uppercase convention. Assignments inside functions or classes are excluded.
- Extract the exact source segment for each node. Use `ast.get_source_segment` where available, or otherwise compute the text from line and column offsets, preserving original formatting.
- Include decorators in the extracted source for classes and functions when they are part of the definition.

**Parallelism:**
- Process files concurrently using `multiprocessing` with a pool of 8 workers. Use the standard `if __name__ == "__main__":` guard and ensure the pool is properly closed and joined.
- Each worker should return its extraction results to the parent process, which performs all file writes, so that writing and counting are not interleaved unsafely. Collect and tally counts in the parent.

**Error handling and edge cases:**
- Files that fail to parse (syntax errors, decoding issues, unreadable files) must be skipped with a warning printed to stderr; they must not abort the whole run.
- Missing input paths should be reported and skipped.
- Empty input lists or inputs yielding no Python files should produce a clear message and exit cleanly.
- Handle files with no matching definitions gracefully (no empty output files).
- Handle symlinks and permission errors during directory walking without crashing.
- If no command-line arguments are given, print a usage message to stderr and exit with a nonzero status.

**Execution:**
- Invoke as a script: `python <script> <path> [<path> ...]`, or with the Termux shebang directly if executable.
- Exit with status 0 on success; use a nonzero status for usage errors.

Write the complete script in one file, with clear structure: helper functions for detection, collection, AST marking, constant-name checking, extraction, and writing, plus a `main` function invoked under the `__main__` guard. Keep comments concise and match the style of a short, practical utility script.
---"""

from __future__ import annotations

import ast
import multiprocessing as mp
import os
import sys

OUTPUT_DIR = "output"
CLASSES_DIR = os.path.join(OUTPUT_DIR, "classes")
FUNCTIONS_DIR = os.path.join(OUTPUT_DIR, "functions")
CONST_DIR = os.path.join(OUTPUT_DIR, "const")
EXCLUDE_DIRS = {"test", "tests", "examples", "output"}
WORKERS = 8


def is_python_script(path: str) -> bool:
    if path.endswith(".py"):
        return True
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            line = f.readline()
        return line.startswith("#!") and "python" in line.lower()
    except Exception:
        return False


def collect_files(inputs: list[str]) -> list[str]:
    files: list[str] = []
    for inp in inputs:
        if os.path.isfile(inp):
            if is_python_script(inp):
                files.append(inp)
        elif os.path.isdir(inp):
            for root, dirs, fnames in os.walk(inp):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for fname in fnames:
                    p = os.path.join(root, fname)
                    if is_python_script(p):
                        files.append(p)
    return files


def mark_parents(node: ast.AST, parent=None):
    for child in ast.iter_child_nodes(node):
        child._parent = node
        mark_parents(child, node)


def is_constant_name(name: str) -> bool:
    return name.isupper()


def extract_from_file(path: str):
    classes: dict[str, str] = {}
    funcs: dict[str, str] = {}
    consts: dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception:
        return path, classes, funcs, consts
    mark_parents(tree)
    for node in ast.walk(tree):
        parent = getattr(node, "_parent", None)
        if isinstance(node, ast.ClassDef):
            src = ast.get_source_segment(source, node)
            if src:
                classes[node.name] = src
        elif isinstance(node, ast.FunctionDef):
            if isinstance(parent, ast.ClassDef):
                continue
            src = ast.get_source_segment(source, node)
            if src:
                funcs[node.name] = src
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            if not isinstance(parent, ast.Module):
                continue
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                name = node.target.id
            else:
                continue
            if not is_constant_name(name):
                continue
            src = ast.get_source_segment(source, node)
            if src:
                consts[name] = src
    return path, classes, funcs, consts


def write_entity(directory: str, name: str, src: str) -> None:
    safe = name.replace(os.sep, "_").replace("/", "_")
    fpath = os.path.join(directory, safe + ".py")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(src.rstrip() + "\n")


def main():
    inputs = sys.argv[1:]
    if not inputs:
        inputs = ["."]
    files = collect_files(inputs)
    if not files:
        print("No Python files found.")
        return
    os.makedirs(CLASSES_DIR, exist_ok=True)
    os.makedirs(FUNCTIONS_DIR, exist_ok=True)
    os.makedirs(CONST_DIR, exist_ok=True)
    all_classes: dict[str, str] = {}
    all_funcs: dict[str, str] = {}
    all_consts: dict[str, str] = {}
    with mp.Pool(WORKERS) as pool:
        for _path, classes, funcs, consts in pool.imap_unordered(extract_from_file, files):
            all_classes.update(classes)
            all_funcs.update(funcs)
            all_consts.update(consts)
    for name, src in all_classes.items():
        write_entity(CLASSES_DIR, name, src)
    for name, src in all_funcs.items():
        write_entity(FUNCTIONS_DIR, name, src)
    for name, src in all_consts.items():
        write_entity(CONST_DIR, name, src)
    print(f"Scanned files : {len(files)}")
    print(f"Classes       : {len(all_classes)}")
    print(f"Functions     : {len(all_funcs)}")
    print(f"Constants     : {len(all_consts)}")
    print("Outputs saved to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
