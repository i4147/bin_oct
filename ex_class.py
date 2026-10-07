#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that recursively scans all .py files under the current directory (skipping hidden directories, site-packages, and its own output folder) and uses tree-sitter with the tree_sitter_python grammar to parse each file and extract top-level class_definition nodes as source text.
For each folder containing files with extracted class definitions, concatenate the extracted code from all files in that folder and write it into a corresponding "imports.py" file under an "output" directory, preserving the relative folder structure.
Finally, print a summary message showing how many folders were processed."""

from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import tree_sitter_python as tsp
from tree_sitter import Language, Parser, Tree

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
