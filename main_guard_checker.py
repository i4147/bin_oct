#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import argparse
import ast
import multiprocessing as mp
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional, Sequence

DEFAULT_EXCLUDES = (
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
)
MAIN_GUARD_PATTERN = re.compile(r"if\s+__name__\s*==\s*[\"\']__main__[\"\']\s*:")
MAIN_FUNC_TEMPLATE_REGEX = (
    "\n\ndef main() -> None:\n"
    '    """Entry point for the script."""\n'
    "    # TODO: Add your main logic here\n"
    '    print("Hello from main!")\n'
)
MAIN_GUARD_TEMPLATE_REGEX = '\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


@dataclass
class FileResult:
    path: Path
    status: Literal["skipped", "missing", "would_add", "added", "error", "fixed"]
    message: str = ""
    duration: float = 0.0


def has_main_guard_regex(content: str) -> bool:
    return bool(MAIN_GUARD_PATTERN.search(content))


def has_main_guard_ast(tree: ast.Module) -> bool:
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.If):
            test = node.test
            if not isinstance(test, ast.Compare):
                continue
            if not (len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)):
                continue
            left = test.left
            if not (isinstance(left, ast.Name) and left.id == "__name__"):
                continue
            if len(test.comparators) != 1:
                continue
            comp = test.comparators[0]
            if isinstance(comp, ast.Constant) and comp.value == "__main__":
                return True
    return False


def is_docstring_expr(node: ast.expr) -> bool:
    if not isinstance(node, ast.Expr):
        return False
    return bool(isinstance(node.value, ast.Constant) and isinstance(node.value.value, str))


def should_wrap_node_ast(node: ast.stmt) -> bool:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return False
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return False
    if is_docstring_expr(node):
        return False
    if isinstance(node, ast.If):
        test = node.test
        if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
            left = test.left
            if isinstance(left, ast.Name) and left.id == "__name__" and len(test.comparators) == 1:
                comp = test.comparators[0]
                if isinstance(comp, ast.Constant) and comp.value == "__main__":
                    return False
    return True


def indent_block(block: str, spaces: int = 4) -> str:
    prefix = " " * spaces
    lines = block.splitlines(True)
    out = []
    for ln in lines:
        if ln.strip() == "":
            out.append(ln)
        else:
            out.append(prefix + ln)
    return "".join(out)


def fix_file_ast(path: Path) -> FileResult:
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        return FileResult(path, "error", f"Parse error: {e}")
    if has_main_guard_ast(tree):
        return FileResult(path, "skipped", "Already has main guard")
    nodes = list(tree.body)
    wrap_nodes = [n for n in nodes if should_wrap_node_ast(n)]
    if not wrap_nodes:
        return FileResult(path, "skipped", "Nothing to wrap")
    lines = src.splitlines(True)

    def segment(start: int, end: int) -> str:
        return "".join(lines[start - 1 : end])

    main_parts = []
    keep_segments = []
    for n in nodes:
        start = getattr(n, "lineno", None)
        end = getattr(n, "end_lineno", None)
        if not isinstance(start, int) or not isinstance(end, int):
            return FileResult(path, "error", "Missing lineno/end_lineno (AST limitation)")
        if should_wrap_node_ast(n):
            main_parts.append(segment(start, end).rstrip() + "\n")
        else:
            keep_segments.append((start, end))
    keep_segments.sort()
    new_parts = []
    cursor = 1
    for start, end in keep_segments:
        if start > cursor:
            new_parts.append("".join(lines[cursor - 1 : start - 1]))
        new_parts.append("".join(lines[start - 1 : end]))
        cursor = end + 1
    if cursor <= len(lines):
        new_parts.append("".join(lines[cursor - 1 :]))
    main_body = "".join(main_parts).rstrip("\n")
    main_fn = "\n\ndef main():\n"
    if main_body.strip() == "":
        main_fn += "    pass\n"
    else:
        main_fn += indent_block(main_body + "\n", 4).rstrip("\n") + "\n"
    main_fn += '\n\nif __name__ == "__main__":\n'
    main_fn += "    raise SystemExit(main())\n"
    new_src = "".join(new_parts).rstrip() + main_fn
    path.write_text(new_src, encoding="utf-8")
    return FileResult(path, "fixed", "Wrapped code in main() and added guard")


def fix_file_regex(path: Path, dry_run: bool = False) -> FileResult:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return FileResult(path, "error", f"Failed to read: {exc}")
    if has_main_guard_regex(content):
        return FileResult(path, "skipped", "Already has guard")
    new_content = content.rstrip() + MAIN_GUARD_TEMPLATE_REGEX
    if dry_run:
        return FileResult(path, "would_add", "Would add guard (dry-run)")
    try:
        path.write_text(new_content, encoding="utf-8")
    except OSError as exc:
        return FileResult(path, "error", f"Failed to write: {exc}")
    return FileResult(path, "added", "Added guard successfully")


def find_python_files(directory: Path, exclude_patterns: Sequence[str]) -> list[Path]:
    if not directory.exists():
        return []
    excluded = frozenset(exclude_patterns)
    results = []
    for path in directory.rglob("*.py"):
        if excluded.intersection(path.parts):
            continue
        results.append(path)
    return sorted(results)


