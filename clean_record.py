#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that scans the current directory for all `*.dist-info` folders and cleans up their `RECORD` files.
For each `RECORD` file found, it should parse each line as a CSV-style entry with the file path as the first field, and remove any entries pointing to files inside a `.dist-info` directory whose filename is not in an allowed whitelist (METADATA, RECORD, WHEEL, entry_points.txt, top_level.txt).
Skipped/removed entries should be printed to stdout with a message indicating the removed path, and after processing each RECORD file the script should overwrite it with the filtered lines and print a confirmation message naming the dist-info folder.
The script should expose a `main()` entry point and exit via `SystemExit(main())` when run as a standalone program."""

from __future__ import annotations
from pathlib import Path

ALLOWED_DIST_INFO_FILES = {
    "METADATA",
    "RECORD",
    "WHEEL",
    "entry_points.txt",
    "top_level.txt",
}


def clean_records():
    for dist_info in Path().glob("*.dist-info"):
        record_file = dist_info / "RECORD"
        if record_file.exists():
            lines = record_file.read_text().splitlines()
            filtered = []
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split(",")
                path = parts[0]
                path_obj = Path(path)
                is_in_dist_info = any(part.endswith(".dist-info") for part in path_obj.parts)
                if is_in_dist_info and path_obj.name not in ALLOWED_DIST_INFO_FILES:
                    print(f"Removed dist-info reference: {path}")
                    continue
                filtered.append(line)
            record_file.write_text("\n".join(filtered) + ("\n" if filtered else ""))
            print(f"record file in {record_file.parent.name} cleaned.")


def main():
    clean_records()


if __name__ == "__main__":
    raise SystemExit(main())
