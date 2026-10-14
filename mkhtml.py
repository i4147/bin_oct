#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that creates a starter HTML file from a built-in template. The script should run from the command line, accept an optional output file path as its first argument, and default to creating a file named index.html in the current directory when no path is given. When run, it writes a minimal HTML5 boilerplate page with a title "html template", a linked stylesheet named style.css and a linked script named script.js in the document head, and a body containing a div with a level-two heading reading "Heading2". The file must be saved using UTF-8 encoding. The script should be a simple, self-contained command-line utility that produces the file silently on success, with no additional output, and should handle the case where the provided path is invalid or cannot be written by reporting a clear error message to the user.
---"""

from __future__ import annotations
from pathlib import Path
import sys

HTML_TEMPLATE = """<!doctype html>
<html>
  <head>
    <link rel="stylesheet" href="style.css" />
    <script src="script.js"></script>
    <title>html template</title>
  </head>
  <body>
    <div>
      <h2>Heading2</h2>
    </div>
  </body>
</html>
"""
if __name__ == "__main__":
    file_name = Path(sys.argv[1]) or Path("index.html")
    file_name.write_text(HTML_TEMPLATE, encoding="utf-8")
