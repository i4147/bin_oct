#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that cleans up Python packaging build artifacts from the current working directory and its subdirectories. The tool should recursively scan the project tree and remove generated build leftovers, including build output folders, distribution folders, and common build target directories, as well as egg-info metadata directories and package metadata files left behind by packaging tools. It should also inspect configuration files named setup.cfg and remove only those that contain a specific, minimal egg_info configuration (an empty build tag and a zero date tag), leaving any other setup.cfg files untouched, so that user-authored configuration is never deleted. The script should report each removal to the user with a short, clear message identifying what was deleted, handle file reading safely (for example, tolerating files that cannot be decoded or are malformed), and avoid crashing when encountering unexpected or partially matching content. It should be designed to run as a standalone command-line utility that is safe to execute repeatedly, and should prioritize avoiding accidental deletion of source code or user data.
---"""

from __future__ import annotations
from pathlib import Path
import shutil

L1 = "[egg_info]"
L2 = "tag_build = "
L3 = "tag_date = 0"
SETUPCFG = """[egg_info]
tag_build =
tag_date = 0
"""


def is_setupcfg(fn: Path) -> bool:
    content = fn.read_text(encoding="utf8")
    if content == SETUPCFG:
        return True
    lines = content.splitlines(keepends=False)
    return bool(lines[0] == L1 and lines[1] == L2 and lines[2] == L3)


if __name__ == "__main__":
    cwd = Path.cwd()
    for item in cwd.rglob("*"):
        if item.is_dir() and item.name in ("build", "dist", "target"):
            shutil.rmtree(str(item))
            print(f"{item.name} removed.")
        if item.is_dir() and item.name.endswith("egg-info"):
            shutil.rmtree(str(item))
            print(f"{item.name} removed.")
        if item.is_file() and item.name == "PKG-INFO":
            item.unlink()
            print(f"{item.name} removed.")
        if item.is_file() and item.name == "setup.cfg" and is_setupcfg(item):
            item.unlink()
            print(f"{item.name} removed.")
