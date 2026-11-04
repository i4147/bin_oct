#!/data/data/com.termux/files/usr/bin/env python

import os
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
                fullname = Path(self.directory) / file
                if Path(fullname).is_dir() and not Path(fullname).is_symlink():
                    self.stack.append(fullname)
                return fullname
        return None


if __name__ == "__main__":
    cwd = Path.cwd()
    for file in DirectoryWalker(str(cwd)):
        if Path(file).is_file() and file.endswith("README.pdf"):
            dirname1 = Path(file).parent
            full_name = file
            last_dir = dirname1.name
            new_name = last_dir + ".pdf"
            if not Path(new_name).exists():
                try:
                    Path(file).rename(dirname1 / new_name)
                    print(f"file {full_name} renamed to {new_name}")
                except OSError as e:
                    print(e)
