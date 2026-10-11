#!/data/data/com.termux/files/usr/bin/env python
"""Write a single-file Python 3 script, intended to run under Termux (shebang pointing to the Termux Python interpreter at /data/data/com.termux/files/usr/bin/env python). It should use `from __future__ import annotations` and import only `sys` and `pathlib.Path` from the standard library, with no third-party dependencies.

Behavior when run as the main program:

- Take exactly one command-line argument: a file path. Strip leading and trailing whitespace from that argument before using it as a path.
- Read the file in binary mode as raw bytes.
- Then treat those bytes as text and decode backslash escape sequences in it: first encode the bytes to UTF-8 bytes (this step is applied to the already-read bytes object, so the input is handled as text at that point), then apply Python's `unicode_escape` codec to turn sequences such as `\\n`, `\\t`, `\\\\`, `\\"`, and `\\uXXXX` into their actual characters.
- Overwrite the same file with the decoded result, writing it as UTF-8 text.
- Print a single confirmation line of the form `<path> updated`, where the path is the stripped argument as given.

Key details and edge cases to reproduce faithfully:

- The script has no `main()` function; the logic lives directly under an `if __name__ == "__main__":` guard.
- No argument validation or error handling is present. A missing argument, a nonexistent file, a directory path, or a permission error will surface as an uncaught exception and a non-zero exit. Do not add try/except blocks or usage messages unless asked.
- The `unicode_escape` decoding operates on text whose non-ASCII characters are already UTF-8 encoded; byte sequences that are invalid under this codec will raise an exception, which should be left uncaught.
- The file is read and written in full (no streaming), so it is suitable only for files that fit in memory.
- The file is modified in place; no backup is created.
- Output the file path exactly as the user supplied it (after stripping), not a resolved absolute path.

Deliver the script as one complete file with the Termux shebang at the top, minimal formatting, and no extra comments beyond what is needed.
---"""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__":
    path = Path(sys.argv[1].strip())
    text = path.read_bytes()
    decoded = text.encode("utf-8").decode("unicode_escape")
    path.write_text(decoded, encoding="utf-8")
    print(f"{path} updated")
