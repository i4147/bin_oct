#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that merges all Python source files in the current working directory into a single consolidated Python file. The merged file should be named after the directory it is run from (for example, a folder named "myproject" produces "myproject.py" in that same folder). The script should discover every ".py" file in the directory, excluding the output file itself if them in a consistent, alphabetical order so that repeated runs produce the same result.
For each source file, read its contents using UTF-8 encoding and append them sequentially to the output file. Before writing, rewrite any relative package-style imports found in the source text so they reference the directory's name as the package name instead. Specifically, handle three forms: "from . import module", "from .module import name", and "import ." patterns, converting them to absolute imports that use the folder name. All other code should be preserved exactly as written.
Errors such as unreadable files or permission problems should be handled gracefully, with clear messages to the user rather than unhandled crashes. When finished, the script should print a short summary stating how many files were merged and the name of the output file.
---"""

from __future__ import annotations
import os
from pathlib import Path
import re


def resolve_imports(content: str, cwd: Path) -> str:
    folder_name = Path(cwd).name
    content = re.sub(r"from \. import ([a-zA-Z0-9_]+)", f"from {folder_name} import \\1", content)
    content = re.sub(
        r"from \.([a-zA-Z0-9_]+) import ([a-zA-Z0-9_]+)",
        f"from {folder_name}.\\1 import \\2",
        content,
    )
    return re.sub(r"import \.", f"import {folder_name}", content)


def merge_python_files() -> None:
    cwd = Path.cwd()
    folder_name = Path(cwd).name
    output_filename = f"{folder_name}.py"
    py_files = [f for f in os.listdir(cwd) if f.endswith(".py") and f != output_filename]
    py_files.sort()
    with Path(output_filename).open("w", encoding="utf-8") as outfile:
        for py_file in py_files:
            with Path(py_file).open(encoding="utf-8") as infile:
                content = infile.read()
                content = resolve_imports(content, cwd)
                outfile.write(content)
    print(f"Merged {len(py_files)} files into {output_filename}")


if __name__ == "__main__":
    merge_python_files()
