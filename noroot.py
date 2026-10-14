#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory tree for shell script files andes a specific kind of conditional exit guard from them. The script should start from the current working directory, obtain the list of target files through a helper that returns the non-binary files in that location, and process each file in turn.
For each file, the script should read its contents as UTF-8 text and repeatedly locate and delete every block that matches this pattern: an `if` statement that tests whether a command substitution of some variable or expression returns a non-zero value (written in the style `if [ $(...) -ne 0 ]; then`), followed by a body that ends with an `exit 1` line, and then closed by an `fi` terminator. The match should be case-insensitive and span multiple lines, and any content between the `exit 1` line and the `fi` should also be removed along with the whole block. Only the matching blocks should be removed; all other content must be preserved exactly as it was.
If a file was changed, the script should write the cleaned content back to that same file in UTF-8 and print a short message identifying the file that was cleaned. Files with no matches must be left untouched and not rewritten. If any error occurs while handling a particular file (such as an unreadable file or a write failure), the script should print a descriptive error message to standard error that includes the file path, and then continue processing the remaining files rather than stopping.
The script should be runnable directly from the command line with no required arguments and should produce no output for files that do not need changes beyond the cleaned-file messages and error reports.
---"""

from __future__ import annotations
from pathlib import Path
import re
import sys
from dh import get_nobinary

IF_BLOCK_REGEX = re.compile(
    r"^if\s+\[\s*\$\((\S+)\)\s*\{\-ne\s+0\s*\}\]\s*;\s*then\s*\n((?:.|\n)*?)^\s*exit\s+1\s*$(.*?)^\s*fi",
    re.MULTILINE | re.IGNORECASE,
)


def remove_conditional_exit_blocks(path: Path) -> None:
    try:
        original_content = path.read_text(encoding="utf-8")
        modified_content = original_content
        while True:
            match = IF_BLOCK_REGEX.search(modified_content)
            if not match:
                break
            modified_content = modified_content[: match.start()] + modified_content[match.end() :]
        if original_content != modified_content:
            path.write_text(modified_content, encoding="utf-8")
            print(f"Cleaned: {path}")
    except Exception as e:
        print(f"Error processing {path}: {e}", file=sys.stderr)


def main() -> None:
    cwd = Path.cwd()
    files_to_process = get_nobinary(cwd)
    for item_path in files_to_process:
        if item_path.is_file():
            try:
                content = item_path.read_text(encoding="utf-8", errors="ignore")
                is_likely_bash = False
                if content.startswith(("#!/bin/bash", "#!/usr/bin/env bash")) or oct(item_path.stat().st_mode)[
                    -3:
                ] not in (
                    "000",
                    "001",
                    "010",
                    "011",
                    "002",
                    "012",
                    "100",
                    "110",
                    "111",
                    "101",
                ):
                    is_likely_bash = True
                if is_likely_bash:
                    remove_conditional_exit_blocks(item_path)
            except Exception as e:
                print(f"Could not read or process {item_path}: {e}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
