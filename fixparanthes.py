#!/data/data/com.termux/files/usr/bin/env python
"""I'll write the prompt now.

Write a self-contained Python 3 command-line script (intended to run under Termux on Android, so use a `#!/data/data/com.termux/files/usr/bin/env python` shebang and `from __future__ import annotations`) that reads a JSON file, rewrites bracket characters inside every JSON string literal, and writes the result back. Use only the standard library: `json`, `re`, `sys`, and `pathlib.Path`.

**Purpose and usage**
- Invoked as `<script> <json-file>` with exactly one argument. If the argument count is not exactly two, print a usage message of the form `usage: <script name> <json-file>` (script name taken from the invoked path's basename) and exit via `sys.exit` with that message.
- The script processes a single JSON file given by that path.

**String detection**
- Define a module-level compiled regex matching a double-quoted JSON-style string: an opening `"`, then any sequence of either a non-quote, non-backslash character or a backslash followed by any character, then a closing `"`. Use it with `re.sub` over the raw file text so that only string literals are altered and structural JSON outside strings is left untouched.

**Per-string transformation (`fix_content`)**
Process the inner content of each matched string character by character with an index loop:
- A backslash followed by `[` or `{` is replaced with `(` (the backslash and the bracket are both consumed, two characters advanced).
- A backslash followed by `]` or `}` is replaced with `)`.
- A backslash followed by `(` or `)` is emitted as that parenthesis alone (backslash dropped).
- Any other backslash escape is copied through unchanged as the backslash plus the following character.
- A backslash at the very end of the content with no following character is copied as-is.
- An unescaped `[` or `{` becomes `(`; an unescaped `]` or `}` becomes `)`; all other characters are copied unchanged.
- After the loop, count `(` and `)` in the resulting string. If there are more opens than closes, append the missing `)` characters at the end. If there are more closes than opens, prepend the missing `(` characters at the start. Otherwise leave it unchanged.

**Per-match wrapper (`fix_literal`)**
- Takes a regex match object, takes the full matched text, strips the surrounding quote characters, applies `fix_content` to the inner text, and returns it re-wrapped in double quotes.

**`main` flow**
- Validate argument count as above.
- Convert the argument to a `Path`. Read the file as text (UTF-8). Apply the string regex substitution using `fix_literal`.
- Parse-check or write the output so that the file is saved with the transformed text. Ensure the result is written back to the same path (overwriting the original) using UTF-8, and handle the case where the file is missing or unreadable by printing an error and exiting non-zero rather than crashing with a traceback.
- Include a `if __name__ == "__main__": main()` guard.
- Type-annotate functions (`-> str`, `-> None`, `re.Match` parameter) consistent with `from __future__ import annotations`.

**Edge cases and behavior notes**
- Brackets outside string literals are not modified.
- Escaped quotes inside strings are handled by the regex's backslash-pair alternative, so `\\"` does not terminate a string.
- Paren balancing is per string literal, not globally, and only adds parentheses at the ends of each string.
- The script makes no attempt to validate the JSON after transformation; output correctness depends on the input.
- Keep code style plain and idiomatic: short helper functions, index-based loops where shown, minimal comments, no external dependencies.
---"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

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
