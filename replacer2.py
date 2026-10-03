#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that performs a find-and-replace operation across all .py files in the current working directory.
It should accept exactly two command-line arguments, the text to search for and the text to replace it with, decoding escape sequences (like \n) in both so multi-line snippets can be passed as strings.
For each Python file found, it should read the content, check whether the old text is present, and if so replace all occurrences and write the file back, printing a checkmark and filename for each modified file while catching and reporting any read/write errors per file.
It should also print usage instructions and exit gracefully if the wrong number of arguments is given or if no Python files are found, and print a summary of how many files were found and what replacement is being performed before processing."""

import sys
from pathlib import Path


def replace_in_file(path: Path, old_text: str, new_text: str) -> bool:
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        if old_text not in content:
            return False
        new_content = content.replace(old_text, new_text)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    except Exception as e:
        print(f"Error processing {path}: {e}")
        return False


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python replacer.py <old_text> <new_text>")
        print("\nExample:")
        print('python replacer.py "    try:\\n    path=Path(path)" "    path=Path(path)\\n    try:"')
        sys.exit(1)
    old_text = sys.argv[1]
    new_text = sys.argv[2]
    old_text = old_text.encode().decode("unicode_escape")
    new_text = new_text.encode().decode("unicode_escape")
    cwd = Path(".")
    py_files = list(cwd.glob("*.py"))
    if not py_files:
        print("No Python files found in current directory.")
        sys.exit(0)
    print(f"Found {len(py_files)} Python file(s)")
    print(f"Replacing: {old_text!r}")
    print(f"With:      {new_text!r}")
    print("-" * 40)
    modified_count = 0
    for py_file in py_files:
        if replace_in_file(py_file, old_text, new_text):
            print(f"✓ Modified: {py_file}")
            modified_count += 1
        else:
            print(f"  Skipped: {py_file} (no match)")
    print("-" * 40)
    print(f"Done! Modified {modified_count} file(s).")


if __name__ == "__main__":
    raise SystemExit(main())
_
