#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python script (Termux-targeted, shebang `/data/data/com.termux/files/usr/bin/env python`) that recursively scans the current working directory for Python source files and extracts top-level class definitions from each file, grouping them by folder and writing one consolidated file per folder into an output directory.

**Purpose and behavior:**

- Use `from __future__ import annotations` at the top, and use `collections.defaultdict` and `pathlib.Path`.
- Parse Python source with tree-sitter: import `tree_sitter_python` as `tsp` and `Language`, `Parser`, `Tree` from `tree_sitter`. Create a module-level `Parser`, set its language to `Language(tsp.language())`.
- Define a module-level output directory `output` (as a `Path`), and create it with `mkdir(exist_ok=True)` at import time.
- Define a module-level set `VALID` containing only the node type `"class_definition"`.

**Core function `extract_file(src: bytes, tree: Tree) -> list[str]`:**

- Take the raw source bytes and the parsed tree.
- Iterate only over the direct children of the root node.
- For each child whose type is in `VALID`, slice the source bytes from `start_byte` to `end_byte`, decode as UTF-8 (default), and collect the strings in a list.
- Return that list. Only top-level classes are captured; nested classes and functions are ignored.

**Main workflow (runs at module level, no `main()` guard):**

1. Create `folder_imports` as a `defaultdict(list)`.
2. Recursively iterate over `Path().rglob("*.py")` (relative to the current working directory). Skip any file where:
   - any path part starts with `.` (hidden directories/files), or
   - `"site-packages"` appears in the path parts.
   - Also skip files where `OUT_DIR` is among the file's parent paths (so the output directory is not reprocessed). Note that this comparison is against the `Path` object directly.
3. For each remaining file: read bytes with `read_bytes()`, parse with the parser, and extract classes via `extract_file`.
4. If any classes were found, key the entry by the file's parent folder, computed as `py.parent.relative_to(".")`, and append the classes joined by newlines as one string to that folder's list.
5. After scanning, iterate over `folder_imports.items()`. Skip empty lists (defensive). For each folder:
   - Build the output path `OUT_DIR / folder / "imports.py"`.
   - Create parent directories with `parents=True, exist_ok=True`.
   - Join all per-file strings for that folder with two newlines (`"\\n\\n"`), and write with `write_text` (default encoding).
6. Finally, print a completion message in this exact multi-line form: a leading newline, then a sparkle emoji and `Done!`, followed by the count of processed folders, e.g. `✨ Done! Processed N folder(s)`. The print should use an f-string whose opening quotes are triple quotes, with the line break between `print(f\"\"\"` and the message content.

**Edge cases and notes:**

- Files that fail to parse or have no top-level classes produce no output; tree-sitter is tolerant, so no explicit exception handling is performed.
- The root folder (`.`) yields a relative folder of `.`, so its output goes to `output/imports.py`.
- Files are not deduplicated; identical class definitions across files are all written.
- No command-line arguments are accepted; behavior depends entirely on the current working directory.
- Dependencies: `tree-sitter` and `tree-sitter-python` packages.
- Run from the project root with the Python interpreter; the script is intended for execution in a Termux environment.
- Do not include explanations or extra output beyond what is described above.
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
