#!/data/data/com.termux/files/usr/bin/env python
"""Write a single-file Python 3 command-line script that, given a file path as its first argument, reads that file as UTF-8 text, decodes all HTML character references in its contents, and writes the result back to the same file as UTF-8.

Requirements:

- Start with a shebang line pointing to the Termux Python interpreter at /data/data/com.termux/files/usr/bin/env python, and place `from __future__ import annotations` at the top of the module.
- Use only the Python standard library: `sys`, `html.unescape`, and `pathlib.Path`. No third-party dependencies.
- Define a `main()` function with no return value annotation of anything other than `None`. It should:
  - Take the target file path from `sys.argv[1]` and wrap it in a `Path`.
  - Read the file with `read_text(encoding="utf-8", errors="replace")`, so invalid UTF-8 byte sequences are replaced rather than raising an exception.
  - Pass the full text through `html.unescape` to convert named, decimal, and hexadecimal HTML entities (e.g., `&amp;`, `&#39;`, `&#x41;`) into their literal characters.
  - Overwrite the same file with the unescaped text using `write_text(..., encoding="utf-8")`. The file is modified in place; no backup or separate output file is created.
- Under the `if __name__ == "__main__":` guard, call `main()` and pass its result to `raise SystemExit(...)`, so the process exits with status 0 on success.

Behavior and edge cases:

- The script performs no argument validation. If no path is supplied, accessing `sys.argv[1]` raises an `IndexError` and the script terminates with a traceback; a missing file raises `FileNotFoundError`, and an unwritable path raises `OSError`. These exceptions are intentionally left unhandled, so the script exits with a non-zero status and a traceback.
- Only the first command-line argument is used; any additional arguments are ignored.
- The entire file is loaded into memory at once, so very large files are read fully before writing.
- Unescaping is applied once per run; double-encoded entities (such as `&amp;amp;`) become `&amp;` after one run and are not further decoded.
- Line endings and all other bytes are preserved exactly, apart from entity substitutions.
- Output should be minimal: the script prints nothing on success.

Usage: run as `python <script> <file>` (or execute directly on Termux via its shebang). Keep the code concise, idiomatic, and consistent with the style of a small utility script, with no extra comments beyond what is needed.
---"""

from __future__ import annotations

import sys
from html import unescape
from pathlib import Path


def main() -> None:
    fn = Path(sys.argv[1])
    content = fn.read_text(encoding="utf-8", errors="replace")
    fn.write_text(unescape(content), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
