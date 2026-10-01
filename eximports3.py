#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that scans all .py files in the current working directory (using a helper get_files function) and, for each file, parses its AST to extract the top-level names of imported modules from both "import" and "from ...
import" statements, skipping files that fail to parse due to syntax or encoding errors.
It should process the files in parallel using a helper mpf function, aggregate all unique module names across the codebase, and write them one per line into a requirements.txt file, using a helper unique_path function to avoid overwriting an existing file with that name.
Finally, it should print a confirmation message showing the name of the created output file."""

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
