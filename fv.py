#!/data/data/com.termux/files/usr/bin/env python
"""Write a single-file Python 3 command-line script, intended to run under Termux on Android (use the shebang `#!/data/data/com.termux/files/usr/bin/env python`). It should begin with `from __future__ import annotations`.

Purpose: a minimal text file viewer. It takes one file path from the command line, reads the file's full contents, and displays them through Python's built-in `pydoc` pager so the user can scroll through the text interactively.

Requirements:

- Imports: `pydoc`, `sys`, and `pathlib.Path` from the standard library only. No third-party dependencies.
- Define a `main()` function with a `-> None` return annotation. It should:
  - Read the first positional argument from `sys.argv[1]` and convert it to a `Path`.
  - Read the file as text using UTF-8 encoding with `errors="replace"`, so undecodable bytes are substituted rather than raising an exception.
  - Pass the resulting string to `pydoc.pager(...)`.
- Entry point: guard with `if __name__ == "__main__":` and call `raise SystemExit(main())`, so the process exits with status 0 on normal completion.

Behavior and edge cases to reproduce:

- The script takes exactly one meaningful argument. It does not validate argument count explicitly; if no path is supplied, the resulting `IndexError` is left unhandled and the script terminates with a traceback. Likewise, a missing or unreadable file raises the standard `FileNotFoundError`/`OSError` without custom handling. Do not add extra argument parsing, help text, or try/except blocks unless needed to match this behavior.
- Paging is delegated entirely to `pydoc.pager`, which uses the system pager (typically `less` or `more`) when attached to a terminal, and falls back to plain output otherwise. Do not implement custom paging, scrolling, or terminal handling.
- Decoding never fails on invalid UTF-8; invalid sequences become replacement characters.
- The whole file is loaded into memory at once, so very large files will consume correspondingly large memory.
- Output goes to the pager, not through `print`, and no other output is produced.

Usage: `python <script>.py <path-to-file>` (or run directly via the shebang after making the file executable). Keep the script short, with no classes, logging, configuration files, or extra features.
---"""

from __future__ import annotations

import pydoc
import sys
from pathlib import Path


def main() -> None:
    pydoc.pager(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace"))


if __name__ == "__main__":
    raise SystemExit(main())
