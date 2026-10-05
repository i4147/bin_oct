#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that scans the current directory for all files with a .json extension, treating each as PyPI package metadata.
For each file, it should parse the JSON and extract the package name, checking either the "info.name" field or a top-level "name" field, then rename the file to "{package_name}.json" if it differs from the current filename.
The script should print a status message for each file indicating whether it was renamed, already correctly named, or skipped due to a missing package name, and it must gracefully handle and report invalid JSON files or other exceptions without stopping execution on the remaining files."""

from __future__ import annotations
import json
import os
from pathlib import Path


def rename_pypi_metadata_files() -> None:
    files = [f for f in os.listdir(".") if f.endswith(".json")]
    for filename in files:
        try:
            with Path(filename).open(encoding="utf-8") as f:
                data = json.load(f)
            pkg_name = None
            if "info" in data and "name" in data["info"]:
                pkg_name = data["info"]["name"]
            elif "name" in data:
                pkg_name = data["name"]
            if pkg_name:
                new_name = f"{pkg_name}.json"
                if filename == new_name:
                    print(f"Skipping: {filename} is already correctly named.")
                    continue
                Path(filename).rename(new_name)
                print(f"Renamed: {filename} -> {new_name}")
            else:
                print(f"Warning: Could not find package name in {filename}")
        except json.JSONDecodeError:
            print(f"Error: {filename} is not a valid JSON file.")
        except Exception as e:
            print(f"An error occurred with {filename}: {e}")


if __name__ == "__main__":
    rename_pypi_metadata_files()
