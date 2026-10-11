#!/data/data/com.termux/files/usr/bin/env python
"""Write a single-file Python 3 command-line script (intended for Termux on Android, so include the Termux shebang `#!/data/data/com.termux/files/usr/bin/env python`) that normalizes unusual whitespace characters in a text file, in place.

Requirements:

- Begin with the Termux shebang line, then `from __future__ import annotations`. Use only the standard library: `re`, `sys`, and `pathlib.Path`.
- Define a function `normalize_white_space(input_path: str) -> None` with full type hints.
- Read the file at `input_path` as UTF-8 text, using `errors="ignore"` so undecodable bytes are silently dropped rather than raising an exception.
- First pass: replace each of the following Unicode whitespace characters with a plain ASCII space (U+0020):
  - U+00A0 (no-break space)
  - the range U+2000 through U+200F (en/em spaces, zero-width space variants, and directional marks)
  - U+2028 (line separator) and U+2029 (paragraph separator)
  - U+202F (narrow no-break space)
  - U+205F (medium mathematical space)
  - U+3000 (ideographic space)
  - U+FEFF (byte order mark / zero-width no-break space)
  Implement this with a single regex character class using `\\u` escapes.
- Second pass: delete (replace with empty string) the zero-width characters U+200B through U+200D and U+FEFF.
- Write the cleaned text back to the same path as UTF-8. Overwrite the original file in place; do not create a backup and do not write to a separate output file.
- Note the ordering: the first pass converts U+FEFF to a space, so the second pass's U+FEFF rule only affects any U+FEFF remaining after the first pass (in practice, none). Preserve this two-step order exactly.
- Main entry point guarded by `if __name__ == "__main__":`. Read the single filename from `sys.argv[1]` and call the function with it. Do not add argument validation, usage messages, or error handling beyond what this implies, so a missing argument raises the default `IndexError` and a missing file raises the default `FileNotFoundError` from pathlib.
- No output is printed on success; the script exits silently with status 0.
- Keep the code minimal, with no extra classes, logging, or configuration. Use docstrings or comments only if they fit the minimal style.
- Usage: `python script.py <path-to-file>`, run from the Termux shell. The file is modified in place, so the user should keep backups if they need the original text.
---"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def normalize_white_space(input_path: str) -> None:
    text = Path(input_path).read_text(encoding="utf-8", errors="ignore")
    cleaned = re.sub(r"[\u00A0\u2000-\u200F\u2028\u2029\u202F\u205F\u3000\uFEFF]", " ", text)
    cleaned = re.sub(r"[\u200B-\u200D\uFEFF]", "", cleaned)
    Path(input_path).write_text(cleaned, encoding="utf-8")


if __name__ == "__main__":
    fname = sys.argv[1]
    normalize_white_space(fname)
