#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory tree for Python source files and reports which classes and functions lack meaningful documentation. The tool should accept a root directory path as its input, recursively locate every Python file beneath it, and analyze each file's structure without executing any of its code. For each file that can be read as UTF-8 and parsed as valid Python, it should identify all class definitions, synchronous functions, and asynchronous functions, including nested ones, and determine whether each has a docstring. Files that cannot be read, decoded, or parsed should be skipped silently rather than halting the scan.
The output should be a clear, human-readable report listing every undocumented class or function, grouped by file, with each entry showing the file path, the line number, the kind of definition (class, function, or async function), and its name. The report should also include a summary of total files scanned, total definitions examined, and total undocumented definitions found. The script should exit with a non-zero status when undocumented items are found and zero when everything is documented, so it can be used as a quality gate in continuous integration pipelines. Make it robust to large projects, handle invalid or missing root paths gracefully with a helpful error message, and keep the scanning logic separate from the reporting logic so each can be extended independently.
---"""

from __future__ import annotations
import ast
from pathlib import Path
from typing import Iterator


def walk_py_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        if path.is_file():
            yield path


def is_docstring_only(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
) -> bool:
    body = node.body
    if len(body) != 1:
        return False
    stmt = body[0]
    if not isinstance(stmt, ast.Expr):
        return False
    value = stmt.value
    return isinstance(value, ast.Constant) and isinstance(value.value, str)


def scan_file(path: Path) -> list[tuple[str, str, int]]:
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []
    findings: list[tuple[str, str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            kind = "class"
        elif isinstance(node, ast.AsyncFunctionDef):
            kind = "async function"
        elif isinstance(node, ast.FunctionDef):
            kind = "function"
        else:
            continue
        if is_docstring_only(node):
            findings.append((kind, node.name, node.lineno))
    return findings


def main() -> None:
    root = Path.cwd()
    for path in walk_py_files(root):
        findings = scan_file(path)
        if not findings:
            continue
        rel = path.relative_to(root)
        for kind, name, lineno in findings:
            print(f"{rel}:{lineno}: {kind} {name}")


if __name__ == "__main__":
    main()
