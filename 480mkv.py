#!/data/data/com.termux/files/usr/bin/env python
"""Write a single self-contained Python 3 script (intended for Termux on Android, so the shebang points to the Termux Python path) that filters a text file of links down to the lines matching a preferred video quality.

Behavior requirements:

- Purpose: read a text file whose lines are video links, keep only the lines that reference an mkv or mp4 file at a chosen quality, overwrite the same file with those kept lines, and report how many were kept.
- Input: a single required command-line argument giving the path to the text file. Read it as UTF-8.
- Quality selection: if the substring "480" appears anywhere in the file content, use 480 as the target quality; otherwise use 720. Match the chosen quality as a plain substring of each line.
- Filtering rule: a line is kept only if it is non-empty after stripping whitespace, contains "mkv" or "mp4" (case-sensitive substring), and contains the chosen quality string. Lines are otherwise discarded.
- Output: if at least one line matches, overwrite the input file with the kept lines joined by newline characters, written as UTF-8. If no lines match, leave the file unchanged. In both cases print exactly one line to standard output in the form "N links found." where N is the count of kept lines.
- Structure: the logic runs only when the script is executed directly, not when imported. Use `from __future__ import annotations` and `pathlib.Path` for file access, and `sys` for argument access.
- Dependencies: Python standard library only.
- Error handling: none is required beyond natural Python behavior; a missing argument or missing file will raise the standard exception. Do not add extra validation unless needed for correctness.
- Edge cases to preserve: empty file (zero matches, file untouched, prints "0 links found."); file containing both 480 and 720 lines (the 480 path is chosen whenever "480" appears anywhere in the content, even if it only appears in a non-link line); trailing newline in the original file is not preserved in the output because the output uses a join on lines.
- Usage: run from the command line as `python <script> <path-to-text-file>`, with the script file marked executable and invoked via its shebang line for Termux environments.
- Output the complete script only, with a brief comment at the top describing its purpose.
---"""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__":
    fn = Path(sys.argv[1])
    content = fn.read_text(encoding="utf-8")
    lines = content.splitlines()
    lowest = "480" if "480" in content else "720"
    nl = [line for line in lines if line.strip() and ("mkv" in line or "mp4" in line) and (lowest in line)]
    if nl:
        fn.write_text("\n".join(nl), encoding="utf-8")
    print(f"{len(nl)} links found.")
