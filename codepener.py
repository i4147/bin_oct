#!/data/data/com.termux/files/usr/bin/env python
"""The code you pasted is cut off mid-string at `print(f"Err`, so the `process_file` error handling and the `main` entry point are not visible. I'll write the prompt based on what is shown and mark the unseen parts as assumptions the agent should decide on sensibly.

Write a self-contained Python 3 command-line script that wraps raw HTML body content (such as a CodePen-style snippet) into a complete standalone HTML5 document.

**Purpose**
The script reads an HTML fragment from a file, wraps it in a full HTML5 page skeleton, and writes the result to an output file. It is intended to run under Termux on Android, so the shebang should point to the Termux Python path (`/data/data/com.termux/files/usr/bin/env python`).

**Behavior and structure to reproduce**

1. Start the file with the Termux-style shebang and `from __future__ import annotations`. Import `sys` and `pathlib.Path`.

2. Provide a pure function that takes the HTML body fragment, an optional `title` (default `"Document"`), and an optional `charset` (default `"UTF-8"`). It returns a complete HTML5 document string with:
   - a `<!DOCTYPE html>` declaration and `<html lang="en">`;
   - a `<head>` containing a UTF-8 (or the given) meta charset, a viewport meta tag (`width=device-width, initial-scale=1.0`), the title, and a stylesheet link to `style.css` (relative href);
   - a `<body>` containing the fragment verbatim, followed by a script tag loading `script.js` (relative src), then closing tags.
   Build the string with an f-string, keeping the output format exact (newlines and indentation of four spaces as shown in a conventional HTML template).

3. Provide a `process_file` function with parameters `input_file`, `output_file=None`, and `title=None`:
   - Read `input_file` using UTF-8 encoding. On `FileNotFoundError`, print an error message naming the file and return `False`. On any other exception, print an error including the exception text and return `False`.
   - If `title` is `None`, derive it from the input file's stem: replace hyphens with spaces and apply title-case (e.g., `my-page.html` becomes `My Page`), using `pathlib.Path`.
   - Call the wrapping function with the content and title.
   - If `output_file` is `None`, overwrite the input file in place.
   - Write the result to the output file in UTF-8. On success, print a check-marked line stating the input was successfully converted, and a second check-marked line stating where it was saved, then return `True`. On a write exception, print an error message with the exception text and return `False` (the exact wording of the write-failure branch was cut off in the source, so use a sensible message beginning with "Error").

4. Include a command-line entry point guarded by `if __name__ == "__main__":` that uses `sys.argv`:
   - Accept an input file path as the first argument, an optional output file path as the second, and an optional title as the third (or equivalent sensible positional handling).
   - If no input argument is given, print a usage message showing how to invoke the script and exit with a nonzero status.
   - Call `process_file` with the parsed arguments and exit with status 0 on success or 1 on failure (based on the boolean return value).

**Edge cases and notes**
- Missing input file must be handled gracefully without a traceback.
- Non-UTF-8 input will be caught by the generic exception handler when reading.
- Output file defaults to overwriting the input file; the agent should make this explicit in usage text.
- Titles derived from filenames should handle multiple hyphens and mixed case consistently.
- Do not add third-party dependencies; use only the standard library.
- Keep the code minimal, readable, and consistent with typical Python style (PEP 8, docstrings optional but concise).

**Deliverable**
A single runnable Python script file implementing all of the above, with no external dependencies.
---"""

from __future__ import annotations

import sys
from pathlib import Path


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
