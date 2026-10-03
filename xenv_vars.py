#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that recursively scans all files in the current directory tree (skipping any paths inside a .git folder) to detect environment variable declarations formatted as UPPERCASE_NAME=value at the start of a line.
For each file, it should read line by line with UTF-8 encoding, gracefully catching and printing any read errors without stopping the scan, and collect all unique matched variable names into a set.
Finally, it should write the sorted list of unique variable names, one per line, to an output file named env_vars.txt, and print a summary message showing how many unique variable names were found, handling any file-write errors gracefully as well."""

from __future__ import annotations

import builtins
import re
from pathlib import Path


def main():
    env_vars = set()
    env_var_pattern = re.compile(r"^([A-Z_0-9]+)=")
    for path in Path().rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_file():
            try:
                with builtins.open(path, encoding="utf-8") as f:
                    for line in f:
                        match = env_var_pattern.match(line)
                        if match:
                            env_vars.add(match.group(1))
            except Exception as e:
                print(f"Could not process file {path}: {e}")
    output_filename = "env_vars.txt"
    try:
        with builtins.open(output_filename, "w", encoding="utf-8") as f:
            f.writelines(var + "\n" for var in sorted(env_vars))
        print(f"Found {len(env_vars)} unique environment variable names. Saved to {output_filename}")
    except Exception as e:
        print(f"Could not write to output file {output_filename}: {e}")


if __name__ == "__main__":
    main()
