#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that converts a pip freeze output file into a JSON file mapping package names to their versions.
The function should accept an input file path (default "pip.freeze") and an output file path (default "packages.json"), read the input line by line, split each line on "==" to extract the package name and version, and store them in a dictionary.
It should then write this dictionary as indented JSON to the output file and print a confirmation message showing how many packages were saved.
The script should run this conversion automatically when executed as the main module."""

import json
from pathlib import Path


def freeze_to_json(
    input_file: str = "pip.freeze", output_file: str = "packages.json"
) -> None:
    packages = {}
    with Path(input_file).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "==" in line:
                pkg, ver = line.split("==", 1)
                packages[pkg] = ver
    with Path(output_file).open("w", encoding="utf-8") as f:
        json.dump(packages, f, indent=4)
    print(f"Saved {len(packages)} packages to {output_file}")


if __name__ == "__main__":
    freeze_to_json()
