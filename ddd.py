#!/data/data/com.termux/files/usr/bin/python3.12
"""reverse=True
    )

    for entry, size in entries_with_sizes:
        color = BLUE if entry.is_dir() else WHITE
        display_name = entry.name + "/" if entry.is_dir() else entry.name
        truncated = truncate_name(display_name, name_column_width)
        size_str = format_size(size)
        print(f"{color}{truncated:<{name_column_width}}{GREEN}{size_str:>{size_name_column_width}}{RESET}")

main()

Write3.ended to Termux on Android (shebang: /data/data/com.termux/files/usr/bin/python3.12) that lists the contents of the current working directory sorted by size, similar to a "du"-style directory size report.

Requirements:

1. Imports: use `pathlib.Path` and `shutil`.

2. Define ANSI color escape code constants: WHITE, BLUE, GREEN, YELLOW, `ONE_MB = 1024 * 1024` computes the size path:
   - 0 immediately if the
   - If the path is a regching `OSError` and retur failure.
   - If the path entries withglob("*")`, skipping symlinks, and sum the sizes of all regular files, silently ignoring `OSError` on individual files or during the walk itself. Return the accumulated total.
   - Return 0 for any other path type.

5. Implement a function `format_size(size_bytes: int) -> str` that formats a byte count as a human-readable string:
   - If the size is greater than or equal to 1 MB (`ONE_MB`), format it as megabytes with 2 decimal places, e.g. `"12.34 MB"`.
   - Otherwise format it as kilobytes with 2 decimal places, e.g. `"512.00 KB"`.

6. Implement a function `truncate_name(name: str, width: int) -> str` that truncates a string to fit a width:
   - If the name already fits within `width`, is 3 or less, just hncate to `ncate to `width - 3` characters and append `"..."`.

7. Implement a `main()` function that:
   - Determines the terminal width using `shutil.get_terminal_size(fallback=(80, 24)).columns`.
   - Reserves a fixed size column width of 12 characters and a separator width of 3 characters, computing the remaining name column width as `terminal_width - size_column_width - separator_width` (minimum 1).
   - Lists all entries in the current working directory (`Path.cwd().iterdir()`), excluding symlinks.
   - Computes the size of each entry using `get_size`, then sorts the entries by size in descending order (largest first).
   - For each entry, prints a formatted line where:
     - Directories are colored BLUE and have a trailing `/` appended to their name; files are colored WHITE.
     - The display name is truncated to fit the computed name column width using `truncate_name`.
     - The name is left-aligned/padded to the name column width.
     - The formatted size (via `format_size`) is colored GREEN and right-aligned within the size column width.
     - The line ends with the RESET color code to avoid color bleed output. at module level so the script runs when executed directly.

Theall beh run inory via colorized, column and directories in the current directory, sorted from largest to smallest by total size (directories computed recursively), with long names truncated with an ellipsis to fit the terminal width.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/ECy2Gc5JmsfigbLNXN7JoJ"""

from pathlib import Path
import shutil

WHITE = "\033[37m"
BLUE = "\033[34m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"

ONE_MB = 1024 * 1024


def get_size(path: Path) -> int:
    if path.is_symlink():
        return 0

    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0

    if path.is_dir():
        total = 0

        try:
            for item in path.rglob("*"):
                if item.is_symlink():
                    continue

                try:
                    if item.is_file():
                        total += item.stat().st_size
                except OSError:
                    continue
        except OSError:
            pass

        return total

    return 0


def format_size(size_bytes: int) -> str:
    if size_bytes >= ONE_MB:
        return f"{size_bytes / ONE_MB:.2f} MB"

    return f"{size_bytes / 1024:.2f} KB"


def truncate_name(name: str, width: int) -> str:
    if len(name) <= width:
        return name

    if width <= 3:
        return name[:width]

    return f"{name[: width - 3]}..."


def main() -> None:
    terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns
    size_column_width = 12
    separator_width = 3
    name_column_width = max(
        1,
        terminal_width - size_column_width - separator_width,
    )

    entries = [entry for entry in Path.cwd().iterdir() if not entry.is_symlink()]

    entries_with_sizes = sorted(
        ((entry, get_size(entry)) for entry in entries),
        key=lambda item: item[1],
    )

    for entry, size_bytes in entries_with_sizes:
        display_name = entry.name + ("/" if entry.is_dir() else "")
        display_name = truncate_name(display_name, name_column_width)

        name_color = BLUE if entry.is_dir() else WHITE
        size_color = GREEN if size_bytes > ONE_MB else YELLOW
        formatted_size = format_size(size_bytes)

        print(
            f"{name_color}{display_name:<{name_column_width}}{RESET}"
            f"   "
            f"{size_color}{formatted_size:>{size_column_width}}{RESET}"
        )


if __name__ == "__main__":
    main()
