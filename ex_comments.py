#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current project directory recursively for Python source files and extracts the top-level comments and standalone expression statements (such as docstring-like string literals) from each file, using a syntax-aware parser rather than plain text matching. The script should skip hidden directories, virtual environment or package-install directories, and any output directory it creates itself, so that only the user's own source code is considered.
The tool should group the extracted snippets by the folder that contains each file, preserving the order in which they appear within each file, and then combine them into a consolidated per-folder summary. The results should be written to an output directory that the script creates if it does not already exist, with one clearly named output file per folder that contains relevant content. Folders with no extractable content should produce no output.
Key behaviors to cover:
- Discover all eligible Python files across nested subdirectories, handling relative paths cleanly so the output reflects the project's structure.
- Parse each file robustly, reading raw bytes so that encoding and byte offsets are handled correctly, and decode only the extracted segments.
- Only retain the relevant top-level constructs (comments and standalone expression statements), ignoring all other code.
- Join multiple snippets from the same file and across files in a folder with clear separators so the output remains readable.
- Handle files that fail to parse or cannot be decoded gracefully, reporting a warning and continuing with the remaining files rather than aborting.
- Print a concise summary at the end indicating how many files were scanned, how many folders produced output, and where the results were saved.
The script should be self-contained, run from the command line without arguments, and be designed for clarity and maintainability.
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
VALID = {"comment", "expression_statements"}


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
