#!/data/data/com.termux/files/usr/bin/env python
"""Generate a ``repeated.json`` manifest of duplicated top-level functions, classes, and constant assignments across every ``.py`` file under the current directory, then use that manifest to refactor each affected file: strip the named definitions and inject a single ``from dh import ...`` line so the shared versions come from ``dh`` instead.
Analysis and refactoring both run on a fixed multiprocessing.Pool of 8 workers; logging via loguru."""

from __future__ import annotations
import ast
import collections
import json
from multiprocessing import Pool
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast
import astor  # type: ignore[import-untyped]
from loguru import logger

if TYPE_CHECKING:
    from multiprocessing.pool import AsyncResult
REPEATED_JSON_PATH: Final[Path] = Path("repeated.json")
MAX_WORKERS: Final[int] = 8
DUPLICATE_THRESHOLD: Final[int] = 2
DefinitionKey = tuple[str, str, str]
DefinitionsMap = collections.defaultdict[DefinitionKey, list[str]]
SourceMap = dict[DefinitionKey, str | None]
FileMap = dict[str, list[str]]
Task = tuple[Path, list[str]]


def get_source(node: ast.AST, content: str) -> str | None:
    return ast.get_source_segment(content, node)


def normalize_source(source: str | None) -> str:
    if not source:
        return ""
    return "\n".join(line.rstrip() for line in source.strip().splitlines())


def _iter_target_py_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if ".git" in path.parts:
            continue
        files.append(path)
    return files


def _collect_definitions(
    file_path: Path,
    definitions: DefinitionsMap,
    source_map: SourceMap,
) -> None:
    try:
        content: str = file_path.read_text(encoding="utf-8")
        tree: ast.Module = ast.parse(content)
    except Exception:
        return
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            source: str | None = get_source(node, content)
            norm: str = normalize_source(source)
            key: DefinitionKey = (type(node).__name__, node.name, norm)
            definitions[key].append(str(file_path))
            if key not in source_map:
                source_map[key] = source
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    source = get_source(node, content)
                    norm = normalize_source(source)
                    key = ("Constant", target.id, norm)
                    definitions[key].append(str(file_path))
                    if key not in source_map:
                        source_map[key] = source


def analyze_files() -> list[dict[str, Any]]:
    cwd: Path = Path.cwd()
    definitions: DefinitionsMap = collections.defaultdict(list)
    source_map: SourceMap = {}
    for py_file in _iter_target_py_files(cwd):
        _collect_definitions(py_file, definitions, source_map)
    repeated: list[dict[str, Any]] = []
    for key, paths in definitions.items():
        unique_paths: list[str] = list(set(paths))
        if len(unique_paths) > DUPLICATE_THRESHOLD:
            repeated.append({
                "type": key[0],
                "name": key[1],
                "source": source_map[key],
                "count": len(unique_paths),
                "files": unique_paths,
            })
    return repeated


