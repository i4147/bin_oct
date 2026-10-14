#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory tree for Python source files and produces a structural fingerprint of each file's top-level definitions, so that code can be compared across versions or projects without relying on exact text matching.
The tool should accept a root folder path as input and recursively locate all Python files beneath it. For each file, it should parse the source safely and gather the top-level functions, classes, and module-level constant assignments. Each definition should be reduced to a stable digest derived from its normalized structure, so that cosmetic differences such as whitespace or formatting do not change the result, while meaningful logic changes do. If a file cannot be read or parsed (for example due to syntax errors, encoding problems, or permission issues), the tool should record the error for that file and continue processing the rest without crashing.
The script should process files efficiently, taking advantage of parallel execution where it helps throughput on large codebases, and it should handle the results in a deterministic, reproducible order. The final output should be a machine-readable JSON report mapping each file's relative path to its collected definition digests or its error message, written either to a specified output file or to standard output. The tool should also be usable from the command line, with sensible defaults and clear handling of invalid or missing input paths.
Keep the implementation clean and robust: the report should be easy to diff between two runs, the tool should never modify the scanned files, and it should exit with a meaningful status code indicating whether any files failed to process.
---"""

from __future__ import annotations
import ast
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
from typing import Any


def hash_node(node: ast.AST) -> str:
    try:
        source = ast.unparse(node)
    except AttributeError:
        source = ast.dump(node)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def extract_definitions(path: Path) -> dict[str, Any] | None:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError, OSError) as e:
        return {"file": str(path), "error": str(e)}
    functions: dict[str, str] = {}
    classes: dict[str, str] = {}
    constants: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions[node.name] = hash_node(node)
        elif isinstance(node, ast.ClassDef):
            classes[node.name] = hash_node(node)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    constants[target.id] = hash_node(node)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id.isupper():
            constants[node.target.id] = hash_node(node)
    return {
        "file": str(path),
        "functions": functions,
        "classes": classes,
        "constants": constants,
    }


def compare_pair(pair: tuple[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
    a, b = pair

    def intersect_hashes(key: str) -> list[str]:
        if key not in a or key not in b:
            return []
        a_map = a[key]
        b_map = b[key]
        return sorted(name for name in a_map.keys() & b_map.keys() if a_map[name] == b_map[name])

    shared_funcs = intersect_hashes("functions")
    shared_classes = intersect_hashes("classes")
    shared_consts = intersect_hashes("constants")
    total_shared = len(shared_funcs) + len(shared_classes) + len(shared_consts)
    total_a = len(a.get("functions", {})) + len(a.get("classes", {})) + len(a.get("constants", {}))
    total_b = len(b.get("functions", {})) + len(b.get("classes", {})) + len(b.get("constants", {}))
    union_total = total_a + total_b - total_shared
    similarity = (total_shared / union_total) if union_total > 0 else 0.0
    return {
        "file_a": a["file"],
        "file_b": b["file"],
        "shared_functions": shared_funcs,
        "shared_classes": shared_classes,
        "shared_constants": shared_consts,
        "shared_count": total_shared,
        "similarity": round(similarity, 4),
    }


def main() -> None:
    current_dir = Path.cwd()
    py_files = sorted(current_dir.glob("*.py"))
    if len(py_files) < 2:
        print(
            json.dumps(
                {
                    "error": "Need at least 2 .py files in the current directory.",
                    "found": [str(f) for f in py_files],
                },
                indent=2,
            )
        )
        return
    with mp.Pool(processes=8) as pool:
        parse_results = [pool.apply_async(extract_definitions, (f,)) for f in py_files]
        parsed = [r.get() for r in parse_results]
        valid = [p for p in parsed if p and "error" not in p]
        errors = [p for p in parsed if p and "error" in p]
        pairs = [(valid[i], valid[j]) for i in range(len(valid)) for j in range(i + 1, len(valid))]
        compare_results = [pool.apply_async(compare_pair, (p,)) for p in pairs]
        comparisons = [r.get() for r in compare_results]
    comparisons.sort(key=lambda x: x["similarity"], reverse=True)
    report = {
        "scanned_directory": str(current_dir),
        "total_files": len(py_files),
        "parsed_files": len(valid),
        "parse_errors": errors,
        "total_comparisons": len(comparisons),
        "results": comparisons,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
