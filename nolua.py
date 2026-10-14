#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the immediate subdirectories of the current working directory and checks each one for Lua source files (files with a .lua extension, searched recursively). For every subdirectory that contains no Lua files, the script should print its name in a simple bulleted list format. The script should also provide a way to relocate Lua-containing plugin directories: when a directory contains Lua files, it should be copied into a fixed Vim plugin location inside the Termux home directory (under a pack/plugins/start path, creating any missing parent folders as needed), and the original directory should then be removed after the copy completes. Handle the case where the destination already exists gracefully, skip non-directory entries, and ensure the script runs as a standalone program when executed directly, with clear, readable console output.
---"""

from __future__ import annotations
from pathlib import Path
from dh import get_files


def has_lua(root_dir):
    lua_files = []
    lua_files = get_files(root_dir, ext=[".lua"])
    return bool(lua_files)


def move_to_start(src):
    dest = "/data/data/com.termux/files/home/.vim/pack/plugins/start"
    if not Path(dest).exists():
        Path(dest).mkdir(exist_ok=True)
    import shutil

    target_path = f"{dest}/{src.name}"
    shutil.copytree(str(src), target_path)
    shutil.rmtree(src)


if __name__ == "__main__":
    cwd = Path.cwd()
    for dirpath in cwd.iterdir():
        if not dirpath.is_dir():
            continue
        if not has_lua(dirpath):
            print(f" - {dirpath.name}")
