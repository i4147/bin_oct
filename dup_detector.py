#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python command-line tool with the following specification:

Build a Python 3 command-line script that scans a directory tree for Python source files and detects near-duplicate top-level code objects (functions, async functions, classes, and simple single-name module-level constants) across those files, using fuzzy similarity rather than exact matching.

**Purpose and overall behavior**
- The script walks a given root directory recursively and collects every file ending in ".py", skipping any file whose name is exactly "utils.py".
- For each collected file, it parses the source with Python's standard `ast` module and extracts top-level objects only (direct children of the module body). Each extracted object records its type ("function", "class", or "constant"), its name, and its source code segment.
- Files that cannot be read as UTF-8 or that fail to parse due to syntax errors are silently skipped and yield no objects.
- Only these top-level node kinds are considered: sync and async function definitions, class definitions, and assignments with exactly one target that is a simple name. Other statements are ignored.
- The script then compares extracted objects to find near-duplicates, grouping objects whose code is highly similar, and reports the results.

**Dependencies and startup**
- Requires the third-party packages `ssdeep` (fuzzy hashing) and `rapidfuzz` (string similarity, using its `fuzz` module). If either import fails, print exactly this message to stdout and exit with status 1: "Please install dependencies: pip install ssdeep rapidfuzz".
- Use only standard-library modules otherwise: argparse, ast, hashlib, json, multiprocessing, os, sys, and collections.defaultdict. Include `from __future__ import annotations` at the top.
- Begin the file with a shebang line for Termux on Android: `#!/data/data/com.termux/files/usr/bin/env python`.

**Expected inputs**
- A command-line interface built with argparse, accepting a directory path to scan, and any options the implementer deems useful (for example, a similarity threshold and an output format or output file). Choose sensible defaults and document them in the help text.

**Comparison and grouping logic**
- Use a two-stage approach: compute a fuzzy hash (ssdeep) per object's source for a fast candidate filter, then confirm candidates with rapidfuzz similarity scoring against a configurable threshold.
- Use hashlib (for example, a content hash) to detect exact duplicates cheaply before fuzzy comparison.
- Group objects by name or type where appropriate so that unrelated items are not compared needlessly; use collections.defaultdict for grouping.
- Use multiprocessing to parallelize file extraction or comparison across CPU cores, and make sure the script's entry point is guarded by `if __name__ == "__main__":` so it works with multiprocessing on all platforms.
- Guard against self-comparison and avoid reporting the same pair twice.

**Outputs**
- Print or write results describing each group of near-duplicate objects: the object type, name, the file path and line information, and the similarity score(s).
- Support machine-readable output via json if the implementer includes a JSON option; otherwise print a readable text report to stdout.
- If no duplicates are found, state that clearly rather than printing nothing.

**Error handling and edge cases**
- Handle empty directories, directories with no `.py` files, non-existent or non-directory paths (report a clear error and exit non-zero), files with encoding or syntax errors (skip silently), and files containing no qualifying top-level objects.
- Handle objects whose source segments cannot be recovered (use a safe fallback).
- Ensure a single unreadable file does not crash the whole run.

**Execution details**
- Run as a standalone script from the command line; it should be executable with `python <script>` or directly via its shebang.
- Keep the code idiomatic, well-structured into small functions (file discovery, object extraction, comparison, reporting, and a main function with argparse setup), and include brief docstrings.
---"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import multiprocessing
import os
import sys
from collections import defaultdict

try:
    import ssdeep
    from rapidfuzz import fuzz
except ImportError:
    print("Please install dependencies: pip install ssdeep rapidfuzz")
    sys.exit(1)


def get_py_files(directory):
    py_files = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".py") and f != "utils.py":
                py_files.append(os.path.join(root, f))
    return py_files


