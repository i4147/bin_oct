#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory and all of its subdirectories for Python source files, analyzes each file to determine which external third-party packages it depends on, and produces a consolidated dependency list saved to a requirements file named "requirements.txt" in the current directory.
The tool should:
- Recursively discover every Python source file (files ending in the .py extension) under the directory where the script is run.
- Parse each file's source code structurally, rather than relying on text matching, so that all import statements are detected wherever they appear in the file, including inside functions, classes, and conditional blocks.
- Record only the top-level package name for each import (for example, reducing a dotted module path to its root package), and ignore relative imports that refer to modules within the project itself.
- Process files in parallel where practical to keep the scan fast on large projects.
- Silently skip files that cannot be read as UTF-8 text or that contain invalid Python syntax, so that a single malformed file never stops the overall scan.
- Merge the results from all files into a single set of unique package names, eliminating duplicates.
- Write the final package names to the requirements file, one per line, in a clean and readable order.
- Print a brief summary to the console indicating how many files were scanned and how many unique dependencies were found.
- Make no network requests and require no user input; it should run unattended from the command line and complete with a clear success message.
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
