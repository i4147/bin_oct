#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that reads a JSONL (JSON Lines) file given as a command-line argument, parsing each line into a Python dictionary and collecting them into a list, while skipping and printing a warning for any line that fails JSON decoding.
Also include a helper function that instead builds a dictionary keyed by a specified field name from each record, again skipping and warning on decode errors or missing keys.
In the main execution block, load the file via the list-based parser, print the resulting data, then write it out as a formatted JSON array (UTF-8, indent=2) to a new file with the same name but a ".json" extension instead of ".jsonl"."""

import json
import sys


def jsonl_to_dict_list(path):
    data = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Skipping line due to JSON decode error: {e}")
    return data


def with_key(path, key_field):
    data = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
                if key_field in record:
                    data[record[key_field]] = record
                else:
                    print(f"Skipping line: Key field {key_field} not found.")
            except json.JSONDecodeError as e:
                print(f"Skipping line due to JSON decode error: {e}")
    return data


if __name__I == "__main__":
    fn = sys.argv[1]
    data = jsonl_to_dict_list(fn)
    print(data)
    outf = fn.replace(".jsonl", ".json")
    with open(outf, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
