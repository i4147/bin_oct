#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that converts a plain .py source file into a Jupyter notebook (.ipynb) using nbformat, placing the entire file's contents into a single code cell.
It should accept the input .py path as the first command-line argument and an optional output .ipynb path as the second argument, defaulting the output name to the input file's stem with a .ipynb extension if not provided.
The script should read the source file as UTF-8 text, build a new notebook object, write it out as indented JSON, and print a confirmation message showing the input and output filenames.
If no input file argument is given, it should print a usage message and exit with a non-zero status."""

from __future__ import annotations
import json
import sys
from pathlib import Path
import nbformat as nbf


def simple_convert(py_file: str, ipynb_file: str | None = None) -> None:
    if not ipynb_file:
        ipynb_file = Path(py_file).stem + ".ipynb"
    code = Path(py_file).read_text(encoding="utf-8")
    nb = nbf.v4.new_notebook()
    nb["cells"] = [nbf.v4.new_code_cell(code)]
    with Path(ipynb_file).open("w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    print(f"Converted {py_file} to {ipynb_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_convert.py input.py [output.ipynb]")
        sys.exit(1)
    py_file = sys.argv[1]
    ipynb_file = sys.argv[2] if len(sys.argv) > 2 else None
    simple_convert(py_file, ipynb_file)
