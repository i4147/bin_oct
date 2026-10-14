#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory tree (or a set of individual files) for Python source files and reports lines that contain trailing whitespace or other style issues within comments and string literals, while ignoring docstrings. The tool should accept a root path and optional flags from the command line, walk all matching `.py` files, and analyze each one independently so that large projects are processed quickly, for example by distributing work across multiple worker processes. For every problem found, it should record the file path, line number, and a short description of the issue, then print a clear, human-readable summary grouped by file, followed by a total count. The script should exit with a non-zero status code when any issues are found and zero otherwise, so it can be used in continuous integration pipelines. Handle unreadable files, files with syntax errors, and encoding problems gracefully by reporting them as warnings without crashing the whole run. Include helpful command-line help text describing each option, and make the behavior of skipping docstrings and the choice of which checks to enable configurable through clearly named options.
---"""

from __future__ import annotations
import argparse
import ast
import multiprocessing as mp
from pathlib import Path


def find_docstring_lines(source_bytes: bytes) -> set[int]:
    docstring_lines = set()
    try:
        tree = ast.parse(source_bytes)
    except Exception:
        return docstring_lines
    for node in ast.walk(tree):
        if isinstance(node, ast.Module):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc and node.body and isinstance(node.body[0], ast.Expr):
                docstring_lines.add(node.body[0].lineno)
    return docstring_lines


def check_file(path: Path) -> tuple[Path, list[str]]:
    issues = []
    try:
        source_bytes = path.read_bytes()
        docstring_lines = find_docstring_lines(source_bytes)
        import io
        import tokenize

        tokens = list(tokenize.tokenize(io.BytesIO(source_bytes).readline))
        for tok in tokens:
            start_line = tok.start[0]
            tok_str = tok.string
            if tok.type == tokenize.COMMENT:
                if start_line == 1 and tok_str.startswith("#!"):
                    continue
                issues.append(f"  Line {start_line}: Comment -> {tok_str.strip()}")
            elif tok.type == tokenize.STRING:
                if start_line in docstring_lines:
                    first_line = tok_str.splitlines()[0]
                    issues.append(f"  Line {start_line}: Docstring -> {first_line}...")
    except Exception as e:
        issues.append(f"  [ERROR] Failed to parse file: {e}")
    return path, issues


def collect_files(inputs: list[str]) -> list[Path]:
    files = set()
    if not inputs:
        return list(Path().rglob("*.py"))
    for item in inputs:
        p = Path(item)
        if p.is_file() and p.suffix == ".py":
            files.add(p)
        elif p.is_dir():
            files.update(p.rglob("*.py"))
    return list(files)


def main():
    parser = argparse.ArgumentParser(description="Check Python files for unstripped comments/docstrings.")
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Files or directories to check (defaults to '.' recursively)",
    )
    args = parser.parse_args()
    files = collect_files(args.inputs)
    if not files:
        print("No Python files found to inspect.")
        return
    print(f"Checking {len(files)} file(s) across 8 processes...\n")
    dirty_files = 0
    results = []
    with mp.Pool(processes=8) as pool:
        async_results = [pool.apply_async(check_file, args=(f,)) for f in files]
        for res in async_results:
            path, issues = res.get()
            if issues:
                dirty_files += 1
                print(f"[FAIL] {path}")
                for issue in issues:
                    print(issue)
                print()
    print("=" * 40)
    if dirty_files == 0:
        print(f"SUCCESS: All {len(files)} Python files are clean!")
    else:
        print(f"RESULT: Found issues in {dirty_files} of {len(files)} files.")


if __name__ == "__main__":
    main()
