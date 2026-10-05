#!/data/data/com.termux/files/usr/bin/python3.12
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
