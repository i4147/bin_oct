#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that recursively walks the current working directory using a custom iterator-based DirectoryWalker class (which maintains a stack of directories and lazily lists files, pushing subdirectories for later traversal while skipping symlinked directories).
For every file found that is a regular file named "README.pdf", the script should rename it to match its parent directory's name with a ".pdf" extension, placing it in the same directory.
It should skip the rename if a file with the target name already exists, print a confirmation message showing the original and new file paths on success, and print the exception message if the rename operation fails due to an OSError."""

import os
from os.path import dirname as dirn
from os.path import isfile as isf
from os.path import join as jn
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
