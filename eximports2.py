#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a project directory recursively for Python source files and produces a summary of all the import statements they contain, organized by folder. The script should skip hidden directories, virtual environment or package directories (such as site-packages), and any previously generated output folder, so that only the project's own source files are analyzed.
For each qualifying file, the script should parse the source code using a proper syntax-aware parser rather than simple text matching, and extract only the top-level import statements (both plain imports and "from ... import ..." forms), preserving their exact original text. Files that cannot be read or parsed should be handled gracefully without stopping the overall run.
The results should be grouped by folder, with each folder's collected imports listed alongside the file they came from, and displayed or saved in a clear, human-readable report. Paths in the report should be shown relative to the project root where possible, falling back to the original path otherwise. The script should also track and report summary statistics such as the total number of files processed and the number of distinct folders discovered.
The output should be written to an output directory created automatically in the working location if it does not already exist, and the script should run as a standalone command-line tool with no required user input.
---"""

from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from tree_sitter import Language, Parser, Tree
import tree_sitter_python as tsp

parser = Parser()
parser.language = Language(tsp.language())
OUT_DIR = Path("output")
OUT_DIR.mkdir(exist_ok=True)
VALID = {"import_statement", "import_from_statement"}


def extract_file(src: bytes, tree: Tree) -> list[str]:
    root = tree.root_node
    return [src[node.start_byte : node.end_byte].decode() for node in root.children if node.type in VALID]


def get_relative_path(path: Path, base_path: Path) -> Path:
    try:
        return path.relative_to(base_path)
    except ValueError:
        return path


folder_imports = defaultdict(list)
processed_files_count = 0
folders_found = set()
for py in Path().rglob("*.py"):
    if any(part.startswith(".") for part in py.parts) or "site-packages" in py.parts:
        continue
    if OUT_DIR in py.parents:
        continue
    try:
        src = py.read_bytes()
        tree = parser.parse(src)
        imports = extract_file(src, tree)
        if imports:
            folder_path = py.parent
            relative_folder = get_relative_path(folder_path, Path())
            folders_found.add(str(relative_folder))
            file_header = f"# === {py.name} ===\n"
            folder_imports[relative_folder].append(file_header + "\n".join(imports))
            processed_files_count += 1
    except Exception as e:
        print(f"⚠️  Error processing {py}: {e}")
for folder, imports_list in folder_imports.items():
    if not imports_list:
        continue
    out_file = OUT_DIR / folder / "imports.py"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    content = "\n\n".join(imports_list)
    header = f"# Auto-generated imports file for folder: {folder}\n"
    out_file.write_text(header + content)
    print(f"✅ saved: {out_file} ({len(imports_list)} files)")
print(f"""
✨ Done! Processed {processed_files_count} files in {len(folder_imports)} folder(s)""")
print(f"📁 Folders: {', '.join(sorted(folders_found))}")
