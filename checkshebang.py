#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that recursively scans all ".py" files under the current working directory to detect ones containing more than one shebang line (a line starting with "#!").
For each file, it reads its text with UTF-8 encoding (ignoring decode errors), splits it into lines, and counts how many lines begin with "#!"; if the count exceeds one, it prints the file path with a message indicating it has 2 shebangs and increments a counter.
After scanning all files, it prints a summary line showing the total number of files flagged as having duplicate shebangs."""

from pathlib import Path


def fix_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines(keepends=False)
    if not lines:
        return False
    i = 0
    for line in lines:
        if line.startswith("#!"):
            i += 1
    return i > 1


def main() -> None:
    fixed = 0
    cwd = Path.cwd()
    for file in cwd.rglob("*.py"):
        if fix_file(file):
            fixed += 1
            print(f"{file} has 2 shebang")
    print(f"\nDone. Updated {fixed} files.")


if __name__ == "__main__":
    raise SystemExit(main())
