#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line file viewer for the current working directory, displaying the contents of every file in a paged, scrollable format. By default, the tool should list only the files located directly in the current directory.ursive option is provided on the command line, it should also include files found in all subdirectories beneath it. Files should be presented in a stable, case-insensitive alphabetical order based on their paths.
For each file, the output should clearly show a visually distinct header containing the file's path relative to the starting directory, followed by the file's text content. Content should be read as text in a tolerant way so that files with unusual or invalid characters still display without crashing. If a file cannot be read due to a system or permission error, the tool should display a brief message in place of its contents and continue processing the remaining files rather than stopping.
If no files are found, the tool should print a short message indicating that and exit cleanly. The overall output should be delivered through a pager so the user can scroll and navigate through large amounts of content comfortably, with the entire combined output presented asuous, readable document. Provide a help description accessible from the command line that explains the purpose of the tool and its recursive option.
---"""

from __future__ import annotations
import argparse
from pathlib import Path
import pydoc


def collect_files(root: Path, recursive: bool) -> list[Path]:
    paths = root.rglob("*") if recursive else root.iterdir()
    return sorted(
        (path for path in paths if path.is_file()),
        key=lambda path: str(path).lower(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="View files in the current directory with paging.")
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="include files in subdirectories",
    )
    args = parser.parse_args()
    root = Path.cwd()
    files = collect_files(root, args.recursive)
    if not files:
        print("No files found.")
        return
    output = []
    for path in files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            content = f"[Could not read file: {exc}]"
        output.append(f"\n{'=' * 40}")
        output.append(f"FILE: {path.relative_to(root)}")
        output.append("=" * 40)
        output.append(content)
    pydoc.pager("\n".join(output))


if __name__ == "__main__":
    raise SystemExit(main())
