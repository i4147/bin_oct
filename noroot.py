#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script with these characteristics:

Build a Termux-targeted Python 3 command-line utility (shebang pointing to the Termux Python interpreter path) that cleans up shell scripts in the current working directory. It should use `from __future__ import annotations` and standard-library modules only, plus one project-local helper module named `dh` that exposes a function `get_nobinary(directory)` returning an iterable of `Path` objects; the agent should assume that helper exists and import it rather than reimplement it.

The script should define a compiled, multiline, case-insensitive regular expression that matches a bash-style conditional block of this shape: an `if` line testing whether a command substitution's output is not equal to zero (written with the `[ $(command) -ne 0 ]; then` form), followed by any body lines, then a line containing only `exit 1`, then arbitrary trailing content, terminated by a line starting with `fi`. The regex must use non-greedy matching and MULTILINE anchoring so that it removes the whole block from the `if` line through the `fi` line. Describe the pattern's intent in words; do not paste it.

Provide a function `remove_conditional_exit_blocks(path)` that reads the file as UTF-8, repeatedly searches for and splices out every match (re-searching from the start after each removal until none remain), and writes the file back as UTF-8 only if the content changed, printing `Cleaned: <path>` on success. Wrap the whole operation in a try/except that reports any exception to stderr in the form `Error processing <path>: <error>` without aborting the program.

Provide a `main()` function that takes the current working directory, calls `get_nobinary` on it, and iterates over the results. For each entry that is a regular file, read its content as UTF-8 with errors ignored, and decide whether it is a bash script by checking whether the content begins with a bash shebang (either `#!/bin/bash` or `#!/usr/bin/env bash`) or whether the file's permission bits, read via the file's stat mode, are NOT among a set of specific octal permission values (the last three octal digits of the mode are compared against a tuple of allowed values). Only files judged likely to be bash scripts should be passed to `remove_conditional_exit_blocks`. Skip directories and non-files silently. Handle per-file errors defensively so one bad file does not stop processing of the rest.

Include an entry guard (`if __name__ == "__main__":`) that calls `main()`. Use type hints throughout, `pathlib` for file handling, and `sys.stderr` for error output. Keep the code concise, with minimal comments, and make no assumptions about output beyond the printed messages described above. The script is run from within the directory whose shell scripts should be cleaned, with no command-line arguments.

Note for the agent: the exact regex and the exact permission-value tuple should be reproduced faithfully from the original source, which the agent will be given separately; match the described behavior precisely.
---"""

from __future__ import annotations

import re
import sys
from pathlib import Path

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
