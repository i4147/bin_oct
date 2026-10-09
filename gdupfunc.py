#!/data/data/com.termux/files/usr/bin/python
"""
Advanced Python 3.14 Duplicate Code Detector
----------------------------------------------
Target Runtime: Python 3.14+
Features:
  - Uses Python 3.14 `concurrent.futures.InterpreterPoolExecutor` (subinterpreters with per-interpreter GIL).
  - Parallel AST normalization and fuzzy variable alpha-renaming.
  - Detects objects differing in type annotations across instances.
  - Strips docstrings & trivial AST structures.
  - Generates JSON outputs and an interactive HTML report in `./output/`.
"""

from __future__ import annotations
import argparse
import ast
from concurrent.futures import InterpreterPoolExecutor
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Set, Tuple


# Directories to ignore automatically during recursive parsing
DEFAULT_EXCLUDES: set[str] = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "build",
    "dist",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "output",
}

# Minimum AST node count to skip trivial statements/functions
MIN_AST_NODES: int = 5


# ----------------------------------------------------------------------
# AST Normalization & Analysis
# ----------------------------------------------------------------------


class TypeAnnotationChecker(ast.NodeVisitor):
    """Recursively checks if an AST node contains type annotations."""

    def __init__(self):
        self.has_annotations = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.returns:
            self.has_annotations = True
        for arg in node.args.args + node.args.kwonlyargs:
            if arg.annotation:
                self.has_annotations = True
        if node.args.vararg and node.args.vararg.annotation:
            self.has_annotations = True
        if node.args.kwarg and node.args.kwarg.annotation:
            self.has_annotations = True
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_FunctionDef(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        self.has_annotations = True
        self.generic_visit(node)


class CodeNormalizer(ast.NodeTransformer):
    """
    Normalizes an AST node by:
      1. Stripping docstrings.
      2. Stripping type annotations.
      3. Renaming local variables systematically (alpha-renaming) for fuzzy matching.
    """

    def __init__(self, fuzzy: bool = True):
        super().__init__()
        self.fuzzy = fuzzy
        self.var_map: dict[str, str] = {}
        self.var_counter = 0

    def _get_norm_var(self, name: str) -> str:
        """Maps local variable names to standardized placeholders (var_0, var_1, etc.)."""
        if not self.fuzzy or name.startswith("__") or name.isupper():
            return name
        if name not in self.var_map:
            self.var_map[name] = f"var_{self.var_counter}"
            self.var_counter += 1
        return self.var_map[name]

    def _strip_docstring(self, node: Any):
        """Removes docstrings from functions, classes, and modules."""
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module))
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            node.body.pop(0)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._strip_docstring(node)
        node.returns = None
        for arg in node.args.args + node.args.kwonlyargs:
            arg.annotation = None
            if self.fuzzy:
                arg.arg = self._get_norm_var(arg.arg)
        if node.args.vararg:
            node.args.vararg.annotation = None
            if self.fuzzy:
                node.args.vararg.arg = self._get_norm_var(node.args.vararg.arg)
        if node.args.kwarg:
            node.args.kwarg.annotation = None
            if self.fuzzy:
                node.args.kwarg.arg = self._get_norm_var(node.args.kwarg.arg)
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        return self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self._strip_docstring(node)
        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if node.value is not None:
            new_node = ast.Assign(targets=[node.target], value=node.value)
            return self.visit(new_node)
        return None

    def visit_Name(self, node: ast.Name):
        if self.fuzzy and isinstance(node.ctx, (ast.Store, ast.Load)):
            node.id = self._get_norm_var(node.id)
        return node


def get_canonical_structure(node: ast.AST, fuzzy: bool = True) -> str:
    """Generates normalized canonical code representation for AST comparison."""
    node_copy = ast.parse(ast.unparse(node))
    normalized_node = CodeNormalizer(fuzzy=fuzzy).visit(node_copy)
    return ast.unparse(normalized_node)


def has_type_annotations(node: ast.AST) -> bool:
    """Checks if the AST node contains any type annotations."""
    checker = TypeAnnotationChecker()
    checker.visit(node)
    return checker.has_annotations


