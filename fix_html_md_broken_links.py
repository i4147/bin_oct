#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans the current working directory for documentation and web files (Markdown and HTML), and repairs broken hyperlink references within them. For each such file, the script should read its contents, identify every link target referenced in an HREF attribute, and check whether that target exists relative to the file's location. When a link target does not exist locally, the script should look for a matching file in a fixed shared static-assets directory on the device; if a matching file is found there, the link should be rewritten to point to that file's absolute path. Links that already resolve correctly, or that have no counterpart in the static directory, must be left untouched.
Before saving changes, the script should preserve the original file by renaming it with a backup extension, then write the corrected content back under the original filename using UTF-8 encoding, tolerating malformed bytes in the source. The tool should process every matching file it finds without requiring user interaction, run as a standalone command-line program, and exit cleanly upon completion. Focus on robust, safe batch processing that never loses the original content, and report nothing beyond what is necessary for a simple, unattended run.
---"""

from __future__ import annotations
import os
from pathlib import Path
import re

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
