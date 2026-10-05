#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that compares the current working directory against a target directory provided as a command-line argument, recursively examining all files and subdirectories for differences.
It should use the filecmp module's dircmp class to perform the comparison, then call report_full_closure to generate a full recursive comparison report covering the entire directory tree.
The resulting comparison output should be printed to the console using pprint for readable formatting."""

from __future__ import annotations
import sys
from filecmp import dircmp
from pathlib import Path
from pprint import pprint

if __name__ == "__main__":
    dir1 = Path.cwd()
    dir2 = Path(sys.argv[1])
    c = dircmp(dir1, dir2)
    pprint(c.report_full_closure())
