#!/data/data/com.termux/files/usr/bin/env python
"""Write a single self-contained prompt that instructs an AI coding agent to build a Python script which recursively scans the current directory for Python files and collects their top-level import statements, grouped by folder, and writes the results to an output directory. The prompt must describe the purpose, inputs, outputs, dependencies, logic, error handling, edge cases, and execution details, without including code or code snippets.

Create a Python script (intended to run under Termux on Android, so use a Termux-style shebang pointing to the Termux Python interpreter) that performs the following:

**Purpose:** Scan the current working directory recursively for `.py` files and collect every top-level import statement from each file, grouped by the folder containing the file. Write the grouped results to files in an output directory.

**Dependencies:**
- The `tree_sitter` package (version 0.22 or later API, where `Parser` accepts a language assigned via a `language` attribute and `Language` is constructed from a language object).
- The `tree_sitter_python` package, which provides a language object via its `language()` function.
- Standard library: `from __future__ import annotations`, `collections.defaultdict`, and `pathlib.Path`.

**Setup:**
- Create a module-level `Parser`, set its language to the Python grammar obtained by wrapping `tree_sitter_python.language()` in a `Language` object.
- Define the output directory as a relative `Path` named `output`, and create it at startup if it does not exist (no error if it already exists).
- Define the set of node types to extract as exactly `import_statement` and `import_from_statement`.

**Core logic:**
1. Define a function that takes the raw file bytes and the parsed tree, iterates only over the direct children of the tree's root node, keeps children whose type is one of the valid import types, and returns each one's exact source text (sliced by start and end byte offsets, decoded as UTF-8). Imports nested inside functions, classes, or conditionals are therefore excluded; only module-level imports are captured. Multi-line imports are captured as a single string including their internal newlines.
2. Define a helper that returns a path relative to a base path, falling back to the original path if the relative computation raises `ValueError`.
3. Initialize a `defaultdict(list)` mapping folder paths to lists of strings, a processed-files counter (starting at 0), and a set of found folder names (as strings).
4. Iterate over `Path().rglob("*.py")` (relative to the current directory). For each file:
   - Skip it if any component of its path parts starts with a dot (hidden files or directories), or if the path contains the component `site-packages`.
   - Skip it if the output directory is among its parent directories (so the script never re-reads its own outputs).
   - Inside a try block: read the file as bytes, parse it with the module parser, extract the import strings.
   - If the file has any imports: compute its parent folder, compute that folder relative to the current directory, add the folder's string form to the found-folders set, build a header line of the form `# === <filename> ===` followed by a newline, and append to the folder's list the header concatenated with the file's import lines joined by newlines (the text of the header and the joined imports form one entry per file).
   - Files with no imports produce no entry.
   - Increment the processed-files counter for each file successfully processed (including those with no imports, as the counter tracks successfully parsed files).
5. Errors while processing an individual file (for example unreadable files, decoding problems, or parse failures) must be caught per file so the scan continues with the next file; the error should be reported in a way that does not halt the run (for example, a warning printed to standard error including the file path).

**Output:**
- After scanning, for each folder key in the collected mapping, write a text file into the output directory. The file name should be derived from the folder path (for the root folder, a sensible name such as `root` or `_root`; for nested folders, replace path separators with underscores or similar to produce a flat, filesystem-safe name), with a `.txt` extension. Each file contains all per-file entries for that folder, separated by blank lines, with the header line preceding each file's imports.
- Print a summary to standard output showing the number of files processed, the number of folders with imports found, and the output directory location.

**Edge cases to handle:**
- Empty directories or directories with no Python files: produce no output files, and the summary should show zero counts.
- Files that exist only as broken symlinks or unreadable files: skip with a warning.
- Files with syntax errors: tree-sitter is error-tolerant, so parse normally; imports inside error nodes may be missed, which is acceptable.
- Duplicate folder names at different depths: the flattened file name must not collide; use the full relative path to generate names.
- Running the script multiple times: the output directory may already exist; existing files should be overwritten.

**Execution and usage:**
- Run the script from the root of the project to be analyzed; it scans relative to the current working directory.
- Make the script executable with the Termux Python shebang.
- Use UTF-8 for all text reads and writes.
- No command-line arguments are required or accepted.
- Use only the standard library plus the two tree-sitter packages; do not add other dependencies.
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
