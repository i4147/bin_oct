#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that tells an AI coding agent to build a Python command-line script with the following specification.

Build a Python 3 command-line script that filters translation records in a JSON file, keeping only successful translations and moving unchanged ones into a separate failure log. The script should be written for Termux on Android, so its shebang line should point to Termux's Python at `/data/data/com.termux/files/usr/bin/env python`, and it should begin with `from __future__ import annotations`. Use only the standard library: `json`, `sys`, and `pathlib`.

**Invocation and argument handling**
- Run as `script.py <dic.json>` with exactly one positional argument, the path to a JSON file.
- If the argument count is not exactly one, print a usage message that includes the script name (`sys.argv[0]`) and the placeholder `<dic.json>`, then exit with status 1.
- If the path does not point to an existing regular file, print `Error: file not found: <path>` and exit with status 1.

**Input formats**
- Open the file as UTF-8 and parse it with `json.load`.
- Accept two structures:
  - A JSON object (dict) mapping original strings to translated strings. Each item is a key-value pair.
  - A JSON array (list) of objects, each with the keys `"orig"` and `"translated"`. Convert each entry into an (orig, translated) pair by reading those keys.
- Any other top-level JSON type must print `Error: unsupported JSON structure (expected dict or list).` and exit with status 1.
- Do not guard against malformed list entries beyond what the natural key access does; a missing key will raise an error.

**Classification logic**
- Iterate over all (orig, translated) pairs.
- A pair where the original and translated strings are exactly equal is a failure, meaning the translation did not change the text. Collect the original string into a `failed` list.
- All other pairs are successes. Collect them as (orig, translated) tuples into a `good` list.
- Preserve the input order within each list.

**Rewriting the input file**
- Overwrite the same JSON file with only the successful records.
- If the input was a dict, write a dict built from the good pairs.
- If the input was a list, write a list of objects with `"orig"` and `"translated"` keys, preserving the original key names.
- Write with UTF-8 encoding, `ensure_ascii=False`, and `indent=2`.

**Reporting success**
- Print `Kept <N> records in <path>` where N is the count of successful records and path is the JSON file path.

**Failed-record log**
- If there are no failed records, print `No failed records — skipped creating failed.txt` (with an em dash) and return without creating any file.
- Otherwise, write a file named `failed.txt` in the same directory as the JSON file (use `with_name` on the path). The file should list the failed original strings, one per line.
- If `failed.txt` already exists, do not blindly overwrite it. Instead, read its existing contents, and append only the failed entries not already present, so that repeated runs accumulate failures without duplicates. (Implement the existing-file check and merge with UTF-8 encoding.)
- Print a confirmation message stating how many failed records were written and the path of the log file.

**Execution entry point**
- Define a `main()` function containing all logic, and invoke it under the standard `if __name__ == "__main__":` guard.
- Use `sys.exit(1)` for all error paths and normal return for success.

**Style**
- Keep the script short, plain, and readable, with no classes and no third-party dependencies.
- Use f-strings for messages and UTF-8 for all file operations.
---"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <dic.json>")
        sys.exit(1)
    json_path = Path(sys.argv[1])
    if not json_path.is_file():
        print(f"Error: file not found: {json_path}")
        sys.exit(1)
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        items = list(data.items())
    elif isinstance(data, list):
        items = [(entry["orig"], entry["translated"]) for entry in data]
    else:
        print("Error: unsupported JSON structure (expected dict or list).")
        sys.exit(1)
    good = []
    failed = []
    for orig, translated in items:
        if orig == translated:
            failed.append(orig)
        else:
            good.append((orig, translated))
    if isinstance(data, dict):
        good_data = dict(good)
    else:
        good_data = [{"orig": o, "translated": t} for o, t in good]
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(good_data, f, ensure_ascii=False, indent=2)
    print(f"Kept {len(good)} records in {json_path}")
    if not failed:
        print("No failed records — skipped creating failed.txt")
        return
    failed_path = json_path.with_name("failed.txt")
    if failed_path.exists():
        existing = failed_path.read_text(encoding="utf-8")
        with failed_path.open("a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("\n".join(failed))
            f.write("\n")
        print(f"Appended {len(failed)} failed records to {failed_path}")
    else:
        with failed_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(failed))
            f.write("\n")
        print(f"Wrote {len(failed)} failed records to {failed_path}")


if __name__ == "__main__":
    main()
