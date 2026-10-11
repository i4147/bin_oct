#!/data/data/com.termux/files/usr/bin/env python
"""Create a self-contained prompt that instructs an AI coding agent to reproduce a Python command-line utility with the following specification.

Build a Python 3 command-line script (targeting Termux on Android, so the shebang points to `/data/data/com.termux/files/usr/bin/env python`) that scans a directory tree for Python source files and finds duplicate top-level definitions across them. Use only the standard library, and include `from __future__ import annotations` at the top.

Core behavior:

1. **Definition extraction.** For each `.py` file, read it as UTF-8 and parse it with the `ast` module. If reading or parsing fails for any reason, silently treat the file as having no definitions and return an empty mapping. Only inspect top-level statements in the module body. Recognize three kinds of definitions:
   - Sync and async function definitions, keyed by their name and their full normalized source text (obtained via `ast.unparse`).
   - Class definitions, keyed the same way.
   - Simple assignments with exactly one target that is a plain name, treated as "constant" definitions, keyed the same way using the assigned name and unparsed statement text.

   Each extracted entry records the file path, the object's name, its type (function, class, or constant), and the AST node. The lookup key is a tuple of (type, name, unparsed source), so two definitions with the same name but different bodies are distinct entries.

2. **Duplicate detection.** Aggregate definitions across all scanned files and group identical ones (same type, name, and unparsed source) appearing in more than one location. Use `collections.defaultdict` for grouping. Report each group with the object name, type, and every file path where it appears.

3. **Parallel processing.** Use `concurrent.futures` (a thread or process pool) to parse files concurrently, since there may be many files. Collect results as they complete and merge them into the aggregate structure.

4. **Affected-file modification.** The script contains a helper function, `modify_affected_file`, which takes a file path string, an object name, and an object type (and related parameters) and rewrites the affected file to remove or modify the matched duplicate definition. Implement it so that it locates the target top-level node in the file's AST, edits the source accordingly, and writes the result back. Before writing, guard against destructive mistakes: only modify when the target is found exactly, and never write if parsing fails. Keep edits minimal and preserve the rest of the file's text.

5. **Command-line interface.** Use `argparse` to accept a root directory (defaulting to the current working directory), plus options to control behavior such as the number of worker threads, whether to apply modifications, and a verbosity or dry-run flag. By default the script should only report duplicates and not modify any files; modifications require an explicit flag. Print results in a readable, grouped format to standard output, and write diagnostic or error messages to standard error. Return a meaningful process exit code (0 on success, nonzero on argument or fatal errors).

6. **Filesystem handling.** Use `os` and `pathlib.Path` to walk the directory tree recursively, skipping hidden directories and common virtual-environment or cache directories such as `__pycache__`, `.git`, and `venv`-style folders. Only consider files ending in `.py`. Handle missing or unreadable paths gracefully, reporting them on standard error without crashing.

7. **Edge cases to handle:**
   - Empty directories or directories with no Python files: report that nothing was found and exit cleanly.
   - Files with syntax errors or non-UTF-8 content: skip them silently (they contribute no definitions).
   - Files that are symlinks or that disappear mid-scan: skip without crashing.
   - Duplicate names with differing bodies: do not report them as duplicates.
   - Constant assignments with multiple targets or non-name targets: ignore them.
   - Nested definitions (inside functions or classes): ignore them; only top-level nodes count.

8. **Execution details.** The script should be runnable directly (`python script.py [root] [options]`) and should guard its entry point with `if __name__ == "__main__":`. Wrap the main logic in a `main()` function that returns an integer exit code, and call `sys.exit` with it. Keep the code dependency-free beyond the standard library, so it runs on a stock Termux Python install.

Write clean, idiomatic code with type hints where helpful, descriptive function names, and concise docstrings. Include a brief usage explanation in the module docstring showing how to invoke the tool, its options, and what its output looks like.
---"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import os
import sys
from collections import defaultdict
from pathlib import Path


def parse_file_definitions(path: Path) -> dict:
    definitions = {}
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except Exception:
        return {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node_key = ("function", node.name, ast.unparse(node))
            definitions[node_key] = {
                "name": node.name,
                "type": "function",
                "node": node,
            }
        elif isinstance(node, ast.ClassDef):
            node_key = ("class", node.name, ast.unparse(node))
            definitions[node_key] = {"name": node.name, "type": "class", "node": node}
        elif isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                node_key = ("constant", name, ast.unparse(node))
                definitions[node_key] = {"name": name, "type": "constant", "node": node}
    return {node_key: (str(path), data) for node_key, data in definitions.items()}


def modify_affected_file(path_str: str, obj_name: str, obj_type: str, raw_obj_code: str) -> str:
    path = Path(path_str)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    new_body = []
    removed = False
    for node in tree.body:
        if obj_type in ("function", "class") and isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            if node.name == obj_name and ast.unparse(node) == raw_obj_code:
                removed = True
                continue
        elif obj_type == "constant" and isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id == obj_name and ast.unparse(node) == raw_obj_code:
                    removed = True
                    continue
        new_body.append(node)
    if not removed:
        return source
    import_node = ast.ImportFrom(module="dh", names=[ast.alias(name=obj_name, asname=None)], level=0)
    new_body.insert(0, import_node)
    tree.body = new_body
    modified_source = ast.unparse(tree)
    ast.parse(modified_source)
    return modified_source


def main():
    parser = argparse.ArgumentParser(
        description="Recursively find and consolidate duplicate functions, classes, and constants."
    )
    parser.add_argument(
        "-m",
        "--move",
        action="store_true",
        help="Consolidate duplicate code blocks into dh.py and update files with required imports.",
    )
    args = parser.parse_args()
    current_dir = Path()
    dh_path = current_dir / "dh.py"
    script_path = Path(__file__).resolve()
    py_files = [f for f in current_dir.rglob("*.py") if f.resolve() != script_path and f.resolve() != dh_path.resolve()]
    if not py_files:
        print("🔍 No Python files found to scan.")
        return
    print(f"🔍 Scanning {len(py_files)} files concurrently...")
    global_registry = defaultdict(list)
    cpu_cores = os.cpu_count() or 1
    with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_cores) as executor:
        futures = {executor.submit(parse_file_definitions, f): f for f in py_files}
        for future in concurrent.futures.as_completed(futures):
            file_defs = future.result()
            for node_key, (path_str, data) in file_defs.items():
                global_registry[node_key].append((path_str, data))
    duplicates = {k: v for k, v in global_registry.items() if len(v) > 1}
    if not duplicates:
        print("🎉 Success! No repeated functions, classes, or constants were detected.")
        return
    print(f"⚠️  Detected {len(duplicates)} repeated structural definitions:\n")
    dh_additions = []
    files_to_update = defaultdict(list)
    for (obj_type, obj_name, raw_code), occurrences in duplicates.items():
        files_listed = [occ[0] for occ in occurrences]
        print(f"[{obj_type.upper()}] '{obj_name}' is repeated in {len(files_listed)} files:")
        for f in files_listed:
            print(f"   -> {f}")
        print()
        if args.move:
            dh_additions.append(raw_code)
            for f_str, _ in occurrences:
                files_to_update[f_str].append((obj_name, obj_type, raw_code))
    if args.move:
        print("🛠️  Processing Consolidation (-m flag active)...")
        existing_dh_content = ""
        if dh_path.exists():
            existing_dh_content = dh_path.read_text(encoding="utf-8")
        new_dh_content = existing_dh_content + "\n\n" + "\n\n".join(dh_additions)
        try:
            ast.parse(new_dh_content)
            dh_path.write_text(new_dh_content, encoding="utf-8")
            print(f"✅ Extracted duplicate definitions safely written to: {dh_path}")
        except Exception as e:
            print(f"❌ Aborted: Merged definitions inside dh.py failed AST parsing logic: {e}")
            sys.exit(1)
        updated_count = 0
        for file_str, objects in files_to_update.items():
            try:
                current_path = Path(file_str)
                updated_source = current_path.read_text(encoding="utf-8")
                for obj_name, obj_type, raw_code in objects:
                    updated_source = modify_affected_file(file_str, obj_name, obj_type, raw_code)
                current_path.write_text(updated_source, encoding="utf-8")
                print(f"✅ In-place code updated & verified: {file_str}")
                updated_count += 1
            except Exception as e:
                print(f"❌ Failed to parse or modify file safely {file_str}: {e}. Skipping structural changes.")
        print(f"\n📊 Refactor complete. Adjusted and verified {updated_count} files.")


if __name__ == "__main__":
    raise SystemExit(main())
