#!/data/data/com.termux/files/home/.local/bin/python
"""
Check Python files in current directory and report definitions
that are not exported in __init__.py
"""

import ast
from pathlib import Path
from typing import Dict

from loguru import logger


def extract_definitions(path: Path) -> dict[str, list[str]]:
    definitions = {"functions": [], "classes": [], "constants": []}

    try:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as e:
        logger.error(f"Failed to parse {path}: {e}")
        return definitions
    except Exception as e:
        logger.error(f"Unexpected error reading {path}: {e}")
        return definitions

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                definitions["functions"].append(node.name)

        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                definitions["classes"].append(node.name)

        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    if name.isupper() and not name.startswith("_"):
                        definitions["constants"].append(name)

        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            if name.isupper() and not name.startswith("_"):
                definitions["constants"].append(name)

    return definitions


def extract_exports_from_init(init_path: Path) -> set[str]:
    exported = set()

    try:
        with open(init_path, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=str(init_path))
    except (SyntaxError, UnicodeDecodeError) as e:
        logger.error(f"Failed to parse {init_path}: {e}")
        return exported
    except Exception as e:
        logger.error(f"Unexpected error reading {init_path}: {e}")
        return exported

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(
                                elt.value, str
                            ):
                                exported.add(elt.value)

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    logger.warning(f"Wildcard import found in {init_path}")
                    continue

                exported.add(alias.asname or alias.name)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                exported.add(name)

    return exported


def check_directory(directory: Path | None = None) -> dict[str, dict[str, list[str]]]:
    if directory is None:
        directory = Path.cwd()

    init_path = directory / "__init__.py"

    if not init_path.exists():
        logger.error(f"No __init__.py found in {directory}")
        return {}

    print(f"Reading exports from {init_path}")
    exported = extract_exports_from_init(init_path)
    logger.debug(f"Found {len(exported)} exported names: {sorted(exported)}")

    missing = {}

    python_files = [
        f
        for f in directory.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    ]

    if not python_files:
        logger.warning(f"No Python module files found in {directory}")
        return {}

    for py_file in sorted(python_files):
        logger.debug(f"Scanning {py_file.name}")
        definitions = extract_definitions(py_file)

        module_name = py_file.stem
        file_missing = {"functions": [], "classes": [], "constants": []}

        for category, names in definitions.items():
            for name in names:
                if name not in exported and module_name not in exported:
                    file_missing[category].append(name)

        if any(file_missing.values()):
            missing[py_file.name] = file_missing

    return missing


def main():
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    directory = Path.cwd()
    print(f"Checking package definitions in: {directory}")

    missing = check_directory(directory)

    if not missing:
        logger.success("All definitions are exported in __init__.py")
        return 0

    print()
    print("=" * 70)
    print("DEFINITIONS NOT EXPORTED IN __init__.py")
    print("=" * 70)

    total = 0
    for filename, categories in missing.items():
        print(f"\n📄 {filename}")
        for category, names in categories.items():
            if names:
                total += len(names)
                icon = {"functions": "🔧", "classes": "🏛️ ", "constants": "📌"}[category]
                print(f"  {icon} {category.capitalize()}:")
                for name in sorted(names):
                    print(f"      - {name}")

    print()
    print("=" * 70)
    logger.warning(f"Total missing definitions: {total}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
