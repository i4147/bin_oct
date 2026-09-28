#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that recursively scans the current directory for all .py files (skipping hidden directories, "site-packages", and its own "output" folder), uses tree-sitter with the tree_sitter_python grammar to parse each file and extract the top-level function definitions as source code snippets.
For each folder containing such definitions, it concatenates the extracted function texts and writes them into a mirrored subfolder under an "output" directory as an "imports.py" file, preserving the original relative folder structure.
At the end, it prints a summary message reporting how many folders were processed."""

from collections import defaultdict
from pathlib import Path
import tree_sitter_python as tsp
from tree_sitter import Language, Parser, Tree

parser = Parser()
parser.language = Language(tsp.language())
OUT_DIR = Path("output")
OUT_DIR.mkdir(exist_ok=True)
VALID = {"function_definition"}


def extract_file(src: bytes, tree: Tree) -> list[str]:
    root = tree.root_node
    return [
        src[node.start_byte : node.end_byte].decode()
        for node in root.children
        if node.type in VALID
    ]


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
