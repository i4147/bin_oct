#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that generates a basic HTML5 boilerplate file on disk. The script should accept an optional output filename, defaulting to "index.html" when none is provided. The generated file should be a minimal, valid HTML5 document with a UTF-8 charset declaration, a responsive viewport meta tag, a page title placeholder, a visible "Hello, World!" heading in the body, and a comment marking where additional content should be added. The file should be written using UTF-8 encoding into the current working directory. Upon success, the script should print a confirmation message that includes the filename and the directory where it was created. If the file cannot be written for any reason, the script should catch the error and print a readable error message instead of crashing. The script should be runnable directly from the command line and perform its main action only when executed as the entry point, not when imported as a module.
---"""

from __future__ import annotations
from pathlib import Path


def create_html_template(filename: str = "index.html") -> None:
    html_template = '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Document</title>\n</head>\n<body>\n    <h1>Hello, World!</h1>\n    <!-- Your content here -->\n</body>\n</html>\n'
    try:
        Path(filename).write_text(html_template, encoding="utf-8")
        print(f"Successfully created {filename} in {Path.cwd()}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    create_html_template()
