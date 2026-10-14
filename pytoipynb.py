#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts a plain Python source file into a Jupyter notebook file. The tool should accept the path of an input Python file as a required command-line argument and an optional path for the output notebook. If no output path is given, the notebook should be named after the input file's base name with a notebook extension and saved in the current working directory. The entire contents of the Python file should be placed into a single code cell of a valid, standard-format notebook, so that opening it in Jupyter shows the original code unchanged. The output should be written with UTF-8 encoding and a readable, indented layout. After a successful conversion, the script should print a short confirmation message naming both the source and destination files. If the user runs the script without providing an input file, it should print a brief usage message explaining the expected arguments and exit with a non-zero status code.
---"""

from __future__ import annotations
import json
from pathlib import Path
import sys
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
