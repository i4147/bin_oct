#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that sc of its subdirectories, looking for lines that define environment variables in the common `NAME=value` form, where the name consists only of uppercase letters, digits, and underscores and appears at the very start of the line. Collect each distinct variable name found across all readable text files, skipping any file that cannot be opened or decoded and reporting the problem without stopping the run. When the scan finishes, write the unique names to a text file named env_vars.txt, one name per line, sorted alphabetically. Finally, print a short summary to the console stating how many unique variable names were found and where they were saved.
---"""

from __future__ import annotations
from pathlib import Path
import re

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
