#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans one or more user-supplied files or directories for Python source files and extracts their structural definitions into organized output. The tool should accept a list of file paths and/or folder paths as input, recursively walk directories while skipping common non-source folders such as test, example, and output directories, and identify Python scripts either by a ".py" extension or by a Python shebang line in the first line of an extensionless file.
For every discovered script, the tool should parse the source code to locate top-level class definitions, top-level function definitions, and module-level constant assignments. Each category should be written to its own dedicated output subdirectory (classes, functions, and constants), with one output file per extracted item named clearly after the item and its source script so results remain traceable. Each output file should contain the complete source text of the extracted definition or assignment, preceded by a short header noting the originating file and line range.
The processing of many files should run in parallel using a fixed pool of worker processes to keep throughput high on large codebases. The tool must handle unreadable files, encoding problems, and syntax errors gracefully by logging a warning and continuing with the remaining files rather than aborting the whole run. At completion, it should print a concise summary reporting the number of files scanned, the number of classes, functions, and constants extracted, and any files that were skipped or failed. The script should be runnable from the command line, accept its inputs as arguments, and create the output directories automatically if they do not exist.
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
