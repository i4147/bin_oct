#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans the current working directory for Python source files, skipping hidden directories, any path containing a "site-packages" segment, and an existing output directory. For each file, it should parse the source with a concrete syntax tree parser and extract the full text of all top-level class definitions. Group the extracted class definitions by the folder that contains each file, preserving the relative folder path. The script should create an output directory if it does not already exist, and be designed so that results can be written out per folder (for example, one consolidated text or Python file per folder containing its collected class definitions). Ensure that folders with no class definitions produce no output, that the original source files are never modified, and that files which cannot be read or parsed are handled gracefully without stopping the whole run. Keep the tool self-contained, deterministic in its output ordering, and clear in its console reporting of how many files and classes were processed and where results were saved.
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
VALID = {"class_definition"}


def extract_file(src: bytes, tree: Tree) -> list[str]:
    root = tree.root_node
    return [src[node.start_byte : node.end_byte].decode() for node in root.children if node.type in VALID]


folder_imports = defaultdict(list)
for py in Path().rglob("*.py"):
    if any(part.startswith(".") for part in py.parts) or "site-packages" in py.parts:
        continue
    if OUT_DIR in py.parents:
        continue
    src = py.read_bytes()
    tree = parser.parse(src)
    imports = extract_file(src, tree)
    if imports:
        folder_path = py.parent
        relative_folder = folder_path.relative_to(".")
        folder_imports[relative_folder].append("\n".join(imports))
for folder, imports_list in folder_imports.items():
    if not imports_list:
        continue
    out_file = OUT_DIR / folder / "imports.py"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    content = "\n\n".join(imports_list)
    out_file.write_text(content)
print(f"""
✨ Done! Processed {len(folder_imports)} folder(s)""")
