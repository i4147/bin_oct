#!/data/data/com.termux/files/usr/bin/python
"""Find duplicate Python files after normalizing away noise.

Normalization removes comments (incl. shebangs), docstrings, type
annotations, blank lines, and source positions. Two files are duplicates
when their normalized ASTs are identical.

The normalized AST is hashed with xxHash, then re-verified before any
deletion when ``-r`` is used.
"""

from __future__ import annotations

import argparse
import ast
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

from dh import cprint, get_pyfiles

try:
    from xxhash import xxh3_64_hexdigest as _hash_bytes
except ImportError:  # pragma: no cover
    from xxhash import xxh64_hexdigest as _hash_bytes

if TYPE_CHECKING:
    from collections.abc import Sequence

try:
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )

    _RICH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _RICH_AVAILABLE = False


# ---------------------------------------------------------------------------
# AST normalization
# ---------------------------------------------------------------------------


def _strip_docstring(node: ast.AST) -> None:
    """Remove the leading string-literal statement of a body-bearing node."""
    body = getattr(node, "body", None)
    if not body:
        return
    first = body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        del body[0]
        if not body and not isinstance(node, ast.Module):
            body.append(ast.Pass())


class Normalizer(ast.NodeTransformer):
    """Strip docstrings and type annotations from an AST in place."""

    def visit_Module(self, node: ast.Module) -> ast.AST:
        _strip_docstring(node)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        _strip_docstring(node)
        node.returns = None
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        _strip_docstring(node)
        node.returns = None
        return self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        _strip_docstring(node)
        return self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> ast.AST:
        node.annotation = None
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
        if node.value is not None:
            new_node = ast.Assign(targets=[node.target], value=node.value)
            return ast.copy_location(new_node, node)
        return ast.copy_location(ast.Pass(), node)


def canonicalize(path: Path) -> str | None:
    """Return a canonical (normalized, position-free) dump of *path*."""
    try:
        source = path.read_bytes()
        tree = ast.parse(source)
        Normalizer().visit(tree)
        return ast.dump(tree, include_attributes=False)
    except (SyntaxError, ValueError, OSError, MemoryError, RecursionError):
        return None


def process_file(path: Path) -> tuple[str, str] | None:
    canonical = canonicalize(path)
    if canonical is None:
        return None
    return _hash_bytes(canonical.encode("utf-8")), str(path)


# ---------------------------------------------------------------------------
# Parallel processing
# ---------------------------------------------------------------------------


def _process_batch(paths: Sequence[Path]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for p in paths:
        r = process_file(p)
        if r is not None:
            out.append(r)
    return out


def _make_progress() -> "Progress":
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    )


def _run_serial(paths: Sequence[Path], show_progress: bool) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    if show_progress and _RICH_AVAILABLE:
        with _make_progress() as progress:
            task = progress.add_task("Hashing files", total=len(paths))
            for p in paths:
                r = process_file(p)
                if r is not None:
                    results.append(r)
                progress.update(task, advance=1)
    else:
        for p in paths:
            r = process_file(p)
            if r is not None:
                results.append(r)
    return results


def process_files(
    paths: Sequence[Path],
    workers: int,
    show_progress: bool,
) -> list[tuple[str, str]]:
    if not paths:
        return []

    # Avoid process-pool overhead for small workloads.
    if workers <= 1 or len(paths) < 128:
        return _run_serial(paths, show_progress)

    batch_size = max(32, len(paths) // (workers * 4))
    batches = [paths[i : i + batch_size] for i in range(0, len(paths), batch_size)]

    results: list[tuple[str, str]] = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        if show_progress and _RICH_AVAILABLE:
            with _make_progress() as progress:
                task = progress.add_task("Hashing files", total=len(paths))
                futures = {ex.submit(_process_batch, b): len(b) for b in batches}
                for fut in as_completed(futures):
                    results.extend(fut.result())
                    progress.update(task, advance=futures[fut])
        else:
            for chunk in ex.map(_process_batch, batches):
                results.extend(chunk)
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dupfinder",
        description=(
            "Find (and optionally delete) duplicate Python files after "
            "normalizing away comments, docstrings, shebangs, "
            "type annotations, and blank lines."
        ),
    )
    parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Delete duplicate files (the first file of each group is kept).",
    )
    parser.add_argument(
        "--rich",
        action="store_true",
        help="Show a rich progress bar while hashing files.",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes (default: CPU count).",
    )
    parser.add_argument(
        "-d",
        "--dir",
        type=Path,
        default=Path.cwd(),
        help="Root directory to scan (default: current working directory).",
    )
    return parser


def _resolve_workers(requested: int | None) -> int:
    if requested is None:
        return max(1, os.cpu_count() or 1)
    return max(1, requested)


def _verify_group(paths: Sequence[str]) -> bool:
    """Re-canonicalize every path and confirm they are truly identical."""
    first: str | None = None
    for raw in paths:
        canonical = canonicalize(Path(raw))
        if canonical is None:
            return False
        if first is None:
            first = canonical
        elif canonical != first:
            return False
    return True


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    root: Path = args.dir.expanduser().resolve()
    if not root.exists():
        cprint(f"Path does not exist: {root}", "red")
        return 1

    files: list[Path] = [Path(p) for p in get_pyfiles(root)]
    if not files:
        cprint("No Python files found.", "yellow")
        return 0

    if args.rich and not _RICH_AVAILABLE:
        cprint("rich is not installed; --rich ignored.", "yellow")

    workers = _resolve_workers(args.workers)
    results = process_files(files, workers, args.rich and _RICH_AVAILABLE)

    groups: dict[str, list[str]] = {}
    for digest, path in results:
        groups.setdefault(digest, []).append(path)

    duplicates = {d: ps for d, ps in groups.items() if len(ps) > 1}
    if not duplicates:
        cprint("No duplicate files found.", "green")
        return 0

    extra = sum(len(ps) - 1 for ps in duplicates.values())
    for digest, paths in duplicates.items():
        print(f"files with hash: {digest}")
        for p in paths:
            print(f"  - {p}")
    print()
    cprint(f"{len(duplicates)} group(s), {extra} duplicate file(s).", "cyan")

    if not args.remove:
        cprint("Pass -r to delete duplicate files.", "yellow")
        return 0

    deleted = 0
    for paths in duplicates.values():
        if not _verify_group(paths):
            cprint(f"Skipping group due to hash collision: {paths[0]}", "red")
            continue
        for raw in paths[1:]:
            fp = Path(raw)
            try:
                fp.unlink()
                print(f"{raw} removed")
                deleted += 1
            except OSError as exc:
                cprint(f"Failed to remove {raw}: {exc}", "red")

    if deleted:
        cprint(f"{deleted} file(s) removed.", "cyan")
    else:
        cprint("Nothing was removed.", "green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
