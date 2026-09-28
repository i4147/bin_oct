#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that takes a JSON file path as a command-line argument, reads and parses the file's contents, and converts all top-level keys to lowercase while preserving their values.
The script should then overwrite the original file with the modified data, using UTF-8 encoding, disabling ASCII-only output, and formatting the JSON with an indent of 2 spaces.
Finally, it should print a confirmation message indicating that the file was successfully updated."""

import json
import sys

input_file = sys.argv[1]
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)
lowercased_data = {key.lower(): value for key, value in data.items()}
with open(input_file, "w", encoding="utf-8") as f:
    json.dump(lowercased_data, f, ensure_ascii=False, indent=2)
print(f"Successfully updated {input_file}")