def iter_py_files(inputs: Sequence[str]) -> list[Path]:
    if not inputs:
        roots = [Path()]
    else:
        roots = [Path(p) for p in inputs]
    out = []
    for r in roots:
        if r.is_dir():
            out.extend(sorted(x for x in r.rglob("*.py") if x.is_file()))
        elif r.suffix == ".py" and r.is_file():
            out.append(r)
    return sorted(set(out))


def check_files(files: list[Path]) -> dict[str, list]:
    results = {"missing": [], "skipped": [], "errors": []}
    for f in files:
        src = f.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src, filename=str(f))
        except SyntaxError:
            results["errors"].append((f, "Parse error"))
            continue
        if has_main_guard_ast(tree):
            results["skipped"].append(f)
        else:
            results["missing"].append(f)
    return results


def fix_files_sequential(files: list[Path], method: Literal["ast", "regex"], dry_run: bool = False) -> dict:
    results = {"fixed": [], "added": [], "would_add": [], "skipped": [], "errors": []}
    fix_func = fix_file_ast if method == "ast" else fix_file_regex
    for f in files:
        result = fix_func(f, dry_run) if method == "regex" else fix_func(f)
        if result.status == "fixed":
            results["fixed"].append(f)
        elif result.status == "added":
            results["added"].append(f)
        elif result.status == "would_add":
            results["would_add"].append(f)
        elif result.status == "skipped":
            results["skipped"].append(f)
        elif result.status == "error":
            results["errors"].append((f, result.message))
        print(f"{f}: {result.status} - {result.message}")
    return results


def fix_files_parallel(
    files: list[Path], method: Literal["ast", "regex"], num_workers: int, dry_run: bool = False
) -> dict:
    results = {"fixed": [], "added": [], "would_add": [], "skipped": [], "errors": []}
    fix_func = fix_file_ast if method == "ast" else fix_file_regex
    with mp.Pool(processes=num_workers) as pool:
        if method == "regex":
            async_results = [pool.apply_async(fix_func, (f, dry_run)) for f in files]
        else:
            async_results = [pool.apply_async(fix_func, (f,)) for f in files]
        for idx, ar in enumerate(async_results, 1):
            result = ar.get()
            if result.status == "fixed":
                results["fixed"].append(result.path)
            elif result.status == "added":
                results["added"].append(result.path)
            elif result.status == "would_add":
                results["would_add"].append(result.path)
            elif result.status == "skipped":
                results["skipped"].append(result.path)
            elif result.status == "error":
                results["errors"].append((result.path, result.message))
            print(f"[{idx}/{len(files)}] {result.path}: {result.status}")
    return results


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect and add main guard to Python files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")
    check_parser = subparsers.add_parser("check", help="Detect missing guards")
    check_parser.add_argument("paths", nargs="*", help="Files or directories to scan (default: current dir)")
    check_parser.add_argument("--exclude", nargs="+", default=[], help="Directories to exclude")
    fix_parser = subparsers.add_parser("fix", help="Add guards to files")
    fix_parser.add_argument("paths", nargs="*", help="Files or directories to scan (default: current dir)")
    fix_parser.add_argument("--method", choices=["ast", "regex"], default="ast", help="Fix method")
    fix_parser.add_argument("--exclude", nargs="+", default=[], help="Directories to exclude")
    fix_parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    fix_parser.add_argument("--parallel", type=int, default=0, help="Number of workers (0=sequential)")
    args = parser.parse_args(argv)
    if not args.mode:
        parser.print_help()
        return 0
    if args.mode == "check":
        files = iter_py_files(args.paths) if args.paths else iter_py_files([])
        results = check_files(files)
        missing = len(results["missing"])
        skipped = len(results["skipped"])
        errors = len(results["errors"])
        print(f"\n📋 Summary: {missing} missing, {skipped} with guard, {errors} errors")
        if missing > 0:
            print(f"Files missing main guard:")
            for f in sorted(results["missing"]):
                print(f"  {f}")
        return 0 if missing == 0 else 1
    elif args.mode == "fix":
        exclude_patterns = DEFAULT_EXCLUDES + tuple(args.exclude)
        directory = Path(args.paths[0]) if args.paths else Path()
        files = find_python_files(directory, exclude_patterns)
        if not files:
            print(f"No Python files found in {directory}")
            return 0
        print(f"Found {len(files)} Python files")
        if args.parallel > 0:
            results = fix_files_parallel(files, args.method, args.parallel, args.dry_run)
        else:
            results = fix_files_sequential(files, args.method, args.dry_run)
        print(f"\n📊 Results:")
        print(f"  Fixed: {len(results['fixed'])}")
        print(f"  Added: {len(results['added'])}")
        print(f"  Would add (dry-run): {len(results['would_add'])}")
        print(f"  Skipped: {len(results['skipped'])}")
        print(f"  Errors: {len(results['errors'])}")
        if results["errors"]:
            print("\n❌ Errors:")
            for path, msg in results["errors"]:
                print(f"  {path}: {msg}")
            return 2
        return 0
    return None


if __name__ == "__main__":
    raise SystemExit(main())
