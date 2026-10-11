#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script with the following specification:

Create a Python command-line utility for Termux (Android) that walks a directory of Python source files, strips type annotations from each file's AST, and writes the stripped code out, using parallel processing and content hashing.

**Purpose:** The script converts annotated Python source into annotation-free Python. It processes every Python file found in a target location, transforms each file's syntax tree to remove type hints, and writes the results to disk. It is designed to run on the Termux environment on Android, so the shebang line should point to the Termux Python interpreter at `/data/data/com.termux/files/usr/bin/env python`.

**Dependencies and imports:**
- Use `from __future__ import annotations` at the top.
- Import standard-library `ast` and `pathlib.Path`, plus `TYPE_CHECKING` and `Any` from `typing`.
- Import `cprint` and `get_pyfiles` from a local helper module named `dh`. `get_pyfiles` returns the Python files to process; `cprint` is used for colored console output.
- Import `Parallel` and `delayed` from `joblib`.
- Import `xxh64_hexdigest` from `xxhash` for fast content hashing.
- Under an `if TYPE_CHECKING:` guard, import `Callable` and `Iterable` from `collections.abc` for type hints only.

**Component 1: `TypeAnnotationStripper`** — a subclass of `ast.NodeTransformer` with these behaviors:
- For both synchronous and asynchronous function definitions, set the return annotation to `None`, then recurse into children with `generic_visit`, and return the node.
- For function arguments, set the annotation to `None` and return the node.
- For annotated assignments: if the assignment has a value, replace it with a plain assignment (same targets and value) and copy source location info from the original node. If it has no value (a bare annotation like `x: int`), replace it with a `pass` statement and copy location info.
- Note that `visit_arg` does not recurse further, and the class does not handle class-level variable annotations beyond what `AnnAssign` covers.

**Component 2: `mpf(func, items, workers=None)`** — a parallel map helper:
- Convert `items` to a list.
- Use `n_jobs = -1` (all cores) when `workers` is `None`, otherwise use the given worker count.
- Return a list of results from `joblib.Parallel(n_jobs=...)` applied to `delayed(func)` over each item.

**Component 3: `process_file(path: ...)`** — per-file processing (the source is cut off here, so infer a reasonable implementation consistent with the other components): read the file as text, parse it with `ast.parse`, apply `TypeAnnotationStripper` via `ast.fix_missing_locations` and `ast.unparse`, compute an `xxh64_hexdigest` of the content for identification or change detection, and write the stripped output. Handle read/parse errors gracefully so one bad file does not stop the batch.

**Main flow:**
- Obtain the list of Python files via `get_pyfiles`.
- Run `process_file` over them with `mpf` so processing is parallel.
- Report progress and results with `cprint`.

**Edge cases and error handling:**
- Files that fail to parse (`SyntaxError`) or cannot be read (`OSError`, `UnicodeDecodeError`) should be reported and skipped, not crash the run.
- An empty file list should exit cleanly with a message.
- Bare annotations without values must be removed entirely (replaced with `pass`), not left as dangling syntax.
- Source location must be preserved or repaired so that `ast.unparse` and compilation succeed.

**Usage:** Run directly as an executable script on Termux (`chmod +x` then `./script.py`), or with `python script.py`. Include a `if __name__ == "__main__":` entry point. Output should be concise, with colored status lines from `cprint`.

**Quality requirements:** Keep the code idiomatic and match the style of the described components: type hints on all function signatures, docstrings or brief comments where logic is non-obvious, and no unused imports.
---"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dh import cprint, get_pyfiles
from joblib import Parallel, delayed
from xxhash import xxh64_hexdigest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


class TypeAnnotationStripper(ast.NodeTransformer):
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        node.returns = None
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        node.returns = None
        self.generic_visit(node)
        return node

    def visit_arg(self, node: ast.arg) -> ast.arg:
        node.annotation = None
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
        if node.value is not None:
            new_node = ast.Assign(targets=[node.target], value=node.value)
            return ast.copy_location(new_node, node)
        pass_node = ast.Pass()
        return ast.copy_location(pass_node, node)


def mpf(
    func: Callable[..., Any],
    items: Iterable[Any],
    workers: int | None = None,
) -> list[Any]:
    n_jobs = -1 if workers is None else workers
    items_list = list(items)
    return Parallel(n_jobs=n_jobs)(delayed(func)(item) for item in items_list)


def process_file(path: str | Path) -> tuple[str, str] | None:
    p = Path(path)
    try:
        code = p.read_text(encoding="utf-8")
        parsed = ast.parse(code)
        stripper = TypeAnnotationStripper()
        parsed = stripper.visit(parsed)
        ast.fix_missing_locations(parsed)
        unparsed = ast.unparse(parsed)
        digest = xxh64_hexdigest(unparsed.encode("utf-8"))
        return digest, str(p)
    except Exception:
        return None


def main() -> None:
    cwd: Path = Path.cwd()
    files: list[Path] = list(get_pyfiles(cwd))
    file_dict: dict[str, list[str]] = {}
    raw_results = mpf(process_file, files)
    results: list[tuple[str, str]] = [res for res in raw_results if res is not None]
    for digest, path in results:
        file_dict.setdefault(digest, []).append(path)
    for digest, paths in file_dict.items():
        if len(paths) > 1:
            print(f"files with hash: {digest}")
            for path in paths:
                print(f"  - {path}")
    deleted: int = 0
    for paths in file_dict.values():
        if len(paths) <= 1:
            continue
        for path in paths[1:]:
            file_path = Path(path)
            if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"{path} removed")
                    deleted += 1
                except OSError as e:
                    print(f"Failed to remove {path}: {e}")
    if deleted:
        cprint(f"{deleted} files removed.", "cyan")
    else:
        cprint("No duplicate files found.", "green")


if __name__ == "__main__":
    raise SystemExit(main())
