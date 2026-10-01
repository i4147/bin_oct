#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that recursively scans the current working directory for all subdirectories and removes any that are empty.
It should collect all directories using pathlib's rglob, sort them by depth (deepest first) so that nested empty directories are removed before their parents, and attempt to remove each one, silently skipping those that fail (e.g., because they are not empty).
For each successfully removed directory, print a message showing its path, and after processing finish by printing the total count of empty directories removed.
The script should be runnable as a standalone program via a main function returning an exit code."""

from pathlib import Path


def main() -> None:
    count = 0
    root = Path.cwd()
    dirs = [p for p in root.rglob("*") if p.is_dir()]
    dirs.sort(key=lambda p: len(p.parts), reverse=True)
    for dir_path in dirs:
        try:
            dir_path.rmdir()
            print(f"removing empty dir: {dir_path}")
            count += 1
        except OSError:
            pass
    print(f"total {count} empty dirs removed")


if __name__ == "__main__":
    raise SystemExit(main())
