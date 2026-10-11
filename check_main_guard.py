#!/data/data/com.termux/files/usr/bin/python
"""Write that instructs an AI coding agent to build a Python 3 command-line tool with the following specification:

Build a standalone Python 3 command-line script (intended to run under Termux on Android, so use a shebang pointing to the Termux Python path, `/data/data/com.termux/files/usr/bin/python`) that scans a directory tree and reports every Python source file that lacks an `if __name__ == "__main__":` guard.

Requirements:

1. **Purpose**: Recursively find all files under a target directory and determine, for each candidate Python file, whether it contains a top-level main guard of the form `if __name__ == "__main__":` (or the equivalent with the operands in reversed order). Output the list of files that do not have such a guard.

2. **Imports and setup**: Use only the standard library. Use `from __future__ import annotations`, `ast`, `sys`, `warnings`, `collections.abc.Iterator`, and `pathlib.Path`. Suppress all warnings globally with `warnings.filterwarnings("ignore")`.

3. **File enumeration**: Implement a generator function `walk_files(directory: Path) -> Iterator[Path]` that uses `Path.walk()` to traverse the directory tree recursively and yields the full path of every regular file found (files only, not directories). Yield paths in the order produced by the walk.

4. **Main guard detection**: Implement `has_main_guard(filepath: Path) -> bool` as follows:
   - Read the file as UTF-8 text. If reading fails due to `UnicodeDecodeError` or `OSError`, print a warning to stderr in the form `  ! Could not read <filename>: <error>` and return `True` (treat unreadable files as if they are not to be reported).
   - Parse the source with `ast.parse`, passing the filename for error context. If a `SyntaxError` occurs, print `  ! Syntax error in <filename>: <error>` to stderr and return `True`.
   - Walk the entire AST with `ast.walk` (not just top-level statements) and examine every `ast.If` node. For each, the test must be an `ast.Compare` with exactly one operator, which must be `ast.Eq`. The two operands must be, in either order: the name `__name__` (an `ast.Name` with id `__name__`) and the string constant `"__main__"` (an `ast.Constant` whose value equals `"__main__"`). Define small nested helper predicates for these two checks.
   - If a matching node is found, return `True`; otherwise return `False`.

5. **Main program behavior**:
   - Accept a directory path as the first command-line argument (`sys.argv[1]`). If no argument is given, print a usage message to stderr and exit with a nonzero status code (e.g., 1). Accept the directory as a path string and convert it to `Path`.
   - Validate that the path exists and is a directory; otherwise print an error to stderr and exit nonzero.
   - Iterate over all files via `walk_files`. Consider only files whose suffix is `.py` (case-sensitive). For each such file, call `has_main_guard`; if it returns `False`, print the file path to stdout (one per line, as the full path or path relative to the target directory as a consistent choice, documented in code).
   - Non-`.py` files are skipped silently.
   - Print nothing else to stdout apart from the list of offending files, so the output is pipe-friendly.

6. **Error handling and edge cases**:
   - Empty directories or directories with no `.py` files produce no output and exit with status 0.
   - Files with BOM, non-UTF-8 encodings, syntax errors, or permission problems must not crash the program; they are handled as described above.
   - Symbolic links: follow the behavior of `Path.walk()` defaults; do not attempt to resolve cycles manually.
   - Guard detection must recognize the guard even when nested inside functions, classes, or other blocks, because `ast.walk` visits all nodes.
   - Comparisons such as `__name__ != "__main__"`, `__name__ == "other"`, or chained comparisons do not count as a guard.

7. **Execution**: Run as `python <script> <directory>`. Exit status is 0 on normal completion regardless of how many files are reported, nonzero only for usage or invalid-directory errors. Include a `main()` function and an `if __name__ == "__main__":` guard at the bottom of the script that calls it and exits with the returned code.

8. **Style**: Use type hints throughout, concise docstrings or comments where helpful, and small focused helper functions defined at module level or nested as appropriate.

Deliver the complete script as a single file.
---"""

from __future__ import annotations

import ast
import sys
import warnings
from collections.abc import Iterator
from pathlib import Path

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
