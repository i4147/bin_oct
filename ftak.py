#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that recursively scans all .py files under the current working directory to find empty stub definitions, meaning classes, functions, or async functions whose body consists solely of a docstring.
It should use the ast module to parse each file (skipping files that fail to decode or contain syntax errors), walk the AST to identify matching class/function definitions, and collect their kind, name, and line number.
The main function should iterate through all discovered Python files, scan each for these stub definitions, and report the findings for files that contain at least one."""

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
