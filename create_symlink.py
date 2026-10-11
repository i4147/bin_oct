#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python 3 script for Termux (Android) with the following specification:

Create a small Python 3 utility script intended to run under Termux on Android, with the shebang line pointing to the Termux Python interpreter path (/data/data/com.termux/files/usr/bin/env python). The script should begin with a future annotations import so type hints are deferred, and use the standard library only (pathlib). No third-party dependencies.

Purpose: The script creates extensionless symlinks for executable script files, so they can be invoked by bare name from the shell. It scans two fixed directories in the user's home folder:
- ~/bashbin, looking for files ending in ".sh", and
- ~/bin, looking for files ending in ".py".

Define two module-level constants of type Path: one for the bashbin directory and one for the bin directory, both derived from the user's home directory via Path.home().

Implement a function that takes a directory Path and a file extension string (without the dot). It should:
- Iterate over files in that directory matching the glob pattern for that extension (non-recursive).
- For each matched file, resolve it to an absolute path with symlinks fully resolved.
- Compute the target symlink name as the file's name with the extension removed (the stem), placed in the same directory as the source file.
- Handle three cases:
  1. If a path already exists at the symlink location and it is a regular file or other non-symlink entry: remove it (unlink), then create a symlink at that location pointing to the source file's bare filename (relative, not absolute). Print a message in the form "Created: <link name> -> <source file name>". Then skip to the next file.
  2. If a symlink already exists at that location: do nothing silently and move on.
  3. If nothing exists at that location (or it is a broken state not covered above): create a relative symlink pointing to the source file's bare filename and print the same "Created: ..." message.

Note: the first two conditions are checked explicitly; the third covers the absence case. Symlinks are created with relative targets using only the filename, so they remain valid within the directory.

Main execution: only when run as the main program, call the function first for the bashbin directory with extension "sh", then for the bin directory with extension "py".

Behavior and edge cases to preserve:
- No explicit error handling is required beyond what naturally occurs; if a directory does not exist, the glob yields nothing and the script exits silently with no output.
- Files are processed in whatever order the glob returns them; no sorting is required.
- Output goes to standard output only, one line per created link.
- Do not recurse into subdirectories.
- Do not modify the source files themselves.
- Keep the script concise, with type hints on function signatures and a return type of None, and a clear, minimal style consistent with a small utility.

Deliver the complete script as a single file.
---"""

from __future__ import annotations

from pathlib import Path

BASHBIN: Path = Path.home() / "bashbin"
BIN: Path = Path.home() / "bin"


def process_dir(cwd: Path, ext: str) -> None:
    for path in cwd.glob(f"*.{ext}"):
        path = path.resolve()
        symlink_path = path.with_name(path.stem)
        if symlink_path.exists() and not symlink_path.is_symlink():
            symlink_path.unlink()
            symlink_path.symlink_to(path.name)
            print(f"Created: {symlink_path.name} -> {path.name}")
            continue
        if symlink_path.exists() and symlink_path.is_symlink():
            continue
        if not symlink_path.exists() or not symlink_path.is_symlink():
            symlink_path.symlink_to(path.name)
            print(f"Created: {symlink_path.name} -> {path.name}")


if __name__ == "__main__":
    process_dir(BASHBIN, "sh")
    process_dir(BIN, "py")
