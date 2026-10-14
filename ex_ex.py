#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a project directory tree recursively for Python source files and extracts the documentation strings of top-level functions and classes from each file, then produces an organized summary of these docstrings grouped by folder. The script should skip hidden directories, virtual environment or package folders (such as site-packages), and any previously generated output directory so that its own results are never re-processed. It should parse each Python file using a robust syntax-aware approach rather than simple text matching, so that only genuine top-level function and class docstrings are captured.
The script should create an output directory if it does not already exist and write the collected docstrings to files there, with one output per source folder that contains at least one documented file. Each output should clearly preserve the association between a folder and the docstrings found in its files, separating entries from different files so the result is easy to read. Folders without any extracted docstrings should be omitted from the results.
Key behaviors to include:
- Traverse the entire project tree starting from the current working directory.
- Read each file as raw bytes so encoding can be handled correctly during decoding.
- Ignore files that cannot be parsed or decoded gracefully without crashing the whole run, and report such issues in a concise way.
- Preserve the original text of each docstring exactly as it appears in the source.
- Produce a final summary indicating how many folders and docstrings were processed.
The script should be self-contained, runnable from the command line with no required arguments, and robust enough to handle large projects with many nested folders.
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
VALID = {"function_docstrings", "class_docstrings"}


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
