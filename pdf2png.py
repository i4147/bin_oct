#!/data/data/com.termux/files/usr/bin/env python
"""Create a self-contained prompt that tells an AI coding agent to build a Python 3 command-line script with the following specification.

Write a Python 3 command-line script for Termux (Android) that converts a PDF file into one PNG image per page, using the external `pdftoppm` tool from Poppler.

**Purpose**
The script takes a PDF path and renders every page as a PNG at a configurable resolution, then renames the outputs to a consistent, zero-padded naming scheme.

**Interface**
- Start the file with a shebang pointing to the Termux Python interpreter at `/data/data/com.termux/files/usr/bin/env python`.
- Use only the standard library: `sys`, `os`, `shutil`, and `subprocess`.
- Define a function `pdf_to_png(pdf_path, output_dir=None, dpi=200)` as the core logic, and call it from a `__main__` guard using command-line arguments from `sys.argv`.
- Accept the PDF path as the required first argument, and an optional output directory and DPI value. Default DPI is 200.

**Behavior and steps**
1. Verify the PDF file exists using `os.path.isfile`. If not, print `Error: file not found: <path>` to stderr and exit with status 1.
2. Check that `pdftoppm` is available using `shutil.which`. If missing, print an error to stderr stating that `pdftoppm` was not found and suggesting installation with `pkg install poppler`, then exit with status 1.
3. Derive the base name from the PDF filename without its extension. If no output directory was given, use the base name as the directory.
4. Create the output directory (including parents) with `os.makedirs(..., exist_ok=True)`.
5. Build the output prefix as `<output_dir>/<base_name>_page`.
6. Run `pdftoppm` with arguments: `-png`, `-r <dpi>`, the PDF path, and the prefix. Print the full command as `Running: ...` before executing it. Capture stdout and stderr as text using `subprocess.run`.
7. If the return code is nonzero, print `pdftoppm failed:` and the captured stderr to stderr, then exit with status 1.
8. After success, list the output directory, select files starting with `<base_name>_page-`. For each, extract the page number from the portion after the last hyphen (before the extension). Skip any file whose number cannot be parsed as an integer.
9. Rename each file to `<base_name>_page_NNN.png`, with the page number zero-padded to three digits (e.g., `_page_001.png`). Rename using `os.rename` within the output directory.
10. On completion, print a summary indicating how many pages were converted and where the files are saved.

**Edge cases and notes**
- `pdftoppm` names pages with varying digit widths (e.g., `-1.png` vs `-01.png`); the script must handle any width by parsing the integer.
- Unparseable filenames are silently skipped rather than causing a crash.
- Paths with spaces should be handled correctly by passing arguments as a list, never through a shell.
- Do not use `shell=True`.
- Error messages go to stderr; normal progress goes to stdout.
- Usage example: `python script.py document.pdf [output_dir] [dpi]`; print a usage message and exit nonzero if the PDF argument is missing.
---"""

import os
import shutil
import subprocess
import sys


def pdf_to_png(pdf_path, output_dir=None, dpi=200):
    if not os.path.isfile(pdf_path):
        print(f"Error: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    if shutil.which("pdftoppm") is None:
        print(
            "Error: 'pdftoppm' not found. Install with: pkg install poppler",
            file=sys.stderr,
        )
        sys.exit(1)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    if output_dir is None:
        output_dir = base_name
    os.makedirs(output_dir, exist_ok=True)
    prefix = os.path.join(output_dir, f"{base_name}_page")
    cmd = [
        "pdftoppm",
        "-png",
        "-r",
        str(dpi),
        pdf_path,
        prefix,
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("pdftoppm failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    generated = sorted(f for f in os.listdir(output_dir) if f.startswith(f"{base_name}_page-"))
    for f in generated:
        num_part = f.rsplit("-", 1)[-1].split(".")[0]
        try:
            num = int(num_part)
        except ValueError:
            continue
        new_name = f"{base_name}_page_{num:03d}.png"
        os.rename(os.path.join(output_dir, f), os.path.join(output_dir, new_name))
        print(f"  {new_name}")
    print(f"Done. {len(generated)} image(s) saved to '{output_dir}/'")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    input_pdf = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 else None
    dpi_value = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    pdf_to_png(input_pdf, output_directory, dpi_value)
