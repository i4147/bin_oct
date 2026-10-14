#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively walks through a given starting directory and lazily yields the full path of every file and subdirectory it encounters, traversing into subdirectories without following symbolic links. The script should be designed to be iterated over in a memory-efficient manner, producing paths one at a time rather than loading the entire directory tree into memory at once. It should begin its traversal from the current working directory when run as a standalone program, and for each path it finds, it should check whether the entry is a regular file and whether its name ends with a specific file extension supplied by the user (for example, ".txt" or ".py"). Only matching files should be reported, and the script should print their full paths to the console. The script should handle directories that cannot be read gracefully, without crashing, and should be structured so that the directory-walking logic is reusable as a component in other programs.
---"""

from __future__ import annotations
import os
from os.path import (
    dirname as dirn,
    isfile as isf,
    join as jn,
)
from pathlib import Path


class DirectoryWalker:
    def __init__(self, directory) -> None:
        self.stack = [directory]
        self.files = []
        self.index = 0

    def __getitem__(self, index):
        while 1:
            try:
                file = self.files[self.index]
                self.index = self.index + 1
            except IndexError:
                self.directory = self.stack.pop()
                self.files = os.listdir(self.directory)
                self.index = 0
            else:
                fullname = jn(self.directory, file)
                if os.path.isdir(fullname) and not os.path.islink(fullname):
                    self.stack.append(fullname)
                return fullname
        return None


if __name__ == "__main__":
    cwd = Path.cwd()
    for file in DirectoryWalker(str(cwd)):
        if isf(file) and file.endswith("README.pdf"):
            dirname1 = dirn(file)
            full_name = file
            dirs = dirname1.split("/")
            last_dir = dirs[len(dirs) - 1]
            new_name = last_dir + ".pdf"
            if not os.path.exists(new_name):
                try:
                    os.rename(file, jn(dirname1, new_name))
                    print(f"file {full_name} renamed to {new_name}")
                except OSError as e:
                    print(e)
