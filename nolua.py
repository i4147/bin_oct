#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that scans all subdirectories of the current working directory and uses a helper function from a custom "dh" module to detect whether each subdirectory contains any Lua (.lua) files.
For every subdirectory that does not contain Lua files, print its name prefixed with " - ".
Also include a helper function that moves a given plugin directory into the Vim start-plugins directory at "/data/data/com.termux/files/home/.vim/pack/plugins/start" (creating the destination if it doesn't exist) by copying the directory tree there and then deleting the original source directory.
"""

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