def count_ast_nodes(node: ast.AST) -> int:
    """Counts total AST sub-nodes to evaluate structural complexity."""
    return sum(1 for _ in ast.walk(node))


# ----------------------------------------------------------------------
# Worker Function Executed Across Subinterpreters
# ----------------------------------------------------------------------


def process_file_task(task_args: tuple[str, bool, int]) -> list[dict[str, Any]]:
    """
    Parses a single Python file.
    Accepts string file path for fast subinterpreter IPC serialization.
    """
    file_str, enable_fuzzy, min_nodes = task_args
    file_path = Path(file_str)
    extracted_objects = []

    try:
        source_code = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source_code, filename=file_str)
    except (SyntaxError, UnicodeDecodeError, PermissionError):
        return extracted_objects

    for node in ast.iter_child_nodes(tree):
        if count_ast_nodes(node) < min_nodes:
            continue

        obj_type = None
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            obj_type = "function"
        elif isinstance(node, ast.ClassDef):
            obj_type = "class"
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id.isupper() for t in targets):
                obj_type = "constant"

        if obj_type:
            canonical_code = get_canonical_structure(node, fuzzy=enable_fuzzy)
            extracted_objects.append({
                "type": obj_type,
                "name": getattr(node, "name", ast.unparse(node)),
                "file": file_str,
                "line": node.lineno,
                "raw_code": ast.unparse(node),
                "canonical_code": canonical_code,
                "has_annotations": has_type_annotations(node),
            })

    return extracted_objects


# ----------------------------------------------------------------------
# HTML Dashboard Generator
# ----------------------------------------------------------------------


