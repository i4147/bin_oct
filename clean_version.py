#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that cleans up the output of a pip freeze dependency listing, reducing each entry to just its bare package name. The script should accept a single command-line argument giving the path to an existing text file containing pip freeze output. If the file does not exist, it should exit with a clear error message rather than failing with a stack trace.
The script should read the file as text (tolerating encoding issues), then process each line as follows:
- Ignore blank lines and comment lines (those beginning with a hash symbol).
- Skip lines that are direct VCS or URL references (such as entries beginning with git+, http://, or https://), since they do not map to a simple package name.
- For direct references in the form "name @ location", keep only the package name before the at sign.
- For standard version specifiers (such as "name==1.2.3", "name>=2.0", or editable-install lines prefixed with "-e"), extract only the package name portion, which may contain letters, digits, underscores, dots, and hyphens.
- Discard any line from which no valid package name can be determined.
After processing, the script should overwrite the original file so that it contains only the extracted package names, one per line, preserving the original order and keeping duplicates removed or retained in a consistent, sensible way. The script should be runnable from the command line with a short description in its help text explaining that it cleans pip freeze output in place, keeping only package names.
Focus on producing a robust, dependency-free, readable tool that handles edge cases in pip freeze output gracefully, and make sure the final file ends with a trailing newline.
---"""

from __future__ import annotations
import argparse
from pathlib import Path
import re

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
