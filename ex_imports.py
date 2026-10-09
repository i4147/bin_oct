#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that scans all .py files under the current working directory (using a helper get_files function) and, using tree-sitter with the tree_sitter_python grammar, parses each file to extract its top-level import_statement and import_from_statement nodes as source text.
It should process files in parallel via an mpf helper, aggregate the unique import lines across all files while excluding relative imports starting with "from .", sort them alphabetically, and write the result to a file named "{current_dir_name}_importz.py" inside ~/tmp/output, using a unique_path helper to avoid overwriting an existing output file.
Finally, it should print "done." after writing the file."""

from __future__ import annotations
from pathlib import Path
import sys

from dh import get_files, mpf, unique_path
from tree_sitter import Language, Parser
import tree_sitter_python as tsp


OUTPUT_DIR = Path.home() / "tmp" / "output"
parser = Parser()
parser.language = Language(tsp.language())
VALID = {"import_statement", "import_from_statement"}


def process_file(path):
    path = Path(path)
    src = path.read_bytes()
    tree = parser.parse(src)
    root = tree.root_node
    return [src[node.start_byte : node.end_byte].decode() for node in root.children if node.type in VALID]


def main() -> None:
    cwd = Path.cwd()
    outfile = OUTPUT_DIR / f"{cwd.name}_importz.py"
    if outfile.exists():
        outfile = unique_path(outfile)
    all_imports = []
    files = get_files(cwd, ext=[".py"])
    results = mpf(process_file, files)
    for imports in results:
        if imports:
            for k in imports:
                if not k.startswith("from .") and k not in all_imports:
                    all_imports.append(k)
    all_imports = sorted(set(all_imports))
    outfile.write_text("\n".join(all_imports), encoding="utf-8")
    print("done.")


if __name__ == "__main__":
    raise SystemExit(main())
