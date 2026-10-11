#!/data/data/com.termux/files/usr/bin/env python
"""Write a complete, self-contained Python script that recursively scans the current working directory for environment variable assignments and writes the unique variable names to a text file. Specification:

**Purpose:** Walk every file under the current directory (recursively, including subdirectories) and collect the names of environment variables that appear as assignments at the start of a line, in the form `NAME=...`, where NAME consists only of uppercase letters, digits, and underscores. Write the unique names, sorted alphabetically, one per line, to a file named `env_vars.txt` in the current working directory. Then print a summary line stating how many unique names were found and where they were saved.

**Requirements and behavior:**

- Use only the Python standard library. Start the script with a Termux-compatible shebang line pointing to the Termux Python interpreter (`/data/data/com.termux/files/usr/bin/env python`). Include `from __future__ import annotations` at the top.
- Use `re` to compile a pattern anchored at the start of the line that matches one or more uppercase letters, digits, or underscores followed by an equals sign, capturing the name group. Match only at the beginning of each line; do not match names appearing mid-line or lowercase names.
- Use `pathlib.Path` to recursively enumerate all entries from the current directory with a `**/*`-style glob pattern (equivalent to `rglob("*")`), and process only entries that are regular files (skip directories and other non-file entries).
- Open each file with UTF-8 encoding and read it line by line. For each line, apply the pattern and add the captured name to a set so duplicates are removed.
- Wrap the processing of each file in a try/except block catching `Exception`. On failure (for example, binary files that cannot be decoded, permission errors), print a message in the form `Could not process file <path>: <error>` and continue with the next file rather than aborting.
- Store the results in a set. After scanning, write to `env_vars.txt` (opened in write mode with UTF-8 encoding), emitting each name in sorted order followed by a newline. Use a generator expression with `writelines` or an equivalent approach. Overwrite any existing file of that name.
- After writing, print exactly one summary message in the form: `Found <N> unique environment variable names. Saved to env_vars.txt`, where N is the size of the set.
- Do not accept command-line arguments, prompts, or configuration; the script operates entirely on the current working directory and the fixed output filename.
- Edge cases: an empty directory or no matching lines should produce an empty `env_vars.txt` and a summary reporting zero names. The output file itself may be present during the scan; it is acceptable that it is read like any other file. Files are scanned in whatever order the filesystem yields them, but output is always sorted.
- Keep the script short and procedural, with no classes or functions required, and with a top-level flow that matches the description above.
- Note for reproduction: the script is intended to be run from the root of a project directory (e.g., `python <script>.py` from that directory), and it may be slow on very large trees because it reads every file in full line by line.
---"""

from __future__ import annotations

import re
from pathlib import Path

env_vars = set()
env_var_pattern = re.compile("^([A-Z_0-9]+)=")
for path in Path().rglob("*"):
    if path.is_file():
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    match = env_var_pattern.match(line)
                    if match:
                        env_vars.add(match.group(1))
        except Exception as e:
            print(f"Could not process file {path}: {e}")
output_filename = "env_vars.txt"
with open(output_filename, "w", encoding="utf-8") as f:
    f.writelines(var + "\n" for var in sorted(env_vars))
print(f"Found {len(env_vars)} unique environment variable names. Saved to {output_filename}")
