#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that inspects Python wheel archives (.whl files) and determines whether each wheel is effectively empty, meaning it contains no meaningful package content beyond its packaging metadata. The script should accept one or more wheel file paths, report which wheel is currently being examined as it processes it, and return a clear boolean verdict for each wheel indicating whether it is empty or contains real content. A wheel should be considered non-empty as soon as it includes any file outside its metadata directory, and it should be treated as empty only when every recorded entry belongs to that metadata directory. The script must handle malformed or unreadable archives gracefully, such as missing metadata, missing manifest files, or corrupt zip data, by returning a sensible result rather than crashing. Design the logic so it can be reused as a function that other tools can import, and provide a simple command-line entry point that prints a summary line per wheel with its path and verdict.
---"""

from __future__ import annotations
import csv
from pathlib import Path
import zipfile


def is_empty_wheel(wheel_path: str) -> bool:
    print(f"checking {wheel_path}")
    try:
        with zipfile.ZipFile(wheel_path, "r") as z:
            [
                name.rstrip("/")
                for name in z.namelist()
                if name.endswith(".dist-info/") or (name == name.rstrip("/") + "/" and name.endswith(".dist-info"))
            ]
            dist_info = next(
                (name.rstrip("/") for name in z.namelist() if ".dist-info" in name),
                None,
            )
            if not dist_info:
                return False
            record_path = f"{dist_info}/RECORD"
            if record_path not in z.namelist():
                return False
            with z.open(record_path) as f:
                reader = csv.reader(line.decode("utf-8") for line in f)
                for row in reader:
                    if not row:
                        continue
                    path = row[0]
                    if not path.startswith(f"{dist_info}/"):
                        return False
            return True
    except (zipfile.BadZipFile, KeyError, UnicodeDecodeError):
        return False


def main() -> None:
    current_dir = Path()
    wheel_files = list(current_dir.glob("*.whl"))
    if not wheel_files:
        return
    empty_wheels = [str(w) for w in wheel_files if is_empty_wheel(str(w))]
    if not empty_wheels:
        print("No empty wheel files found")
        return
    print("\n".join(empty_wheels))


if __name__ == "__main__":
    raise SystemExit(main())
