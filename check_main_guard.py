#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a given directory tree recursively and reports which Python source files lack a proper script entry-point guard (the conventional conditional block that runs code only when the file is executed directly rather than imported). The script should accept a directory path as its main input, traverse all files within it (including nested subdirectories), and identify every Python file. For each Python file, it should read the source safely, handling encoding problems, I/O errors, and syntax errors gracefully by reporting a warning to the error stream and treating the file as already compliant so it is not flagged. It should analyze the file's structure rather than relying on plain text matching, detecting whether a conditional check compares the module's special name variable against the string representing the main program, accounting for both orderings of the comparison operands.
The output should be a clear summary listing the paths of Python files that are missing the entry-point guard, along with a total count of files scanned and files flagged. Suppress unnecessary runtime warnings so the output stays clean. The script should run from the command line, print helpful messages for missing or invalid directory arguments, and exit with a non-zero status when the input path is invalid. Keep the design modular and readable, and include a brief usage explanation in the help output.
---"""

from __future__ import annotations
import ast
from pathlib import Path
import sys
from typing import TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    from collections.abc import Iterator
warnings.filterwarnings("ignore")


def walk_files(directory: Path) -> Iterator[Path]:
    for root, _dirs, files in directory.walk():
        for name in files:
            yield root / name


def has_main_guard(filepath: Path) -> bool:
    try:
        source = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        print(f"  ! Could not read {filepath.name}: {e}", file=sys.stderr)
        return True
    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        print(f"  ! Syntax error in {filepath.name}: {e}", file=sys.stderr)
        return True
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not isinstance(test, ast.Compare):
            continue
        if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
            continue
        left, right = test.left, test.comparators[0]

        def is_dunder_name(n: ast.expr) -> bool:
            return isinstance(n, ast.Name) and n.id == "__name__"

        def is_main_string(n: ast.expr) -> bool:
            return isinstance(n, ast.Constant) and n.value == "__main__"

        if (is_dunder_name(left) and is_main_string(right)) or (is_dunder_name(right) and is_main_string(left)):
            return True
    return False


def main() -> int:
    cwd = Path.cwd()
    for p in walk_files(cwd):
        if p.is_file() and p.suffix == ".py" and p.name != Path(__file__).name and not has_main_guard(p):
            print(p.relative_to(cwd))
    return 0


if __name__ == "__main__":
    sys.exit(main())
