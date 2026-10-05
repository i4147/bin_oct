#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that converts a Jupyter notebook file into a Markdown file.
The script should accept the notebook file path as the first command-line argument, read it using nbformat, and iterate through its cells in order.
Markdown cells should be written directly as plain text, while code cells should be wrapped in triple-backtick Python code fences.
The output should be saved to a new file with the same name as the input but with a ".md" extension, and the script should print a confirmation message showing the export destination once complete."""

from __future__ import annotations
import sys
from pathlib import Path
import nbformat

if __name__ == "__main__":
    fn = Path(sys.argv[1])
    with Path(fn).open(encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)
    fo = fn.with_suffix(".md")
    with Path(fo).open("w", encoding="utf-8") as out:
        for _i, cell in enumerate(nb.cells, 1):
            out.write("\n")
            if cell.cell_type == "markdown":
                out.write(cell.source + "\n\n")
            elif cell.cell_type == "code":
                out.write("```python\n")
                out.write(cell.source + "\n")
                out.write("```\n\n")
    print(f"Exported → {fo}")
