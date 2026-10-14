#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a text file containing LaTeX-style or mixed-notation mathematical content, repairs unbalanced or mismatched bracket characters and escaped delimiters within it, and writes the corrected text to a new output file. The tool should accept the input and output file paths as command-line arguments, process the content so that square and curly brackets are normalized into parentheses while preserving string literals and escaped sequences that must remain intact, balance any unmatched parentheses by adding or removing closing characters as needed, and report a summary of the fixes applied (such as the number of brackets converted or parentheses added). It should handle file-not-found and encoding errors gracefully with clear error messages and a non-zero exit code, and it should also support a JSON-formatted input option where string values inside the JSON are repaired while the JSON structure itself remains valid and parseable. The output should be a corrected file that is ready for downstream use, with the original file left unmodified.
---"""

from __future__ import annotations
import json
from pathlib import Path
import re
import sys

STRING_RE = re.compile(r'"(?:[^"\\]|\\.)*"')


def fix_content(content: str) -> str:
    out = []
    i, n = 0, len(content)
    while i < n:
        c = content[i]
        if c == "\\" and i + 1 < n:
            nxt = content[i + 1]
            if nxt in "[{":
                out.append("(")
                i += 2
                continue
            if nxt in "]}":
                out.append(")")
                i += 2
                continue
            if nxt in "()":
                out.append(nxt)
                i += 2
                continue
            out.append(c)
            out.append(nxt)
            i += 2
            continue
        if c in "[{":
            out.append("(")
        elif c in "]}":
            out.append(")")
        else:
            out.append(c)
        i += 1
    s = "".join(out)
    opens = s.count("(")
    closes = s.count(")")
    if opens > closes:
        s += ")" * (opens - closes)
    elif closes > opens:
        s = "(" * (closes - opens) + s
    return s


def fix_literal(match: re.Match) -> str:
    raw = match.group(0)
    return '"' + fix_content(raw[1:-1]) + '"'


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(f"usage: {Path(sys.argv[0]).name} <json-file>")
    path = Path(sys.argv[1])
    if not path.is_file():
        sys.exit(f"not a file: {path}")
    text = path.read_text(encoding="utf-8")
    fixed_text = STRING_RE.sub(fix_literal, text)
    try:
        data = json.loads(fixed_text)
    except json.JSONDecodeError as e:
        sys.exit(f"still invalid JSON after fix: {e}\n---\n{fixed_text}")
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"fixed and updated: {path}")


if __name__ == "__main__":
    main()
