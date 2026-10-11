#!/data/data/com.termux/files/usr/bin/env python
"""Write a single self-contained Python script (Termux-style shebang for `/data/data/com.termux/files/usr/bin/env python`, with `from __future__ import annotations`) that sorts Python files in the current working directory by Black formatting status. It should:

**Purpose:** Scan the current directory for `*.py` files (non-recursive), run `black --check` on each, and move each file into one of two subdirectories: `ok/` if Black reports it is already formatted, or `error/` if it is not. The script itself must be skipped, identified by comparing the file name against the running script's own name.

**Setup:**
- Define the two directory names as relative `Path` constants: `error` and `ok`.
- Before processing, create both directories if they don't exist, without failing if they already exist.

**Destination handling:**
- Write a helper that returns a destination path unchanged if nothing exists there.
- If the destination already exists, append an incrementing counter before the extension in the form `<stem>_<n>.py`, starting at 1, and return the first unused name. This prevents overwriting files that share a name.

**Formatting check:**
- Write a helper that runs the external `black` command as `black --check <path>` via `subprocess.run`, capturing output so nothing is printed from Black itself.
- Return `True` only when the exit code is 0; any other code (including formatting-needed) returns `False`.
- Assume `black` is available on the PATH; do not add installation logic.

**Main flow:**
- Call the directory setup first.
- Iterate over every `*.py` file in the current directory, skipping the script's own file.
- For each file, print a line like `Checking <file>...`.
- If Black passes, compute a unique destination in `ok/` and print a success line with a check mark and an arrow showing the destination.
- Otherwise, compute a unique destination in `error/` and print a failure line with a cross mark and an arrow showing the destination.
- Move the file to the computed destination with `shutil.move`, converting paths to strings.

**Entry point:**
- Run `main` under the standard `__main__` guard and exit via `raise SystemExit(main())`.
- Use type hints throughout, with `-> None` on the functions.

**Notes and edge cases:**
- Only the top-level directory is scanned; subdirectories and non-`.py` files are ignored.
- The script moves files, so it is destructive to the file's location; it performs no backups.
- If `black` is not installed, `subprocess.run` will raise an exception, which is not caught; the script will terminate with a traceback.
- Output uses Unicode symbols (check mark, cross, arrow), so the terminal must support UTF-8.
- Code style should be concise and idiomatic, with simple `pathlib` and `subprocess` usage and no third-party dependencies beyond the Black CLI.
---"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ERROR_DIR = Path("error")
OK_DIR = Path("ok")


def ensure_dirs() -> None:
    ERROR_DIR.mkdir(exist_ok=True)
    OK_DIR.mkdir(exist_ok=True)


def unique_destination(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    counter = 1
    while True:
        new_dest = parent / f"{stem}_{counter}{suffix}"
        if not new_dest.exists():
            return new_dest
        counter += 1


def black_check(path: Path) -> bool:
    result = subprocess.run(["black", "--check", str(path)], capture_output=True)
    return result.returncode == 0


def main() -> None:
    ensure_dirs()
    for py_file in Path().glob("*.py"):
        if py_file.name == Path(__file__).name:
            continue
        print(f"Checking {py_file}...")
        if black_check(py_file):
            dest = unique_destination(OK_DIR / py_file.name)
            print(f"  ✓ OK → {dest}")
        else:
            dest = unique_destination(ERROR_DIR / py_file.name)
            print(f"  ✗ ERROR → {dest}")
        shutil.move(str(py_file), str(dest))


if __name__ == "__main__":
    raise SystemExit(main())
