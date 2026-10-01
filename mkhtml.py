#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that generates a basic HTML boilerplate file using a predefined template string containing links to "style.css" and "script.js" and a simple heading.
The script should accept a file path as its first command-line argument, defaulting to "index.html" if none is provided, and write the HTML template content to that file using UTF-8 encoding via pathlib.
Use sys.argv to read the argument and Path.write_text to perform the file writing."""

import sys
from pathlib import Path

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
