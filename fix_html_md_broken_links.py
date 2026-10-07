#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that recking for all ".md" and ".html" files,racts href-style links using a regular expression.
For every extracted link that does not exist as a valid relative path, the script checks whether a matching file exists under a fixed static assets directory ("/sdcard/_static"), and if so, replaces the broken link in the file content with the resolved absolute path to that static file.
Before writing changes, it renames the original file to a ".bak" backup, then writes the updated content back to the original filename.
The script should run as a standalone program invoked via a main function and exit with its return status."""

from __future__ import annotations
import os
import re
from pathlib import Path

static_dir = "/sdcard/_static"


def fix_links(path: Path) -> None:
    content: str = path.read_text(encoding="utf-8", errors="replace")
    links = re.findall(r"href=[\'\"]?([^\'\" >]+)", content)
    for link in links:
        if not Path(link).exists():
            static_file = static_dir / link
            if static_file.exists():
                content = content.replace(link, str(static_file.resolve()))
    backup_path = path.with_suffix(".bak")
    Path(path).replace(backup_path)
    Path(path).write_text(content, encoding="utf-8")


def main() -> None:
    for root, _dirs, files in os.walk("."):
        for file in files:
            if file.endswith((".md", ".html")):
                path = Path(root) / file
                fix_links(path)


if __name__ == "__main__":
    raise SystemExit(main())
