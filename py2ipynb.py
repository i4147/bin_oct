#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python command-line script that converts a plain .py source file into a Jupyter .ipynb notebook using nbformat.
It should read the input file's text, split it into logical code cells by heuristically detecting boundaries such as function/class definitions, grouped import blocks, and blank lines followed by unindented code, then build a notebook object with those cells.
The script should accept the input file path and an optional output file path via argparse, print an error and return False if the input file doesn't exist, and otherwise write the resulting notebook as JSON to the output path (defaulting to the input filename with a .ipynb extension) and report success."""

import argparse
import json
from pathlib import Path
import nbformat as nbf
def py_to_ipynb(input_file, output_file=None) -> bool:
    if not Path(input_file).exists():
        print(f"Error: File '{input_file}' not found.")
        return False
    code = Path(input_file).read_text(encoding="utf-8")
    nb = nbf.v4.new_notebook()
    cells = []
    current_cell = []
    lines = code.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if (
            i > 0
            and (
                line.startswith(("def ", "class "))
                or (
                    line.startswith(("import ", "from "))
                    and not current_cell[-1].startswith(("import ", "from "))
                )
                or (
                    line.strip() == ""
                    and current_cell
                    and i + 1 < len(lines)
                    and lines[i + 1].strip()
                    and not lines[i + 1].startswith((" ", "\t"))
                )
            )
            and current_cell
        ):
            cell_code = "\n".join(current_cell).strip()
            if cell_code:
                cells.append(nbf.v4.new_code_cell(cell_code))
            current_cell = []
        current_cell.append(line.rstrip())
        i += 1
    if current_cell:
        cell_code = "\n".join(current_cell).strip()
        if cell_code:
            cells.append(nbf.v4.new_code_cell(cell_code))
    nb["cells"] = cells
    if output_file is None:
        output_file = Path(input_file).stem + ".ipynb"
    with Path(output_file).open("w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print(f"Successfully converted '{input_file}' to '{output_file}'")
    print(f"Created {len(cells)} cell(s)")
    return True
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a Python script to a Jupyter notebook"
    )
    parser.add_argument("input", help="Input Python file (.py)")
    parser.add_argument(
        "output", nargs="?", help="Output notebook file (.ipynb) (optional)"
    )
    parser.add_argument(
        "--no-split",
        action="store_true",
        help="Don't split code into multiple cells (one cell only)",
    )
    args = parser.parse_args()
    if args.no_split:
        code = Path(args.input).read_text(encoding="utf-8")
        nb = nbf.v4.new_notebook()
        nb["cells"] = [nbf.v4.new_code_cell(code)]
        output_file = args.output or Path(args.input).stem + ".ipynb"
        with Path(output_file).open("w", encoding="utf-8") as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
        print(f"Successfully converted '{args.input}' to '{output_file}' (single cell)")
    else:
        py_to_ipynb(args.input, args.output)
if __name__ == "__main__":
    raise SystemExit(main())