#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script which scans a directory tree for files using the deprecated `pkg_resources` API, reports each usage with its line number and suggested modern replacement, and optionally applies the replacements. Describe the arguments, parallel processing, error handling, and output format in prose, with no code.

Create a Python command-line tool that scans a project for uses of the deprecated `pkg_resources` API from setuptools and reports where they occur, with suggested modern replacements. Write it as a single self-contained script with a Termux-style shebang line pointing to the Termux Python interpreter at /data/data/com.termux/files/usr/bin/env python, and begin the file with the `from __future__ import annotations` statement.

Purpose: The tool walks a directory tree, finds Python files that import `pkg_resources` (either via `import pkg_resources` or `from pkg_resources import ...` at the start of a line), and reports every call site of a known set of `pkg_resources` functions, along with the line number and the suggested replacement.

Standard library only: use argparse for the command line, re for pattern matching, multiprocessing's Pool for parallel file processing, and pathlib's Path for filesystem handling. Do not require any third-party packages.

Known replacements (define as a module-level collection mapping a regex pattern to its replacement text). Each pattern matches the literal call prefix with an escaped dot and an opening parenthesis:
- `pkg_resources.resource_filename(` → `importlib.resources.files(`
- `pkg_resources.resource_string(` → `importlib.resources.files(`
- `pkg_resources.require(` → `packaging.requirements.Requirement(`
- `pkg_resources.get_distribution(` → `importlib.metadata.version(`
- `pkg_resources.iter_entry_points(` → `importlib.metadata.entry_points(`
- `pkg_resources.parse_version(` → `packaging.version.Version(`

Detection function: takes a file path and returns a dictionary.
- Read the file as UTF-8. If reading raises an OSError or a UnicodeDecodeError, return a dictionary containing the file path, the error message as a string, and `found` set to False.
- Check for the import with a multiline regex anchored at line starts, matching either `import pkg_resources` or `from pkg_resources`. If no import is present, return the file path with `found` set to False.
- Otherwise, for each replacement pattern, iterate over all matches in the content. For each match compute the 1-based line number by counting newlines before the match start plus one. Record each usage as a dictionary with the matched pattern, the line number, and the suggested replacement. Collect all usages into a list.
- Return the file path, `found` set to True, and the list of usages.

Directory handling: the script accepts a root path (default the current directory) and an optional flag to limit or include paths. Recursively collect all `*.py` files under the root using pathlib's rglob. Skip any file whose path contains a directory named `.git`, `venv`, `.venv`, `__pycache__`, `build`, or `site-packages`.

Parallelism: process files with a multiprocessing Pool using a default worker count equal to the CPU count, overridable by a `--jobs` argument. Use `imap_unordered` or equivalent to collect results as they complete. When the file count is small (fewer than 2 files), process them serially to avoid pool overhead. Guard the main entry point with the standard `if __name__ == "__main__":` check so multiprocessing works on all platforms.

Command-line options:
- A positional `path` argument, default `.`.
- `--jobs` / `-j`, integer worker count.
- `--fix`, which, when set, rewrites each affected file applying the replacements in the mapping, preserving the rest of the file exactly. Print a message per modified file. Only write when at least one usage was found.
- `--quiet` / `-q`, suppress per-file progress output but still print the summary.
- `--exit-code`, which makes the script exit with status 1 if any usages were found (and 0 otherwise), useful for CI.

Output: for each file with findings, print the file path, then each usage as "line number: matched text → suggested replacement" with a clear indentation. Files that fail to read should print a warning to stderr with the file path and error, and must not stop the run. At the end print a summary: number of files scanned, number of files with `pkg_resources` imports, total usages found, number of files modified (if --fix), and number of read errors.

Error handling: catch and report per-file read errors without aborting. If the root path does not exist or is not a directory, print an error to stderr and exit with status 2. Handle KeyboardInterrupt by terminating the pool cleanly and exiting with status 130.

Edge cases to honor: files with a BOM or non-UTF-8 encoding are reported as errors, not crashes; a file that imports pkg_resources but never calls the mapped functions is counted as found with zero usages; an empty directory produces a zero summary; symlinked directories should not be followed to avoid cycles.

Usage example to document in the module docstring: running the script with no arguments scans the current directory, and running it with a path and `--fix --jobs 4` rewrites matches in that tree using four workers.

