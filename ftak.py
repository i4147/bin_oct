#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script with the following specification:

Create a standalone Python 3 command-line script, intended to run under Termux on Android (use the shebang `#!/data/data/com.termux/files/usr/bin/env python`). Its purpose is to scan the current working directory recursively for Python source files and report every class, sync function, and async function whose body consists solely of a single string literal (a docstring-only stub), listing each with its kind, name, and line number.

Requirements:

- Begin the file with the `from __future__ import annotations` import so that modern type-hint syntax works on older Python versions. Use only the standard library: `ast`, `pathlib.Path`, and `typing.Iterator`.
- Provide a generator helper that takes a root `Path` and yields every `*.py` file found recursively via `rglob`, skipping anything that is not a regular file.
- Provide a predicate that takes a function or class AST node (sync function, async function, or class definition) and returns true only when the node's body has exactly one statement, that statement is an expression statement, and its value is a string constant. Otherwise return false.
- Provide a per-file scanner that takes a `Path` and returns a list of tuples of `(kind, name, line_number)`, where kind is one of `"class"`, `"async function"`, or `"function"`. Behavior:
  - Read the file as UTF-8 text. If decoding fails or an OS-level read error occurs, silently return an empty list.
  - Parse the source with `ast.parse`, passing the file path as the filename. If a `SyntaxError` is raised, silently return an empty list.
  - Walk the entire AST with `ast.walk` (so nested definitions are included), classify each node by type (checking `ClassDef`, then `AsyncFunctionDef`, then `FunctionDef`, since order matters), skip all other node types, and record the finding when the docstring-only predicate holds, using the node's name and `lineno`.
- Provide a `main()` function with no return value that uses the current working directory as the root (`Path.cwd()`), iterates over the discovered files, scans each, and prints the results. Include a standard `if __name__ == "__main__":` guard calling `main()`.

Output expectations to specify for the agent: print findings in a clear, human-readable form that includes the relative file path (relative to the root), the line number, the kind, and the name, and print a summary count at the end. Print nothing noisy for files that are unreadable or unparsable. Keep the script free of third-party dependencies, comments limited to what is useful, and naming in plain snake_case. The script should be executable directly from the shell and should not require any arguments.
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
