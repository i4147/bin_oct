#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that recursively walks through all files and folders in the current working directory (using a fast file-walking utility) and detects filenames or directory names containing non-ASCII characters via a regex check.
For each non-English name found, it should translate it into English using the deep_translator GoogleTranslator (auto-detect source language), preserving file extensions, and rename the file or folder accordingly.
It must handle naming collisions by appending an incrementing numeric suffix until a unique path is found, gracefully catch and log translation errors while keeping the original name as fallback, and print a message for each successful rename showing the old and new names."""

from __future__ import annotations
import os
import re
from pathlib import Path
from deep_translator import GoogleTranslator
from fastwalk import walk_files

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
    for path in walk_files(directory):
        if is_english(path.stem):
            continue
        if path.is_file():
            original_path = path
            new_name = translate_filename(path.stem)
            new_path = path.with_stem(new_name)
            counter = 1
            while new_path.exists():
                name, ext = os.path.splitext(new_name)
                new_path = path.with_name(f"{name}_{counter}{ext}")
                counter += 1
            Path(original_path).rename(new_path)
            print(f"Renamed file: {original_path.name} -> {new_path.name}")
        elif path.is_dir():
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
