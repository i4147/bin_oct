#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that recursively scans the current working directory for `.whl` files and checks each one to determine whether it is "empty," meaning its ZIP contents contain no `.py`, `.so`, or `.pyi` files.
For each wheel,raises BadZipFile), print a warning and treat it as not empty.
After scanning, print the total count of empty wheels found, create an `empty_wheels` subdirectory in the current directory if needed, print each empty wheel's relative path, and move it into that subdirectory; if none are found, print a message stating so.
Structure the code with a helper function `is_empty_wheel` returning `bool | None` and a `main` function, and run `main` via `raise SystemExit(main())` in the `__main__` block.
"""

from __future__ import annotations
import zipfile
from pathlib import Path


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