def write_repeated_json(repeated: list[dict[str, Any]]) -> None:
    repeated.sort(key=lambda item: item["count"], reverse=True)
    REPEATED_JSON_PATH.write_text(json.dumps(repeated, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(repeated)} entries to {REPEATED_JSON_PATH}")


def load_refactoring_maps() -> FileMap:
    with REPEATED_JSON_PATH.open("r", encoding="utf-8") as f:
        data: list[dict[str, Any]] = json.load(f)
    file_to_objects: collections.defaultdict[str, list[str]] = collections.defaultdict(list)
    for item in data:
        obj_name: str = item["name"]
        for file_path_str in item["files"]:
            p: Path = Path(file_path_str)
            file_to_objects[p.name].append(obj_name)
    return dict(file_to_objects)


class ASTStripper(ast.NodeTransformer):
    def __init__(self, target_names: list[str]) -> None:
        super().__init__()
        self.target_names: set[str] = set(target_names)
        self.removed_something: bool = False

    def visit_FunctionDef(  # type: ignore[override]
        self, node: ast.FunctionDef
    ) -> ast.FunctionDef | None:
        if node.name in self.target_names:
            self.removed_something = True
            return None
        return cast("ast.FunctionDef", self.generic_visit(node))

    def visit_AsyncFunctionDef(  # type: ignore[override]
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef | None:
        if node.name in self.target_names:
            self.removed_something = True
            return None
        return cast("ast.AsyncFunctionDef", self.generic_visit(node))

    def visit_ClassDef(  # type: ignore[override]
        self, node: ast.ClassDef
    ) -> ast.ClassDef | None:
        if node.name in self.target_names:
            self.removed_something = True
            return None
        return cast("ast.ClassDef", self.generic_visit(node))

    def visit_Assign(  # type: ignore[override]
        self, node: ast.Assign
    ) -> ast.Assign | None:
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in self.target_names:
                self.removed_something = True
                return None
        return cast("ast.Assign", self.generic_visit(node))


def refactor_single_file(file_path: Path, objects_to_remove: list[str]) -> bool:
    try:
        source_code: str = file_path.read_text(encoding="utf-8")
        tree: ast.Module = ast.parse(source_code)
    except Exception as exc:
        logger.error(f"❌ Error parsing {file_path.name}: {exc}")
        return False
    stripper: ASTStripper = ASTStripper(objects_to_remove)
    modified_tree: ast.AST = stripper.visit(tree)
    ast.fix_missing_locations(modified_tree)
    if not stripper.removed_something:
        print(f"➖ No matching structural nodes found inside {file_path.name}")
        return False
    import_names: str = ", ".join(sorted(objects_to_remove))
    import_statement: str = f"from dh import {import_names}\n"
    try:
        cleaned_source: str = astor.to_source(modified_tree)
    except Exception as exc:
        logger.error(f"❌ Failed to stringify AST for {file_path.name}: {exc}")
        return False
    lines: list[str] = cleaned_source.splitlines(keepends=True)
    insert_idx: int = 0
    if lines and lines[0].startswith("#!"):
        insert_idx = 1
    if len(lines) > insert_idx and (
        lines[insert_idx].strip().startswith('"""') or lines[insert_idx].strip().startswith("'''")
    ):
        insert_idx += 1
    lines.insert(insert_idx, import_statement)
    try:
        file_path.write_text("".join(lines), encoding="utf-8")
        print(f"✅ Refactored {file_path.name}: Stripped {objects_to_remove} -> added 'dh' import")
        return True
    except Exception as exc:
        logger.error(f"❌ Error writing updates back to {file_path.name}: {exc}")
        return False


def main() -> None:
    print("🔎 Analyzing Python files for duplicated definitions...")
    repeated: list[dict[str, Any]] = analyze_files()
    if not repeated:
        logger.warning(f"No definitions duplicated in more than {DUPLICATE_THRESHOLD} files. Nothing to refactor.")
        return
    write_repeated_json(repeated)
    refactor_map: FileMap = load_refactoring_maps()
    current_dir: Path = Path()
    local_files: dict[str, Path] = {f.name: f for f in current_dir.glob("*.py")}
    tasks: list[Task] = [
        (local_files[filename], objects) for filename, objects in refactor_map.items() if filename in local_files
    ]
    if not tasks:
        print("No matching files found in the current directory to refactor.")
        return
    print(f"🚀 Found {len(tasks)} files to clean structural code from. Starting parallel processing...")
    with Pool(processes=MAX_WORKERS) as pool:
        async_results: list[AsyncResult[bool]] = [
            pool.apply_async(refactor_single_file, (file_path, objects)) for file_path, objects in tasks
        ]
        for async_res in async_results:
            try:
                async_res.get()
            except Exception as exc:
                logger.error(f"❌ Worker raised: {exc}")
    print("🎉 Structural refactoring complete! All duplicate bodies stripped.")


if __name__ == "__main__":
    raise SystemExit(main())