def generate_html_report(categorized_duplicates: dict[str, list[dict[str, Any]]], output_path: Path):
    """Generates an interactive HTML dashboard highlighting duplicate code blocks."""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Python 3.14 Duplicate Code Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 20px; background: #f8f9fa; color: #333; }}
        h1, h2 {{ color: #1e293b; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .tag {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; font-family: monospace; }}
        .tag-warning {{ background: #fef3c7; color: #92400e; }}
        .tag-success {{ background: #d1fae5; color: #065f46; }}
        pre {{ background: #0f172a; color: #f8fafc; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 13px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
        th {{ background: #f1f5f9; }}
    </style>
</head>
<body>
    <h1>Python 3.14 Duplicate Code Inspection Report</h1>
    <p>Powered by Python 3.14 <code>InterpreterPoolExecutor</code> parallel AST parsing.</p>
"""

    for obj_type, entries in categorized_duplicates.items():
        if not entries:
            continue
        html_content += f"<h2>{obj_type.capitalize()} Duplicates ({len(entries)})</h2>"
        for idx, entry in enumerate(entries, 1):
            annotation_badge = (
                '<span class="tag tag-warning">Differs in Type Annotations</span>'
                if entry["differ_in_type_annotations"]
                else '<span class="tag tag-success">Identical Annotations</span>'
            )
            html_content += f"""
            <div class="card">
                <h3>#{idx} Canonical Pattern ({entry["count"]} occurrences) {annotation_badge}</h3>
                <pre><code>{entry["canonical_code"]}</code></pre>
                <table>
                    <thead>
                        <tr><th>File Path</th><th>Line Number</th><th>Has Type Annotations</th></tr>
                    </thead>
                    <tbody>
            """
            for inst in entry["instances"]:
                html_content += f"""
                    <tr>
                        <td><code>{inst["file"]}</code></td>
                        <td>{inst["line"]}</td>
                        <td>{"Yes" if inst["has_annotations"] else "No"}</td>
                    </tr>
                """
            html_content += "</tbody></table></div>"

    html_content += "</body></html>"
    output_path.write_text(html_content, encoding="utf-8")


# ----------------------------------------------------------------------
# Main Entry Point
# ----------------------------------------------------------------------


def main():
    # Verify Python runtime version requirement
    if sys.version_info < (3, 14):
        sys.exit("Error: This script requires Python 3.14 or newer to use InterpreterPoolExecutor.")

    parser = argparse.ArgumentParser(description="Python 3.14 Duplicate Detector via Subinterpreters")
    parser.add_argument("--dir", type=str, default=".", help="Root directory to scan recursively")
    parser.add_argument("--disable-fuzzy", action="store_true", help="Disable variable alpha-renaming matching")
    parser.add_argument("--min-nodes", type=int, default=MIN_AST_NODES, help="Minimum AST node count threshold")
    parser.add_argument("--max-duplicates", type=int, default=-1, help="Max duplicates allowed before exit failure")
    args = parser.parse_args()

    root_dir = Path(args.dir).resolve()
    output_dir = Path.cwd() / "output"
    output_dir.mkdir(exist_ok=True)

    # Collect target files
    python_files = [
        str(p)
        for p in root_dir.rglob("*.py")
        if not any(part in DEFAULT_EXCLUDES for part in p.parts) and output_dir not in p.parents
    ]

    print(f"Scanning {len(python_files)} Python file(s) using Python 3.14 InterpreterPoolExecutor...")

    tasks = [(p, not args.disable_fuzzy, args.min_nodes) for p in python_files]

    # Execute parallel scanning via Python 3.14 subinterpreters
    with InterpreterPoolExecutor() as executor:
        raw_results = list(executor.map(process_file_task, tasks))

    all_objects = [item for sublist in raw_results for item in sublist]

    # Group extracted constructs by type and canonical code
    grouped_objects: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for obj in all_objects:
        key = (obj["type"], obj["canonical_code"])
        grouped_objects.setdefault(key, []).append(obj)

    categorized_duplicates: dict[str, list[dict[str, Any]]] = {"function": [], "class": [], "constant": []}

    total_duplicates = 0
    annotation_diff_total = 0

    for (obj_type, canonical_code), instances in grouped_objects.items():
        if len(instances) > 1:
            total_duplicates += 1
            has_ann_set = {inst["has_annotations"] for inst in instances}
            differ_in_annotations = len(has_ann_set) > 1
            if differ_in_annotations:
                annotation_diff_total += 1

            entry = {
                "canonical_code": canonical_code,
                "count": len(instances),
                "differ_in_type_annotations": differ_in_annotations,
                "instances": [
                    {"file": inst["file"], "line": inst["line"], "has_annotations": inst["has_annotations"]}
                    for inst in instances
                ],
            }
            categorized_duplicates[obj_type].append(entry)

            if differ_in_annotations:
                for inst in instances:
                    print(
                        f"::warning file={inst['file']},line={inst['line']}::"
                        f"Duplicate {obj_type} detected with mismatched type annotations."
                    )

    # Export sorted JSON files
    for obj_type, entries in categorized_duplicates.items():
        entries.sort(key=lambda x: x["count"], reverse=True)
        json_file = output_dir / f"duplicate_{obj_type}s.json"
        json_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    # Export HTML report
    html_report_path = output_dir / "report.html"
    generate_html_report(categorized_duplicates, html_report_path)

    # Console Summary
    print("\n" + "=" * 50)
    print("PYTHON 3.14 SUBINTERPRETER SCAN SUMMARY")
    print("=" * 50)
    print(f"Total Unique Duplicated Patterns : {total_duplicates}")
    print(f"Annotation Mismatch Count        : {annotation_diff_total}")
    print("-" * 50)
    for obj_type, entries in categorized_duplicates.items():
        diff_count = sum(1 for e in entries if e["differ_in_type_annotations"])
        print(f"  - {obj_type.capitalize()}s: {len(entries)} duplicates ({diff_count} differ in type annotations)")
    print("-" * 50)
    print(f"JSON outputs saved to : {output_dir}/duplicate_*.json")
    print(f"HTML report saved to  : {html_report_path}")

    if args.max_duplicates >= 0 and total_duplicates > args.max_duplicates:
        print(f"\n[ERROR] Total duplicates ({total_duplicates}) exceeds allowed threshold ({args.max_duplicates}).")
        sys.exit(1)


if __name__ == "__main__":
    main()
