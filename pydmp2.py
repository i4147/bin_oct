#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that recursively scans the current working directory for empty subdirectories and removes them.
It should traverse all paths under the root in reverse sorted order (so nested empty directories are handled before their parents), check each directory to see if it contains no files or subdirectories, print a message for each empty directory removed, and finally print the total count of directories deleted.
The script should run as a standalone program via a main function invoked through the standard `if __name__ == "__main__"` entry point."""

from pathlib import Path
def main() -> None:
    count = 0
    root = Path.cwd()
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            print(f"removing empty dir: {path}")
            path.rmdir()
            count += 1
    print(f"total {count} empty dirs removed")
if __name__ == "__main__":
    raise SystemExit(main())