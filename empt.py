#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python 3.12 script intended to run under Termux on Android (using the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that truncates (empties) a file specified via the command line.

Main behavior and requirements:
- Use `from __future__ import annotations` for annotation handling.
- Import `sys` for accessing command-line arguments and `pathlib.Path` for filesystem operations.
- Wrap the main logic in an `if __name__ == "__main__":` guard.
- Read the target file path from `sys.argv[1]` (the first command-line argument passed to the script).
- Strip any leading/trailing whitespace from that argument using `.strip()`.
- Convert the cleaned string into a `Path` object.
- Call `.write_text("")` on that `Path` object to overwrite the file's contents with an empty string, effectively clearing/truncating the file (if the file does not exist, this will create a new empty file at that path).
- The script takes exactly one required input: a file path as the first command-line argument.
- There is no explicit standard output; the only effect is the side effect of emptying/creating the specified file.
- Do not add argument validation, error handling, or usage messages—keep the logic minimal and direct, matching a simple utility script for clearing a file's contents.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/iaekmefFKiheR6sfwhcrh4"""

from __future__ import annotations
import sys
from pathlib import Path

if __name__ == "__main__":
    Path(sys.argv[1].strip()).write_text("")
