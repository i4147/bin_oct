#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script (intended to run under Termux on Android, so use the shebang `#!/data/data/com.termux/files/usr/bin/env python`) that cleans the output of `pip freeze` in place, leaving only the package names.

Requirements:

**Purpose:** Read a single text file produced by `pip freeze` and overwrite it so that it contains only one package name per line, with duplicates removed and original order preserved.

**Interface:**
- Use `argparse` with a description along the lines of "Clean pip freeze output and keep only package names (overwrite file)."
- Accept one required positional argument: the path to the pip freeze output file.
- Use `from __future__ import annotations` for type-hint compatibility.

**Input handling:**
- Convert the argument to a `pathlib.Path`. If the path is not an existing regular file, exit with a system exit (SystemExit) carrying an error message. Ensure the error message variable is properly defined before use so the program does not raise a NameError.
- Read the file as UTF-8 with `errors="ignore"` and split it into lines.

**Name extraction (per line), function `extract_package_name(line: str) -> str | None`:**
1. Strip surrounding whitespace.
2. Return None for empty lines and lines beginning with `#`.
3. Return None for lines starting with `git+`, `http://`, or `https://` (VCS and URL requirements are skipped).
4. If the line contains `@` (direct references like `name @ url`), take the text before the first `@`, strip it, and return it, or None if empty.
5. Otherwise, match a precompiled verbose regular expression (compiled at module level with `re.VERBOSE`) that: anchors at start, optionally allows a leading `-e` followed by whitespace, then captures a named group `name` made of letters, digits, underscores, dots, and hyphens. Return the captured name, or None if there is no match.

**Processing:**
- Apply extraction to every line, collect non-empty results in order.
- Deduplicate while preserving first-occurrence order (use a set for tracking seen names, in a concise idiom).

**Output:**
- Overwrite the same file with the cleaned names joined by newlines, with a single trailing newline, encoded as UTF-8.
- Write nothing else; no console output on success.

**Entry point:**
- Put the logic in a `main()` function returning None, and invoke it under `if __name__ == "__main__":` with `raise SystemExit(...)` wrapping the call so the process exits cleanly. The exit call must be valid and must not reference an undefined name.

**Style:** Use type hints, keep code concise and idiomatic, and include brief comments only where helpful.
---"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PKG_NAME_RE = re.compile(
    r"""
    ^\s*
    (?:
        -e\s+
    )?
    (?P<name>[A-Za-z0-9_.\-]+)
    """,
    re.VERBOSE,
)


def extract_package_name(line: str) -> str | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith(("git+", "http://", "https://")):
        return None
    if "@" in line:
        name = line.split("@", 1)[0].strip()
        return name or None
    match = PKG_NAME_RE.match(line)
    if match:
        return match.group("name")
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean pip freeze output and keep only package names (overwrite file)."
    )
    parser.add_argument("file", help="pip freeze output file")
    args = parser.parse_args()
    path = Path(args.file)
    if not path.is_file():
        raise SystemExit(msg)
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    packages = []
    for line in lines:
        name = extract_package_name(line)
        if name:
            packages.append(name)
    seen = set()
    cleaned = [p for p in packages if not (p in seen or seen.add(p))]
    path.write_text("\n".join(cleaned) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
