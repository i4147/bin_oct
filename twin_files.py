#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that scans the current working directory for all ".json" files and, for each one, checks whether a ".txt" file with the same base name also exists.
If a matching pair is found, the script reports it and, depending on the mode, either deletes the ".txt" file or merely logs that it would be deleted.
It should default to a safe dry-run mode that only prints matched pairs without removing anything, and support an "-a/--apply" command-line flag to actually perform the deletions, handling any deletion errors gracefully.
At the end, it should print a summary showing the total number of JSON files checked and the number of files removed (or a note that it was a dry run)."""

import argparse
from pathlib import Path


def remove_second_if_first_exists(root: Path, dry_run: bool = True) -> None:
    removed = 0
    checked = 0
    for json_path in root.glob("*.json"):
        checked += 1
        txt_path = json_path.with_suffix(".txt")
        if txt_path.exists():
            print(f"[MATCH] {json_path}  ->  {txt_path}")
            if not dry_run:
                try:
                    txt_path.unlink()
                    print(f"[REMOVED] {txt_path}")
                    removed += 1
                except Exception as e:
                    print(f"[ERROR] Could not remove {txt_path}: {e}")
            else:
                print(f"[DRY RUN] Would remove {txt_path}")
    print("\n--- Summary ---")
    print(f"Checked: {checked}")
    print(f"Removed: {removed}" if not dry_run else "Dry run only. No files removed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove .txt files if a .json file with the same name exists.")
    parser.add_argument(
        "-a",
        "--apply",
        action="store_true",
        help="Actually delete files (default is dry run).",
    )
    args = parser.parse_args()
    cwd = Path.cwd()
    remove_second_if_first_exists(cwd, dry_run=not args.apply)
