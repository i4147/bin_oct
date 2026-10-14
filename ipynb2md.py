#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts a Jupyter notebook file into a Markdown document. The script should take the path to a notebook file as a command-line argument and produce a Markdown file with the same base name and location, replacing the notebook extension with a Markdown extension. It should read the notebook in a standard, UTF-8 encoded way, then walk through every cell in order. Markdown cells should be written as-is, preserving their text and adding spacing between blocks. Code cells should be wrapped in fenced code blocks tagged for Python syntax highlighting, with clear separation between cells. Raw or other non-markdown, non-code cell types can be skipped. Upon completion, the script should print a short confirmation message showing the path of the generated Markdown file. Keep the tool simple, dependable, and focused solely on this notebook-to-Markdown conversion.
---"""

from __future__ import annotations
from pathlib import Path
import sys
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
