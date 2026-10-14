#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively discovers every Python project in the current working directory tree by locating its packaging configuration file, builds a wheel distribution for each project in parallel, reports any build failures, and then lists all wheel artifacts that were produced.
The script should:
- Start from the directory where it is executed and search all naging configuration files (files named exactly as the standard Python setup script).
- For each discovered project, change into the project's own directory and run the standard command that produces a wheel package, treating a non-zero exit status as a build failure.
- Process multiple projects concurrently to reduce total build time, and make sure each project is built in its own directory context without interfering with the others.
- Print a clear error message identifying the specific project whose wheel build failed, while allowing the remaining projects to continue building.
- After all builds have finished, search the starting directory tree for generated wheel files and print the full path of each one found, or indicate clearly if none were found.
- Run as a standalone command-line program with its entry point guarded so it only executes when launched directly.
- Use only the standard library or simple, widely available tooling, and keep the solution concise and readable, with a short explanation of its behavior in comments or docstrings.
---"""

from __future__ import annotations
from os import chdir as os_chdir
from pathlib import Path
from dh import get_files, mpf, runcmd


def process_file(path_str: str) -> None:
    path = Path(path_str)
    os_chdir(path.parent)
    cmd = ["python", "setup.py", "bdist_wheel"]
    ret, _, _ = runcmd(cmd)
    if ret != 0:
        print(f"Error building wheel for {path}")


if __name__ == "__main__":
    cwd = Path.cwd()
    files = get_files(cwd)
    targets = [str(path) for path in files if path.name == "setup.py"]
    mpf(process_file, targets)
    whl_files = get_files(cwd, ext=[".whl"])
    if whl_files:
        for k in whl_files:
            print(k)
