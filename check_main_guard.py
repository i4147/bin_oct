#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import ast
import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

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
