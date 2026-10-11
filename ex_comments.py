#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python script that recursively scans the current working directory for Python source files and collects the top-level comment and expression-statement nodes from each file, using tree-sitter for parsing. Results are grouped by folder and written to an output directory.

**Purpose and behavior**

- Starting from the current directory, recursively find every `*.py` file.
- Skip any file where any path component begins with a dot (hidden directories or files), any file whose path contains a `site-packages` component, and any file already located under the output directory `output`.
- For each remaining file, read its bytes and parse them with the tree-sitter Python grammar. Only direct children of the module root node are considered, and only those whose node type is either `comment` or `expression_statements` (note the exact spelling of the second type, with the trailing "s"). Extract each matching node's exact source text by slicing the original bytes between its start and end byte offsets and decoding as UTF-8.
- Group the extracted text blocks by the file's parent folder, relative to the current directory. Within each file, join its extracted snippets with a single newline. Store one such joined block per file in a per-folder list.
- Ensure the output directory `output` exists at startup (create it, tolerating if it already exists).
- For each folder that has at least one collected block, create `output/<folder>/imports.py` (creating parent directories as needed, tolerating existing ones). Its content is all of that folder's blocks joined with two newlines between them. Write it as text, overwriting any existing file. For the current directory itself, the folder path is the output directory root, i.e. `output/imports.py`.
- Skip folders with no collected content (no file in them yielded any matching nodes).
- When finished, print a single message in the form of a celebratory line with a sparkle emoji, followed by "Done!" and the count of folders processed, for example: "✨ Done! Processed N folder(s)". The message should be printed as a multi-line f-string where the newline comes before the text.

**Dependencies**

- Python 3 with `from __future__ import annotations` for type hints.
- Standard library: `collections.defaultdict`, `pathlib.Path`.
- Third-party: `tree_sitter` (providing `Language`, `Parser`, `Tree`) and `tree_sitter_python` (providing a `language()` function that returns the grammar).

**Setup at module level**

- Create one tree-sitter `Parser`, and set its language to the Python grammar obtained by wrapping the result of the grammar package's `language()` call in `Language`.
- Define the output directory constant as a relative path named `output`.
- Define the set of valid node types as the two strings above.

**Edge cases and notes**

- Files that are unreadable or unparsable are not explicitly handled; errors from reading or parsing propagate.
- Decoding uses the default UTF-8 with strict error handling; invalid byte sequences raise an error.
- Writing uses the default text encoding of the platform.
- The script targets a Termux environment on Android; the shebang line references its Python path, so keep it as the first line.
- The count in the final message is the number of folder keys in the grouping dictionary, which includes every folder where at least one matching file was found, even if it yields no written output.
- Because the output directory is excluded from scanning, re-running the script does not reprocess previously generated files.

**Execution**

Run the script from the project root directory with Python 3. Output files are written beneath `output/` mirroring the source folder structure, each containing an `imports.py` file.
---"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import tree_sitter_python as tsp
from tree_sitter import Language, Parser, Tree

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
