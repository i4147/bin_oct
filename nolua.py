#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt for an AI coding agent to recreate a Termux-targeted Python utility that scans the current directory's subdirectories, reports those without Lua files, and provides a helper to move a directory into the Vim plugin "start" folder. Build a prompt that covers purpose, inputs and outputs, dependencies, logic, error handling, edge cases, and usage, without including any code.

Create a Python 3 script for Termux (Android) that inspects the immediate subdirectories of the current working directory and reports which ones contain no Lua source files. It also includes a helper function that moves a directory into the user's Vim native packages "start" folder.

**Shebang and encoding:** Begin the file with the Termux-specific Python interpreter shebang (`/data/data/com.termux/files/usr/bin/env python`). Use `from __future__ import annotations` at the top.

**Dependencies:**
- Standard library: `pathlib.Path`, `shutil` (import it inside the helper function, not at module top level).
- A third-party/local helper module named `dh` that exposes a function `get_files(root_dir, ext=[...])`, which returns a list of file paths under `root_dir` whose extensions match the given list. Import it as `from dh import get_files`. Do not reimplement it; assume it exists.

**Function 1: `has_lua(root_dir)`**
- Calls `get_files(root_dir, ext=[".lua"])` to collect Lua files recursively under `root_dir`.
- Returns `True` if the resulting list is non-empty, otherwise `False` (return a boolean via `bool(...)`).
- Initialize the result variable to an empty list before assigning the call result (keep this slightly redundant style).

**Function 2: `move_to_start(src)`**
- `src` is a `Path` object for a directory.
- Destination base is the fixed absolute path `/data/data/com.termux/files/home/.vim/pack/plugins/start`.
- If the destination base directory does not exist, create it with `mkdir(exist_ok=True)`. Note: this uses a non-recursive mkdir, so parent directories must already exist; do not add `parents=True` unless noted.
- Build the target path as the destination base joined with `src.name` (the directory's basename), as a string.
- Copy the entire source directory tree to the target using `shutil.copytree(str(src), target_path)`. Note that `copytree` raises an error if the target already exists; let that exception propagate (no special handling).
- After a successful copy, delete the original source directory with `shutil.rmtree(src)`. This is a move-by-copy-then-delete, not an atomic rename.
- The function returns nothing.

**Main block (`if __name__ == "__main__":`)**
- Get the current working directory via `Path.cwd()`.
- Iterate over `cwd.iterdir()` (immediate children only, not recursive).
- Skip any entry that is not a directory (use `is_dir()`), via `continue`.
- For each directory, call `has_lua(dirpath)`. If it returns `False` (no Lua files), print a line in the exact format: a space, a hyphen, a space, then the directory's name (only the name, not the full path). Example output form: ` - dirname`.
- Directories that contain Lua files are silently skipped.
- The main block only reports; it does NOT call `move_to_start` by default. The move helper is available for import/use elsewhere or can be wired in by the user. Do not invoke it in the main block.

**Behavior and edge cases to preserve:**
- Only immediate subdirectories of the current directory are examined; hidden directories (e.g., starting with a dot) are not specially excluded and will be checked too.
- Symlinks to directories are treated as directories by `is_dir()` and will be scanned.
- Directory scanning depth is delegated entirely to `get_files`; the script does not implement its own traversal.
- No command-line arguments are parsed; the script takes no input other than the current working directory.
- Output goes to standard output only; no logging module, no file writes except via the move helper.
- No explicit try/except blocks; errors (permission issues, missing `dh` module, copy conflicts, missing destination parents) propagate as uncaught exceptions.
- Use Path methods and `f-strings` where appropriate, but keep the code minimal and close in style to a short utility script.

**Output requirement:** Produce a single complete Python file that matches this behavior exactly, with no extra features, no added CLI flags, no logging, and no additional error handling beyond what is described.
---"""

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