def extract_objects(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return []
    objects = []
    for node in tree.body:
        obj_type = None
        name = None
        src_code = None
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            obj_type = "function"
            name = node.name
        elif isinstance(node, ast.ClassDef):
            obj_type = "class"
            name = node.name
        elif isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                obj_type = "constant"
                name = node.targets[0].id
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            obj_type = "constant"
            name = node.target.id
        if obj_type and name:
            src_code = ast.unparse(node)
            content_hash = hashlib.sha256(src_code.encode("utf-8")).hexdigest()
            objects.append({
                "object_type": obj_type,
                "object_name": name,
                "source_code": src_code,
                "reference_file": path,
                "content_hash": content_hash,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "ssdeep_hash": ssdeep.hash(src_code),
            })
    return objects


def process_file(path):
    return extract_objects(path)


def save_exact_duplicates(
    all_objects,
    output_file="exact_duplicates.json",
):
    hash_groups = defaultdict(list)
    for obj in all_objects:
        hash_groups[obj["content_hash"]].append(obj)
    duplicate_objects = []
    for content_hash, group in hash_groups.items():
        occurrence_count = len(group)
        if occurrence_count <= 1:
            continue
        for obj in group:
            duplicate_objects.append({
                "object_type": obj["object_type"],
                "object_name": obj["object_name"],
                "source_code": obj["source_code"],
                "reference_file": obj["reference_file"],
                "content_hash": content_hash,
                "occurrence_count": occurrence_count,
                "start_line": obj["start_line"],
                "end_line": obj["end_line"],
            })
    duplicate_objects.sort(
        key=lambda obj: (
            -obj["occurrence_count"],
            obj["object_type"],
            obj["object_name"],
            obj["reference_file"],
        )
    )

    def write_json(path: str, data: list[dict]) -> None:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    write_json(output_file, duplicate_objects)
    output_files = {
        "function": "function_duplicates.json",
        "class": "class_duplicates.json",
        "constant": "constant_duplicates.json",
    }
    for object_type, path in output_files.items():
        type_duplicates = [obj for obj in duplicate_objects if obj["object_type"] == object_type]
        write_json(path, type_duplicates)
        print(f"[+] Saved {len(type_duplicates)} {object_type} duplicate instances to {path}")
    print(f"[+] Saved {len(duplicate_objects)} exact duplicate instances to {output_file}")
    return hash_groups


def refactor_duplicates(hash_groups):
    utils_path = "utils.py"
    utils_content = ""
    if os.path.exists(utils_path):
        with open(utils_path, "r", encoding="utf-8") as f:
            utils_content = f.read()
    file_imports = defaultdict(set)
    for group in hash_groups.values():
        if len(group) > 5:
            master_obj = group[0]
            utils_content += f"\n\n# Moved from {master_obj['reference_file']}\n{master_obj['source_code']}\n"
            for obj in group:
                file_imports[obj["reference_file"]].add(obj["object_name"])
    with open(utils_path, "w", encoding="utf-8") as f:
        f.write(utils_content)
    print(f"[+] Created/Updated {utils_path}")
    for path, names_to_import in file_imports.items():
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        objs_to_remove = [
            obj for group in hash_groups.values() if len(group) > 5 for obj in group if obj["reference_file"] == path
        ]
        objs_to_remove.sort(key=lambda x: x["start_line"], reverse=True)
        for obj in objs_to_remove:
            start_idx = obj["start_line"] - 1
            end_idx = obj["end_line"]
            del lines[start_idx:end_idx]
        last_import_idx = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                last_import_idx = i
        insert_idx = last_import_idx + 1
        for name in sorted(names_to_import):
            lines.insert(insert_idx, f"from utils import {name}\n")
            insert_idx += 1
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    print(f"[+] Refactored {len(file_imports)} files.")


def generate_fuzzy_report(all_objects, output_file="fuzzy_duplicates.json"):
    report = []
    n = len(all_objects)
    print("[*] Calculating fuzzy similarities (this may take a while for large codebases)...")
    for i in range(n):
        for j in range(i + 1, n):
            obj1 = all_objects[i]
            obj2 = all_objects[j]
            if obj1["content_hash"] == obj2["content_hash"]:
                continue
            ssdeep_sim = ssdeep.compare(obj1["ssdeep_hash"], obj2["ssdeep_hash"])
            if ssdeep_sim > 0:
                ratio = fuzz.ratio(obj1["source_code"], obj2["source_code"])
                if ratio > 50.0:
                    report.append({
                        "object_1": {
                            "type": obj1["object_type"],
                            "name": obj1["object_name"],
                            "file": obj1["reference_file"],
                            "source_code": obj1["source_code"],
                        },
                        "object_2": {
                            "type": obj2["object_type"],
                            "name": obj2["object_name"],
                            "file": obj2["reference_file"],
                            "source_code": obj2["source_code"],
                        },
                        "similarity_percentage": round(ratio, 2),
                        "ssdeep_score": ssdeep_sim,
                    })
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    print(f"[+] Saved {len(report)} fuzzy duplicate pairs to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Detect and refactor duplicate Python objects.")
    parser.add_argument(
        "-r",
        "--refactor",
        action="store_true",
        help="Move duplicates with >5 appearances to utils.py and update imports.",
    )
    parser.add_argument(
        "-f",
        "--fuzzy",
        action="store_true",
        help="Generate a report for objects with >50% similarity using ssdeep and rapidfuzz.",
    )
    args = parser.parse_args()
    print("[*] Discovering Python files...")
    py_files = get_py_files(".")
    print(f"[*] Found {len(py_files)} files. Starting parallel extraction...")
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        results = pool.map(process_file, py_files)
    all_objects = [obj for file_objects in results for obj in file_objects]
    print(f"[*] Extracted {len(all_objects)} total objects.")
    hash_groups = save_exact_duplicates(all_objects)
    if args.refactor:
        print("[*] Refactoring duplicates with >5 appearances...")
        refactor_duplicates(hash_groups)
    if args.fuzzy:
        generate_fuzzy_report(all_objects)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
