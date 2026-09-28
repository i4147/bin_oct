#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python command-line script that takes a JSON file path as its single argument, loads the JSON object from that file, and reverses its key-value mappings using a reverse_dict function imported from a local module named dh.
The script should then overwrite the same file with the reversed dictionary, writing it as UTF-8 encoded JSON with indentation of 2 spaces, sorted keys, and ensure_ascii disabled so non-ASCII characters are preserved as-is.
After successfully writing the file, it should print "done" to indicate completion."""

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
