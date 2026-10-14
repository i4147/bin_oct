#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a user's local shared-library directory (the ".local/lib" folder inside the current user's home directory) and creates clean, unversioned symbolic links for versioned shared object files. The tool should first verify that the target directory exists and report a clear error message if it does not.
The script should discover all shared object files in that directory, including both plain ".so" files and versioned variants such as ".so.1" or ".so.1.2.3". It should process them in a stable, sorted order and skip any entries that are already symbolic links, as well as files whose names indicate minor or placeholder version suffixes (such as ending in ".0" or ".1") or other fully versioned forms that should not serve as the canonical entry point.
For each remaining library, the script should determine its base name by stripping trailing version numbers so that all versions of the same library map to a single common name (for example, "libfoo.so.1.2.3" maps to "libfoo.so"). Only the first encountered file for each base name should be used to create the link, so that no base name is processed more than once in a single run.
For each selected library, the script should resolve the real underlying file path and create a symbolic link named with the base name inside the same directory, pointing to the resolved real file. If a link or file with that name already exists, the script should handle it safely: it should replace an existing symbolic link that points elsewhere, leave a regular file untouched and report it, and avoid crashing on individual failures.
The script should print clear, concise progress messages for each link created, updated, or skipped, and a final summary of how many links were created, updated, and skipped. It should be robust to permission errors and missing files, continuing with the remaining libraries when one entry fails. It should run as a standalone command-line tool with no required arguments and should not modify anything outside the target directory.
---"""

from __future__ import annotations
import glob
import os
from pathlib import Path
import re


def should_skip(so_path):
    if so_path.is_symlink():
        return True
    name = so_path.name
    if name.endswith((".0", ".1")):
        return True
    return bool(re.search(r"\.so\.\d+(\.\d+)+$", name))


def get_base_name(so_path):
    name = so_path.name
    match = re.match(r"(.+\.so)(?:\.\d+)*$", name)
    if match:
        return match.group(1)
    return name


def create_symlinks():
    lib_dir = Path.home() / ".local" / "lib"
    if not lib_dir.exists():
        print(f"Error: {lib_dir} does not exist")
        return
    so_files = glob.glob(str(lib_dir / "*.so"))
    so_files.extend(glob.glob(str(lib_dir / "*.so.*")))
    processed_bases = set()
    for so_file in sorted(so_files):
        so_path = Path(so_file)
        if should_skip(so_path):
            continue
        abs_path = so_path.resolve()
        base_name = get_base_name(so_path)
        if base_name in processed_bases:
            continue
        processed_bases.add(base_name)
        for version in [".0", ".1"]:
            symlink_name = base_name + version
            symlink_path = lib_dir / symlink_name
            if symlink_path.is_symlink():
                target = os.readlink(symlink_path)
                if target == base_name or Path(target).resolve() == abs_path:
                    print(f"Exists: {symlink_path} -> {target} (correct)")
                    continue
                else:
                    symlink_path.unlink()
            elif symlink_path.exists():
                symlink_path.unlink()
            try:
                relative_path = base_name
                symlink_path.symlink_to(relative_path)
                print(f"Created: {symlink_path} -> {relative_path}")
            except Exception as e:
                print(f"Failed to create {symlink_path}: {e}")


if __name__ == "__main__":
    create_symlinks()