Keep the code idiomatic, with concise comments matching a professional standard, type hints where helpful, and a `main` function that returns an integer exit status.
---"""

from __future__ import annotations

import argparse
import re
from multiprocessing import Pool
from pathlib import Path

REPLACEMENTS = {
    (
        r"pkg_resources\.resource_filename\(",
        "importlib.resources.files(",
    ),
    (
        r"pkg_resources\.resource_string\(",
        "importlib.resources.files(",
    ),
    (
        r"pkg_resources\.require\(",
        "packaging.requirements.Requirement(",
    ),
    (
        r"pkg_resources\.get_distribution\(",
        "importlib.metadata.version(",
    ),
    (
        r"pkg_resources\.iter_entry_points\(",
        "importlib.metadata.entry_points(",
    ),
    (
        r"pkg_resources\.parse_version\(",
        "packaging.version.Version(",
    ),
}


def detect_pkg_resources(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        return {"file": path, "error": str(e), "found": False}
    has_import = re.search(r"^import\s+pkg_resources|^from\s+pkg_resources", content, re.MULTILINE)
    if not has_import:
        return {"file": path, "found": False}
    usages = []
    for pattern, _ in REPLACEMENTS:
        matches = re.finditer(pattern, content)
        for match in matches:
            line_num = content[: match.start()].count("\n") + 1
            usages.append({"pattern": pattern, "line": line_num})
    result = {
        "file": path,
        "found": bool(usages),
        "usages": usages,
        "imports_needed": set(),
    }
    if has_import:
        if re.search(r"pkg_resources\.resource_filename", content):
            result["imports_needed"].add("importlib.resources")
        if re.search(r"pkg_resources\.resource_string", content):
            result["imports_needed"].add("importlib.resources")
        if re.search(r"pkg_resources\.require", content):
            result["imports_needed"].add("packaging.requirements")
        if re.search(r"pkg_resources\.get_distribution", content):
            result["imports_needed"].add("importlib.metadata")
        if re.search(r"pkg_resources\.iter_entry_points", content):
            result["imports_needed"].add("importlib.metadata")
        if re.search(r"pkg_resources\.parse_version", content):
            result["imports_needed"].add("packaging.version")
    result["imports_needed"] = sorted(result["imports_needed"])
    return result


def autofix_pkg_resources(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        return {"file": path, "error": str(e), "fixed": False}
    original_content = content
    content = re.sub(
        r"^import\s+pkg_resources\n|^from\s+pkg_resources.*\n",
        "",
        content,
        flags=re.MULTILINE,
    )
    imports_needed = set()
    for old_pattern, new_pattern in REPLACEMENTS:
        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_pattern, content)
            if "importlib.resources" in new_pattern:
                imports_needed.add("importlib.resources")
            elif "packaging.requirements" in new_pattern:
                imports_needed.add("packaging.requirements")
            elif "importlib.metadata" in new_pattern:
                imports_needed.add("importlib.metadata")
            elif "packaging.version" in new_pattern:
                imports_needed.add("packaging.version")
    if imports_needed:
        import_lines = "\n".join(f"import {imp}" for imp in sorted(imports_needed))
        match = re.search(r"^(#!.*\n)?(\"\"\".*?\"\"\"\n)?", content, re.MULTILINE | re.DOTALL)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + import_lines + "\n" + content[insert_pos:]
        else:
            content = import_lines + "\n" + content
    if content != original_content:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "file": path,
                "fixed": True,
                "imports_added": sorted(imports_needed),
            }
        except OSError as e:
            return {"file": path, "error": f"Write failed: {e}", "fixed": False}
    return {"file": path, "fixed": False, "reason": "No changes needed"}


def collect_python_files(paths: list[str]) -> list[Path]:
    py_files = []
    for path_str in paths:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".py":
            py_files.append(path)
        elif path.is_dir():
            py_files.extend(path.rglob("*.py"))
    return sorted(set(py_files))


def main():
    parser = argparse.ArgumentParser(
        description="Detect and autofix deprecated pkg_resources usage.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python script.py
  python script.py -a
  python script.py src/ -a
  python script.py file.py
  python script.py file1.py file2.py
        """,
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Python files or directories to process (default: . recursively)",
    )
    parser.add_argument(
        "-a",
        "--autofix",
        action="store_true",
        help="Autofix pkg_resources usage (replace with importlib/packaging)",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=4,
        help="Number of parallel processes (default: 4)",
    )
    args = parser.parse_args()
    paths = args.paths or ["."]
    py_files = collect_python_files(paths)
    if not py_files:
        print("No .py files found.")
        return
    print(f"Found {len(py_files)} file(s) | Mode: {'AUTOFIX' if args.autofix else 'REPORT'}")
    print()
    try:
        if args.autofix:
            with Pool(processes=args.jobs) as pool:
                results = pool.map(autofix_pkg_resources, py_files)
            fixed_count = 0
            for result in results:
                if result.get("error"):
                    print(f"❌ {result['file']}: {result['error']}")
                elif result.get("fixed"):
                    fixed_count += 1
                    imports = ", ".join(result.get("imports_added", []))
                    print(f"✓ {result['file']} | Added: {imports}")
                else:
                    reason = result.get("reason", "No pkg_resources found")
                    if reason != "No pkg_resources found":
                        print(f"- {result['file']}: {reason}")
            print()
            print(f"Fixed {fixed_count}/{len(py_files)} file(s)")
        else:
            with Pool(processes=args.jobs) as pool:
                results = pool.map(detect_pkg_resources, py_files)
            found_count = 0
            for result in results:
                if result.get("error"):
                    print(f"❌ {result['file']}: {result['error']}")
                elif result.get("found"):
                    found_count += 1
                    usages = result.get("usages", [])
                    imports = ", ".join(result.get("imports_needed", []))
                    print(f"⚠ {result['file']}")
                    for usage in usages:
                        print(f"   Line {usage['line']}: {usage['pattern']}")
                    print(f"   Imports: {imports}\n")
            print()
            print(f"Found pkg_resources in {found_count}/{len(py_files)} file(s)")
            if found_count > 0:
                print("Run with -a to autofix.")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    raise SystemExit(main())
