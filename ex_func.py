#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current project directory recursively for Python source files and extracts all top-level function definitions from each file, while skipping hidden directories, virtual environment or package folders (such as site-packages), and any previously generated output directory. The script should parse each source file using an accurate syntax-aware parser so that only complete top-level function definitions are captured, not classes, imports, or nested code. Group the extracted function definitions by the folder in which their source files reside, preserving the relative folder path as the grouping key, and join the functions found in each file into a single text block. Once all files are processed, the script should write the grouped results to an output location, creating the output directory if it does not already exist, with one output file per folder (or a clearly organized equivalent) containing the collected function code so that a developer can review all top-level functions of each folder at a glance. The script should handle files that cannot be read or parsed gracefully, continue processing remaining files, and report a concise summary of how many folders and functions were processed. Keep the implementation clean, robust, and cross-platform, and make reasonable choices about output formatting, naming, and error reporting.
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
VALID = {"function_definition"}


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
