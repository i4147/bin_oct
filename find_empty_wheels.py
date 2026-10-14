#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory and all of its subdirectories forwhl), identifies which wheels contain no Python source or compiled extension content, and moves those "empty" wheels into a single dedicated folder named "empty_wheels" created in the working directory.
The script should treat a wheel as "empty" when its archive contains no files with Python source, compiled extension, or Python stub extensions. If a file is not a valid ZIP archive, the script should print a clear warning naming that file, skip it, and not treat it as empty.
Behavior requirements:
- Search recursively from the current directory for every wheel file, considering only actual files.
- Evaluate each wheel and collect the list of empty ones without modifying anything during evaluation.
- If empty wheels are found, print a summary line stating how many were found, then list each wheel's path relative to the current directory, and move each one into the "empty_wheels" folder, creating that folder if it does not already exist.
- If no empty wheels are found, print a message stating so.
- Keep output concise and user-friendly, and make the script runnable as a standalone command-line program with a main entry point.
Focus on clean, readable, robust code that handles filesystem and archive errors gracefully.
---"""

from __future__ import annotations
from pathlib import Path
import zipfile


def is_empty_wheel(whl_path: Path) -> bool | None:
    try:
        with zipfile.ZipFile(whl_path, "r") as zf:
            for name in zf.namelist():
                if name.lower().endswith((".py", ".so", ".pyi")):
                    return False
    except zipfile.BadZipFile:
        print(f"Warning: {whl_path} is not a valid ZIP file. Skipping.")
        return False
    return True


def main() -> None:
    empty_wheels = []
    cwd = Path.cwd()
    target = cwd / "empty_wheels"
    for whl in cwd.rglob("*.whl"):
        if whl.is_file():
            is_empty = is_empty_wheel(whl)
            if is_empty:
                empty_wheels.append(whl)
    if empty_wheels:
        print(f"\nFound {len(empty_wheels)} empty wheel(s).")
        target.mkdir(exist_ok=True)
        for k in empty_wheels:
            print(k.relative_to(cwd))
            new_path = target / k.name
            k.rename(new_path)
    else:
        print("No empty wheels found.")


if __name__ == "__main__":
    raise SystemExit(main())
