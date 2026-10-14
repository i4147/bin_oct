#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a JSON file path as a command-line argument, loads the JSON dictionary it contains, inverts the mapping so that each original value becomes a key pointing back to its original key, and overwrites the same file with the resulting inverted dictionary. The output file should be human-readable, preserve non-ASCII characters without escaping, use two-space indentation, and have its keys sorted alphabetically. Upon completion, the script should print a short confirmation message such as "done". The reversal logic should rely on a helper function from a separate module that the script imports; the script itself should only handle reading the input, invoking the reversal, writing the result back, and reporting completion.
---"""

from __future__ import annotations
import json
import sys
from dh import reverse_dict

if __name__ == "__main__":
    fn = sys.argv[1]
    with open(fn, encoding="utf-8") as f:
        data = json.load(f)
    revdict = reverse_dict(data)
    with open(fn, "w", encoding="utf-8") as fo:
        json.dump(revdict, fo, ensure_ascii=False, indent=2, sort_keys=True)
    print("done")
