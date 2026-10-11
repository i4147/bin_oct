#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python script that scans the current working directory for Python source files and generates a requirements-style list of the top-level third-party module names they import. Use these details:

**Purpose:** Produce a `requirements.txt` listing the unique top-level module names imported across all `.py` files in the current directory tree, so a user can see what packages a project depends on.

**Dependencies and helpers:** The script must import three helpers from a local module named `dh`: `get_files` (recursively collects files from a directory filtered by extension list), `mpf` (a parallel map that applies a function to a list of items and returns the results), and `unique_path` (given a path, returns a non-colliding variant of it, e.g., by appending a numeric suffix). Use the standard library `ast` and `pathlib`. Include the `from __future__ import annotations` line and a Termux-style shebang (`#!/data/data/com.termux/files/usr/bin/env python`).

**Per-file processing (`process_file(path)`):**
- Open the file with UTF-8 encoding, read its full contents, and parse it with `ast.parse`, passing the filename for error reporting.
- Walk every node in the syntax tree.
- For `import x.y.z` statements, add the first dotted segment (`x`) for each alias.
- For `from x.y import ...` statements, add the first segment of the module name, but only when `level == 0` (skip relative imports) and the module is not empty/None.
- Return a set of collected names.
- If the file has a `SyntaxError` or `UnicodeDecodeError`, silently ignore it and return whatever (empty) set was collected. Do not crash or log.
- Note that the standard library modules are not filtered out; every top-level name is included as-is.

**Main execution (under `if __name__ == "__main__":`):**
1. Set the working directory to `Path.cwd()`.
2. Call `get_files` on that directory with extension filter `[".py"]`.
3. Run `process_file` over all files via `mpf` (parallel mapping), producing a list of sets.
4. Merge all sets into one set of unique module names, skipping empty results.
5. Set the output path to `requirements.txt` in the current directory. If that file already exists, replace the path with `unique_path(...)` so the existing file is not overwritten.
6. Write each unique module name on its own line, in set iteration order (unsorted), using plain `open(..., "w")` with default encoding.
7. Print a message in the form `<filename> created.` using only the file's name (not its full path), e.g. `requirements.txt created.` or the suffixed variant.

**Behavioral notes and edge cases:**
- The output is not sorted and not deduplicated against standard library names or version pins; it contains bare module names only.
- Relative imports (`from . import x`) are ignored; `import` statements inside functions and conditionals are included since `ast.walk` visits the whole tree.
- Files that fail to parse produce no entries and no warnings.
- If no imports are found, an empty `requirements.txt` is still created.
- Script is intended to run as a standalone command from the project root; no command-line arguments are accepted.
- Keep the code concise and idiomatic, with minimal comments matching a small utility script's style.
---"""

from __future__ import annotations

import ast
from pathlib import Path

from dh import get_files, mpf, unique_path


def process_file(path):
    Path(path)
    imports = set()
    try:
        with Path(path).open(encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(n.name.split(".")[0] for n in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imports.add(node.module.split(".")[0])
    except (SyntaxError, UnicodeDecodeError):
        pass
    return imports


if __name__ == "__main__":
    cwd = Path.cwd()
    files = get_files(cwd, ext=[".py"])
    results = mpf(process_file, files)
    uniq_imports = set()
    for k in results:
        if k:
            for x in k:
                if x not in uniq_imports:
                    uniq_imports.add(x)
    output_path = Path("requirements.txt")
    if output_path.exists():
        output_path = unique_path(output_path)
    with open(output_path, "w") as f:
        for k in uniq_imports:
            f.write(f"{k}\n")
    print(f"{output_path.name} created.")
