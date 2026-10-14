#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a raw HTML fragment saved in a local file (such as an exported CodePen body snippet) and wraps it into a complete, standalone HTML5 document ready for use in a browser. The tool should accept the input file path as a required argument, and optionally an output file path and a custom page title. If no output path is given, it should derive a sensible output filename from the input. If no title is provided, it should generate a readable page title automatically from the input file's name (replacing hyphens with spaces and capitalizing words).
The generated document should include a proper HTML5 doctype, a language attribute, UTF-8 character encoding (configurable), a responsive viewport meta tag, the page title, and links to an external stylesheet and an external script file, with the original fragment placed inside the body and the script reference placed at the end of the body so that the page loads correctly.
The script should read the input file as UTF-8 text and handle common errors gracefully: a missing input file, or any other read failure, should print a clear, user-friendly error message to the console and exit without crashing or producing a partial output file. On success, it should write the complete HTML to the output file and print a brief confirmation message indicating where the file was saved.
The tool should be runnable from the command line, print usage help when arguments are missing or invalid, and return an appropriate exit status (zero on success, non-zero on failure). Keep the implementation clean, modular, and well-documented with docstrings, and make the core HTML-wrapping logic reusable as a standalone function that other Python code can import.
---"""

from __future__ import annotations
from pathlib import Path
import sys


def convert_codepen_html(html_content, title="Document", charset="UTF-8"):
    full_html = f'<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="{
        charset
    }">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>{
        title
    }</title>\n    <link rel="stylesheet" href="style.css">\n</head>\n<body>\n{
        html_content
    }\n    <script src="script.js"></script>\n</body>\n</html>\n'
    return full_html


def process_file(input_file, output_file=None, title=None):
    try:
        with open(input_file, encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return False
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    if title is None:
        title = Path(input_file).stem.replace("-", " ").title()
    full_html = convert_codepen_html(html_content, title)
    if output_file is None:
        output_file = input_file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_html)
        print(f"✓ Successfully converted: {input_file}")
        print(f"✓ Saved to: {output_file}")
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python codepen_converter.py <input_file> [output_file] [--title 'Page Title']")
        print("\nExample:")
        print("  python codepen_converter.py index.html")
        print("  python codepen_converter.py codepen.html output.html")
        print("  python codepen_converter.py codepen.html --title 'My Project'")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = None
    title = None
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--title" and i + 1 < len(sys.argv):
            title = sys.argv[i + 1]
            i += 2
        else:
            output_file = sys.argv[i]
            i += 1
    success = process_file(input_file, output_file, title)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    raise SystemExit(main())
