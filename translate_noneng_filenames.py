#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans the current working directory (and all of its subfolders) for files whose names contain non-English characters, translates each such filename's base name (excluding the extension) into English using an online translation service, and renames the file accordingly. Files whose names are already plain ASCII/English should be left untouched. The script should process the deepest folders first so that renaming does not disrupt traversal of the directory tree.
Key requirements:
- Start from the directory where the script is run, with no required command-line input.
- Detect non-English filenames by checking whether the base name contains any non-ASCII characters; skip everything else.
- Translate the base name to English automatically, with the source language auto-detected and the target set to English. If translation fails, print a clear error message that includes the filename and keep the original name rather than crashing.
- Preserve each file's original extension and its location within its folder.
- Avoid overwriting existing files: if the translated name already exists in the same folder, append a numeric counter (e.g., "_1", "_2") until a free name is found.
- Print a readable log line for each rename showing the old and new names, and a final summary of how many files were renamed and how many failed.
- Handle errors gracefully so that a single failing file does not stop the entire process.
- Keep the implementation simple, dependency-light, and compatible with modern Python 3 versions.
---"""

from __future__ import annotations
import os
from pathlib import Path
import re
from deep_translator import GoogleTranslator

DIRECTORY = Path.cwd()
non_english_pattern = re.compile(r"[^\x00-\x7F]")


def is_english(text: str) -> bool:
    return not non_english_pattern.search(text)


def translate_filename(filename: str):
    try:
        return GoogleTranslator(source="auto", target="en").translate(filename)
    except Exception as e:
        print(f"Translation error for {filename}: {e}")
        return filename


def rename_files(directory: str) -> None:
    for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
        for name in filenames:
            path = Path(dirpath) / name
            if is_english(path.stem):
                continue
            original_path = path
            new_name = translate_filename(path.stem)
            new_path = path.with_stem(new_name)
            counter = 1
            while new_path.exists():
                _, ext = os.path.splitext(new_name)
                new_path = path.with_name(f"{new_name}_{counter}{ext}")
                counter += 1
            Path(original_path).rename(new_path)
            print(f"Renamed file: {original_path.name} -> {new_path.name}")
        for name in dirnames:
            path = Path(dirpath) / name
            if is_english(path.name):
                continue
            original_path = path
            new_name = translate_filename(path.name)
            new_path = path.with_name(new_name)
            counter = 1
            while new_path.exists():
                new_path = Path(f"{original_path}_{counter}")
                counter += 1
            Path(original_path).rename(new_path)
            print(f"Renamed directory: {original_path.name} -> {new_path.name}")


if __name__ == "__main__":
    rename_files(DIRECTORY)
