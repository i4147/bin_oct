#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that cleans up installed Python package metadata directories (the ".dist-info" folders inside a site-packages location) to reduce disk usage by removing non-essential files. The script should accept a target directory (such as a Python environment's site-packages folder), locate every installed package metadata folder within it, and selectively delete files that are not needed at runtime. Keep only core metadata files such as the package description, file manifest, wheel information, and top-level module listing. Remove other extras such as installer markers, requested-install flags, direct URL records, and a wide range of license, copyright, author, and notice files, including common variants with different extensions and capitalizations. In addition, detect any licenses subdirectory inside a metadata folder and remove it entirely, but only when it sits within a folder whose name identifies it as distribution metadata. Report each removal to the user with a clear message, handle missing or already-cleaned directories gracefully, and avoid touching anything outside package metadata folders. The script should be safe to run repeatedly, provide a summary of how many files and directories were removed, and display the Python version it is running under at startup. Use the standard console output and rely on the project's existing helper utilities for colored or formatted printing where appropriate.
---"""

from __future__ import annotations
from pathlib import Path
import shutil
import sys
from dh import cprint

major, minor, _, _, _ = sys.version_info
py_version = f"{major}.{minor}"
ALLOWED = ["METADATA", "RECORD", "WHEEL", "top_level.txt"]
NOT_ALLOWED = [
    "REQUESTED",
    "INSTALLER",
    "direct_url.json",
    "AUTHORS",
    "AUTHORS.md",
    "AUTHORS.rst",
    "AUTHORS.txt",
    "BSD-0-Clause.rst",
    "BSD-2-Clause.rst",
    "CONTRIBUTORS.txt",
    "COPYING",
    "COPYING.GPL",
    "COPYING.LESSER",
    "COPYING.LGPL",
    "COPYING.MPL",
    "COPYING.rst",
    "COPYING.txt",
    "DESCRIPTION.rst",
    "LICENCE",
    "LICENCE.rst",
    "LICENSE",
    "LICENSE-APACHE",
    "LICENSE.APACHE2",
    "LICENSE.markdown-it",
    "LICENSE.md",
    "LICENSE.rst",
    "LICENSE.txt",
    "LICENSE_numpy.txt",
    "LICENSE_scipy.txt",
    "NOTICE",
    "NOTICE.txt",
    "gpl-3-0.txt",
    "pbr.json",
    "toplevel.txt",
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
]


def process_lic(path: Path) -> None:
    lic_dir = path / "licenses"
    if lic_dir.exists() and "dist-info" in lic_dir.parent.name:
        shutil.rmtree(lic_dir)
        print(f"{lic_dir} removed.")
    for k in NOT_ALLOWED:
        nap = path / k
        if nap.exists():
            print(nap)
            nap.unlink()


def main() -> None:
    cwd = Path.cwd()
    for path in cwd.rglob("*"):
        if path.is_dir() and "dist-info" in path.name:
            process_lic(path)
            if len(list(path.iterdir())) < 2:
                cprint(f"{path.name} empty pkg", "cyan")


if __name__ == "__main__":
    raise SystemExit(main())
