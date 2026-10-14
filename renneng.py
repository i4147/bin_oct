#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans a target directory (defaulting to the current directory) and renames files whose base names contain non-ASCII characters, such as Chinese, Japanese, or other non-English text. For each such file, the script should translate the filename's base name into English using an automatic language-detection translation service, while preserving the original file extension. If translation fails for any file, the script should report the error in a clear message and keep the original name without interrupting the rest of the process.
The script should be safe with respect to existing files: if the translated name would collide with a file already present in the same folder, it must append a numeric suffix (such as _1, _2, and so on) to create a unique name rather than overwriting anything. Filenames that are already pure ASCII should be left untouched. The script should process all subdirectories, handle deeper folders before their parents so that renaming does not disrupt traversal, and print a readable log of every rename performed, along with any errors encountered.
The output is the renamed files on disk plus console feedback summarizing the actions taken. Prioritize robustness, clear reporting, and non-destructive behavior, and feel free to choose any suitable approach for the implementation.
---"""

from __future__ import annotations
import os
from pathlib import Path
import re
from deep_translator import GoogleTranslator

DIRECTORY = "."
non_english_pattern = re.compile(r"[^\x00-\x7F]")


def translate_if_needed(name: str) -> str:
    base, ext = os.path.splitext(name)
    if not non_english_pattern.search(base):
        return name
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(base)
        return translated + ext
    except Exception as e:
        print(f"Translation error for '{name}': {e}")
        return name


def get_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    base = path.stem
    ext = path.suffix
    parent = path.parent
    counter = 1
    while True:
        new_path = parent / f"{base}_{counter}{ext}"
        if not new_path.exists():
            return new_path
        counter += 1


def rename_files(directory: str) -> None:
    for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
        for name in filenames:
            path = Path(dirpath) / name
            new_name = translate_if_needed(path.name)
            if new_name == path.name:
                continue
            new_path = path.parent / new_name
            new_path = get_unique_path(new_path)
            Path(path).rename(new_path)
            print(f"File renamed: {path.name} -> {new_path.name}")
        for name in dirnames:
            path = Path(dirpath) / name
            new_name = translate_if_needed(path.name)
            if new_name == path.name:
                continue
            new_path = path.parent / new_name
            new_path = get_unique_path(new_path)
            Path(path).rename(new_path)
            print(f"Directory renamed: {path.name} -> {new_path.name}")


if __name__ == "__main__":
    rename_files(DIRECTORY)
