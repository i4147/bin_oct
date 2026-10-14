#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that operates on the immediate subdirectories of the current working directory, locating a Python wheel (.whl) package in each one and cleaning up everything else. For each subdirectory, the script should search for a wheel file either directly inside it or inside a nested "dist" folder. If a wheel is found outside the top level of the subdirectory (for example, in "dist"), the script should move it up to the subdirectory's root. After that, it should delete all other contents of the subdirectory, including nested folders and files, while preserving only the kept wheel file; symbolic links should be removed as links rather than followed. If no wheel exists in a subdirectory, the script should report that the folder was skipped and leave it untouched. The script should print clear, human-readable status messages for each action taken: moving a wheel, removing an item, completing a folder with the wheel retained, or skipping a folder. It should handle the top-level iteration by considering only directories (not regular files) within the current working directory, and it should process each one independently so that an issue with one folder does not prevent the others from being cleaned. The goal is a simple, safe utility for normalizing a set of build or download folders so that each one contains exactly one wheel file at its root.
---"""

from __future__ import annotations
from pathlib import Path
import shutil


def find_whl(subdir: Path):
    for location in (subdir, subdir / "dist"):
        if location.is_dir():
            for whl in location.glob("*.whl"):
                return whl
    return None


def clean_subdir(subdir: Path) -> None:
    whl = find_whl(subdir)
    if whl is None:
        print(f"[skip]  {subdir.name}: no .whl file")
        return
    target = subdir / whl.name
    if whl.parent != subdir:
        shutil.move(str(whl), str(target))
        print(f"[move]  {whl.relative_to(subdir)} -> {target.name}")
    for entry in subdir.iterdir():
        if entry.resolve() == target.resolve():
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()
        print(f"[rm]    {subdir.name}/{entry.name}")
    print(f"[done]  {subdir.name}: kept {target.name}")


def main() -> None:
    cwd = Path.cwd()
    subdirs = [p for p in cwd.iterdir() if p.is_dir() and not p.name.startswith(".")]
    if not subdirs:
        print("No top-level subdirectories found.")
        return
    for subdir in subdirs:
        clean_subdir(subdir)


if __name__ == "__main__":
    main()
