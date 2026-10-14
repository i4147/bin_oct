#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory tree recursively and produces a disk usage report, including total size, file and folder counts, and a breakdown of storage consumed by file type. The script should accept a target directory path from the command line (defaulting to the current directory) and an optional output file path for saving the summary. It should handle unreadable or inaccessible files gracefully by counting them without failing the entire scan. Files without an extension should be grouped under a clear label, and extension matching should be case-insensitive. The report should present sizes in human-readable units, list the file types ordered by total size consumed from largest to smallest, and clearly indicate the overall totals. The script should print the summary to the console and, when requested, write the same summary to a file. In addition, it should be able to generate a visual chart (such as a bar or pie chart) showing how space is distributed across the most significant file types, with smaller categories combined into an "other" group, and save or display that chart. Design the command-line interface so that users can easily control the target directory, output destination, and whether a chart is produced, and ensure the script provides helpful error messages when the given path does not exist or is not a directory.
---"""

from __future__ import annotations
import argparse
from collections import defaultdict
import operator
from pathlib import Path
import sys
from dh import fsz
import matplotlib.pyplot as plt


def scan_directory(path: str = "."):
    total_size = 0
    file_count = 0
    folder_count = 0
    extensions = set()
    size_by_ext = defaultdict(int)
    base_path = Path(path)
    for p in base_path.rglob("*"):
        if p.is_dir():
            folder_count += 1
        elif p.is_file():
            file_count += 1
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            total_size += size
            ext = p.suffix.lower() if p.suffix else "(no extension)"
            extensions.add(ext)
            size_by_ext[ext] += size
    return total_size, file_count, folder_count, extensions, size_by_ext


def write_summary(filename: Path | None = None) -> None:
    total_size, file_count, folder_count, extensions, size_by_ext = scan_directory()
    summary_lines = []
    summary_lines.append(f"Total size: {fsz(total_size)}\n")
    summary_lines.append("File extensions:\n")
    sorted_extensions = sorted(extensions)
    for ext in sorted_extensions:
        summary_lines.append(f"   - {ext}\n")
    summary_lines.append(f"Number of files: {file_count}\n")
    summary_lines.append(f"Number of folders: {folder_count}\n")
    summary_lines.append("Size by extension:\n")
    sorted_size_by_ext = sorted(size_by_ext.items(), key=operator.itemgetter(1), reverse=True)
    for ext, size in sorted_size_by_ext:
        summary_lines.append(f"  {ext}: {fsz(size)}\n")
        if filename is None or filename == sys.stderr:
            print(f"  {ext}: {fsz(size)}\n", file=sys.stderr)
    summary_string = "".join(summary_lines)
    if filename.exists():
        print(f"{filename} exists")
        sys.exit(1)
    if filename and filename != sys.stderr:
        try:
            with filename.open("w", encoding="utf-8") as f:
                f.write(summary_string)
            print(f"Summary saved to {filename}")
        except OSError as e:
            print(f"Error saving summary to {filename}: {e}", file=sys.stderr)
    elif filename is None:
        print(summary_string)


def create_bar_chart(chart_type: str, output_filename: str = "/sdcard/dirinfo.png") -> None:
    _, _, _, _, size_by_ext = scan_directory()
    sorted_items = sorted(
        [(ext, size) for ext, size in size_by_ext.items() if size > 0],
        key=operator.itemgetter(1),
        reverse=True,
    )
    if not sorted_items:
        print("No data to plot.", file=sys.stderr)
        return
    extensions, sizes = zip(*sorted_items, strict=False)
    reshaped_extensions = extensions
    plt.title("Size by File Extension")
    plt.xticks(rotation=45, ha="right")
    plt.gca().set_xticklabels(reshaped_extensions)
    plt.figure(figsize=(12, 7))
    plt.bar(reshaped_extensions, sizes, color="skyblue")
    plt.xlabel("File Extension")
    plt.ylabel("Size (bytes)")
    plt.tight_layout()
    try:
        plt.savefig(output_filename)
        print(f"Bar chart saved to {output_filename}")
    except Exception as e:
        print(f"Error saving chart to {output_filename}: {e}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze directory information.")
    parser.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Save the report to a file named .dirinfo in the current directory.",
    )
    parser.add_argument(
        "-i",
        "--image",
        metavar="FILENAME",
        type=str,
        help="Save a Matplotlib bar chart of file types and sizes to the specified image file (e.g., chart.png).",
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=["persian", "english"],
        default="english",
        help="Specify the language/type of the Matplotlib chart title and labels (default: english).",
    )
    parser.add_argument(
        "path",
        metavar="PATH",
        type=str,
        nargs="?",
        default=".",
        help="The directory to scan (default: current directory).",
    )
    args = parser.parse_args()
    if args.save:
        write_summary(Path("/sdcard/.dirinfo"))
    elif args.image:
        create_bar_chart(args.type, args.image)
    else:
        write_summary(Path("/sdcard/dirinfo"))
