#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans the current working directory and all of its subdirectories for files named "setup.py", and updates any ABI version tag that is embedded in them to match the Python interpreter version currently running the script. Specifically, each setup file may contain a wheel or platform declaration of the form "python, abi=..." where the ABI tag follows the pattern "cp3" followed by one or more digits; the script should replace that existing tag with a tag corresponding to the running interpreter's minor version (for example, "cp311" for Python 3.11), while leaving the rest of the file untouched.
The script should behave as follows:
- Process every matching setup file found anywhere beneath the starting directory, not only the top level.
- Only rewrite a file when its content actually changes, and skip files that contain no matching declaration.
- Read and write files using UTF-8 encoding, preserving all other text exactly as it appears.
- For each file that is updated, print a short confirmation line showing the file's path relative to the starting directory, using a check mark prefix.
- If an error occurs while handling a particular file (for example, due to permissions or encoding problems), print an error message identifying that file and the reason, then continue processing the remaining files rather than aborting.
- When finished, print a summary line stating how many files were updated and which target ABI tag was applied.
- The script should run its main logic only when executed directly as a program, not when imported as a module.
---"""

from __future__ import annotations
from pathlib import Path
import re
import sys


def update_setup_files() -> None:
    target_cp = f"cp3{sys.version_info.minor}"
    pattern = re.compile(r'(python,\s*abi\s*=\s*")cp3\d+(")')
    current_dir = Path.cwd()
    updated_files = 0
    for setup_file in current_dir.rglob("setup.py"):
        try:
            content = setup_file.read_text(encoding="utf-8")
            if pattern.search(content):
                new_content = pattern.sub(rf"\g<1>{target_cp}\2", content)
                if new_content != content:
                    setup_file.write_text(new_content, encoding="utf-8")
                    print(f"✓ Updated: {setup_file.relative_to(current_dir)}")
                    updated_files += 1
        except Exception as e:
            print(f"❌ Error processing {setup_file}: {e}")
    print(f"\nFinished! Updated {updated_files} file(s) to match Python version '{target_cp}'.")


if __name__ == "__main__":
    update_setup_files()
