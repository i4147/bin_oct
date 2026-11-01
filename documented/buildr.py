#!/data/data/com.termux/files/usr/bin/env python
"""buildr.py -- build a wheel for one package.

Changes into the package directory, runs ``python setup.py bdist_wheel`` and
reports failures per package.
"""

from __future__ import annotations

from os import chdir as os_chdir
from pathlib import Path

from dh import get_files, mpf, runcmd


def process_file(path_str: str) -> None:
    """Build a wheel for the package whose ``setup.py`` is given by *path_str*."""
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
