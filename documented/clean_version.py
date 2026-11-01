#!/data/data/com.termux/files/usr/bin/env python
"""clean_version.py -- reduce ``pip freeze`` output to bare package names.

The version pins, markers and extras are dropped and the file is overwritten in
place.
"""

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
    """Return the package name of one ``pip freeze`` line.

    Lines that are direct URL or git references yield ``None``; a name is taken from a
    ``#egg=`` or ``name=`` fragment.
    """
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
    """Print the package names of a ``pip freeze`` output file."""
    parser = argparse.ArgumentParser(
        description="Clean pip freeze output and keep only package names (overwrite file)."
    )
    parser.add_argument("file", help="pip freeze output file")
    args = parser.parse_args()
    path = Path(args.file)
    if not path.is_file():
        raise SystemExit(f"Not a file: {path}")
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
