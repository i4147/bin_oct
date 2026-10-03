#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that recursively scans every file under the current directory to detect environment variable assignment lines matching the pattern of an uppercase name followed by an equals sign (e.g., VAR_NAME=), extracting the variable name portion.
It should read each file as UTF-8 text, gracefully catch and print an error for any file that cannot be processed, and collect all unique matched variable names into a set.
Finally, it must write the sorted, unique variable names line by line to an output file named env_vars.txt and print a summary message stating how many unique environment variable names were found and saved."""

from __future__ import annotations

import re
from pathlib import Path

env_vars = set()
env_var_pattern = re.compile("^([A-Z_0-9]+)=")
for path in Path().rglob("*"):
    if path.is_file():
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    match = env_var_pattern.match(line)
                    if match:
                        env_vars.add(match.group(1))
        except Exception as e:
            print(f"Could not process file {path}: {e}")
output_filename = "env_vars.txt"
with open(output_filename, "w", encoding="utf-8") as f:
    f.writelines(var + "\n" for var in sorted(env_vars))
print(f"Found {len(env_vars)} unique environment variable names. Saved to {output_filename}")
