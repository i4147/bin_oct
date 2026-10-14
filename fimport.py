#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that analyzes the source code of other Python files and reports on import statements that are placed inside nested scopes rather than at the module's top level. The tool should accept one or more file or directory paths as input (recursively scanning directories for Python files), parse each file safely without executing it, and identify every import statement (both standard and "from ... import" forms) that appears within a function, async function, class body, or control-flow block such as loops or conditionals. For each finding, it should report the file path, the line number, the import statement as written, and the enclosing context where it occurs. Handle files that cannot be parsed due to syntax errors gracefully by reporting them without stopping the overall run. The output should be a clear, human-readable summary grouped by file, with a total count at the end, and the tool should exit with a non-zero status code when any non-top-level imports are found so it can be used in automated checks. Include a simple option to output results in a machine-readable format, and make sure the tool handles missing paths and unreadable files with informative error messages.
---"""

from __future__ import annotations
import ast
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    pass


class ImportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self._nesting_level = 0
        self.non_top_level_imports: list[ast.stmt] = []

    def _is_top_level(self) -> bool:
        return self._nesting_level == 0

    def _visit_nested(self, node: ast.AST) -> None:
        self._nesting_level += 1
        self.generic_visit(node)
        self._nesting_level -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_nested(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_nested(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._visit_nested(node)

    def visit_For(self, node: ast.For) -> None:
        self._visit_nested(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_nested(node)

    def visit_While(self, node: ast.While) -> None:
        self._visit_nested(node)

    def visit_If(self, node: ast.If) -> None:
        self._visit_nested(node)

    def visit_With(self, node: ast.With) -> None:
        self._visit_nested(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self._visit_nested(node)

    def visit_Try(self, node: ast.Try) -> None:
        self._visit_nested(node)

    def visit_Import(self, node: ast.Import) -> None:
        if not self._is_top_level():
            self.non_top_level_imports.append(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if not self._is_top_level():
            self.non_top_level_imports.append(node)
        self.generic_visit(node)


def find_python_files(root: Path) -> Iterable[Path]:
    return root.rglob("*.py")


def format_import(node: ast.stmt) -> str:
    if isinstance(node, ast.Import):
        parts = []
        for alias in node.names:
            if alias.asname:
                parts.append(f"{alias.name} as {alias.asname}")
            else:
                parts.append(alias.name)
        return "import " + ", ".join(parts)
    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        parts = []
        for alias in node.names:
            if alias.asname:
                parts.append(f"{alias.name} as {alias.asname}")
            else:
                parts.append(alias.name)
        level_dots = "." * (node.level or 0)
        module_str = level_dots + module if module else level_dots
        return f"from {module_str} import " + ", ".join(parts)
    return "<unknown import>"


def inspect_file(path: Path):
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        source = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        print(f"[WARN] Skipping {path} (syntax error: {e})")
        return []
    visitor = ImportVisitor()
    visitor.visit(tree)
    results = []
    for node in visitor.non_top_level_imports:
        lineno = getattr(node, "lineno", "?")
        results.append((lineno, format_import(node)))
    return results


def main() -> None:
    root = Path.cwd()
    any_found = False
    for py_file in find_python_files(root):
        imports = inspect_file(py_file)
        if not imports:
            continue
        any_found = True
        print(f"\n{py_file}:")
        for lineno, stmt in imports:
            print(f"  line {lineno}: {stmt}")
    if not any_found:
        print("No non-top-level imports found.")


if __name__ == "__main__":
    raise SystemExit(main())
