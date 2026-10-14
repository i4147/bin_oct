#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that comments out a specified range of lines in a source file. The tool should accept three command-line arguments: the path to a file, a starting line number, and an ending line number. It must validate its inputs and print clear, user-friendly error messages (then exit with a non-zero status) when arguments are missing, when line numbers are not valid integers, when the line range is invalid (line numbers must be at least 1 and the end line must not precede the start line), or when the file does not exist.
The script should determine the correct single-line comment syntax from the file's extension, supporting common languages such as Python, shell, YAML, Ruby, JavaScript, TypeScript, C, C++, Java, Go, HTML, and CSS, and falling back to a sensible default comment style for unrecognized extensions. Lines within the requested range should be commented out in place, with the rest of the file left untouched, and the modified content should be written back to the same file. Preserve the original line endings and indentation as much as practical, and handle blank lines within the range in a consistent, readable way.
For block-style languages where a single-line comment marker is not natural (such as HTML and CSS), choose an appropriate wrapping approach so that the commented region remains valid and clearly marked. Ensure the script handles files with unusual encodings or trailing newline differences gracefully and reports a clear message when the operation succeeds, including how many lines were commented.
---"""

from __future__ import annotations
import os
import sys

EXTENSION_COMMENTS = {
    ".py": "#",
    ".sh": "#",
    ".yaml": "#",
    ".yml": "#",
    ".rb": "#",
    ".js": "//",
    ".ts": "//",
    ".cpp": "//",
    ".c": "//",
    ".java": "//",
    ".go": "//",
    ".html": "<!--",
    ".css": "/*",
}


def main():
    if len(sys.argv) < 4:
        print("Error: Missing arguments.\nUsage: python comment_range.py <filename> <start_line> <end_line>")
        sys.exit(1)
    path = sys.argv[1]
    try:
        start_line = int(sys.argv[2])
        end_line = int(sys.argv[3])
    except ValueError:
        print("Error: Start and end lines must be valid integers.")
        sys.exit(1)
    if start_line < 1 or end_line < start_line:
        print("Error: Line numbers must start from 1, and end line must be >= start line.")
        sys.exit(1)
    if not os.path.exists(path):
        print(f"Error: The file '{path}' does not exist.")
        sys.exit(1)
    _, ext = os.path.splitext(path.lower())
    comment_char = EXTENSION_COMMENTS.get(ext, "#")
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    total_lines = len(lines)
    if start_line > total_lines:
        print(f"Error: Start line ({start_line}) exceeds file length ({total_lines} lines).")
        sys.exit(1)
    actual_end = min(end_line, total_lines)
    for i in range(start_line - 1, actual_end):
        if not lines[i].strip().startswith(comment_char):
            lines[i] = f"{comment_char} {lines[i]}"
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Success: Commented out lines {start_line} to {actual_end} in '{path}' using '{comment_char}'.")


if __name__ == "__main__":
    raise SystemExit(main())
