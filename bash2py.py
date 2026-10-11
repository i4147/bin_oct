#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python command-line utility named bash2py that extracts embedded Python heredoc bodies from a Bash script. Requirements to convey:

Create a Python 3 script (with a Termux-style shebang pointing to the Termux Python interpreter, and `from __future__ import annotations` at the top) that reads a Bash script file whose path is given as the single command-line argument. It should use only the standard library: `re`, `sys`, and `pathlib`.

Detection rule: a line qualifies as a heredoc start when, after optional leading spaces or tabs, it begins with `python`, `python3`, or `py` as a whole word, followed by any text on the same line, then `<<`, an optional `-` immediately after the `<<`, optional spaces or tabs, an optional single or double quote, an identifier delimiter (letters or underscore, then letters, digits, or underscores), a matching closing quote if one was opened, optional trailing spaces or tabs, and end of line. Capture the indentation, command, dash flag, quote, and delimiter as named groups. Compile the pattern with multiline mode, though it is applied per line.

Extraction rule: scan the file line by line, preserving line endings. For each matching start line, collect following lines as the body until a terminator line is found. The terminator matches the delimiter exactly after stripping the trailing newline; if the start used the dash flag, the terminator comparison first strips leading and trailing whitespace from the line. The body lines exclude the terminator. When a terminator is found, store the joined body text and resume scanning after the terminator. If no terminator is found before end of file, store everything after the start line as the body and stop scanning. Return the list of all extracted bodies in order. Note that a start line is only checked at the outer scan position, so nested or consecutive heredocs are handled by resuming after each block's terminator.

Main behavior: if fewer than two command-line arguments are supplied, print a usage message to standard error of the form "Usage: python bash2py.py <bash_script_path>" and exit with a nonzero status. Note that the original code has a defect: it references the exit function without calling it, so it does not actually terminate; the reproduction should call it with a nonzero status code, and this should be stated as the intended behavior. Otherwise, read the file at the given path, extract the heredoc bodies, and write results to standard output, separating blocks clearly. Edge cases to handle: a missing or unreadable file should produce a clear error to standard error with a nonzero exit; an empty file or a file with no matching heredocs should produce no block output without crashing; file encoding should be read as UTF-8 with reasonable handling of decode errors.

Execution details: the script is run directly via its shebang or with the Python interpreter, takes the bash script path as its only argument, and should include an `if __name__ == "__main__":` guard calling main. Output should be plain text suitable for piping. Keep the implementation concise, idiomatic, and commented sparingly, matching standard Python style with type hints where helpful.
---"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HEREDOC_START_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<cmd>(?:python3?|py)\b[^\n]*?)"
    r"<<(?P<dash>-)?[ \t]*"
    r'(?P<quote>["\']?)(?P<delim>[A-Za-z_][A-Za-z0-9_]*)(?P=quote)[ \t]*$',
    re.MULTILINE,
)


def extract_python_heredocs(bash_text: str):
    blocks = []
    lines = bash_text.splitlines(keepends=True)
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m = HEREDOC_START_RE.match(line.rstrip("\n"))
        if not m:
            i += 1
            continue
        delim = m.group("delim")
        dash = m.group("dash") is not None
        body_lines = []
        j = i + 1
        terminator_found = False
        while j < n:
            raw = lines[j]
            stripped = raw.rstrip("\n")
            candidate = stripped.strip() if dash else stripped
            if candidate == delim:
                terminator_found = True
                break
            body_lines.append(raw)
            j += 1
        if terminator_found:
            blocks.append("".join(body_lines))
            i = j + 1
        else:
            blocks.append("".join(lines[i + 1 :]))
            i = n
    return blocks


def main():
    if len(sys.argv) < 2:
        print("Usage: python bash2py.py <bash_script_path>", file=sys.stderr)
        sys.exit(1)
    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    bash_text = input_path.read_text(encoding="utf-8")
    blocks = extract_python_heredocs(bash_text)
    if not blocks:
        print("No python heredocs found in the given script.", file=sys.stderr)
        sys.exit(1)
    base_name = input_path.stem
    out_dir = Path.cwd()
    written = []
    if len(blocks) == 1:
        out_path = out_dir / f"{base_name}.py"
        out_path.write_text(blocks[0], encoding="utf-8")
        written.append(out_path)
    else:
        for idx, code in enumerate(blocks, start=1):
            out_path = out_dir / f"{base_name}_{idx}.py"
            out_path.write_text(code, encoding="utf-8")
            written.append(out_path)
    for p in written:
        print(f"Wrote: {p}")


if __name__ == "__main__":
    main()
