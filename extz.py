#!/data/data/com.termux/files/usr/bin/env python
"""You are reproducing a Python 3 command-line utility from scratch. Write a single, self-contained script that scans the current working directory recursively and reports how many files exist for each file extension, with optional size totals. Output only the script itself.

Purpose and behavior:
- Walk the current working directory recursively and group every regular file by its file extension (the suffix, e.g. ".py"). Files with no extension should be grouped under a sensible label such as "(no ext)".
- For each extension, report the file count. When a size option is enabled, also report the total size of those files and display sizes in human-readable form (bytes through TB, one decimal place, with a PB fallback).
- Output should be a colored, aligned terminal table or list. Use ANSI escape codes defined in a small color-constants class: reset, bold, dim, cyan, yellow, green, magenta, white, gray, plus composite styles for headers, extension names, counts, and data values. Sort results in a sensible order (e.g., by count descending, then by extension name).
- Accept command-line arguments via argparse, including a flag to include file sizes. Provide a help description. Support a way to disable colors (for example when stdout is not a TTY, or via a flag) so output is plain text when needed.

Skipping rules:
- Maintain a fixed set of directory names to skip anywhere in the path: VCS folders (.git, .hg, .svn), Python caches and virtual environments (__pycache__, .pytest_cache, .venv, venv, env, .tox, .mypy_cache, .ruff_cache, .egg-info), build and dependency output (node_modules, .next, dist, build), coverage output (.coverage, htmlcov), and temp/cache folders (.tmp, .cache).
- Skip any path that is a symbolic link, and skip any path having a component in the skip set.
- Do not follow symlinked directories.

Error handling and edge cases:
- Handle permission errors and files that disappear or cannot be stat'ed during the scan without crashing; skip them silently or with a brief warning to stderr.
- Handle the case where no files are found by printing a clear message.
- Handle KeyboardInterrupt gracefully, exiting with a short message and a nonzero status.
- Hidden files (dotfiles such as .bashrc with no real suffix) should be treated as having no extension unless Python's suffix logic says otherwise; be consistent.
- Extensions should be compared case-sensitively or normalized consistently; state the choice in code comments.

Execution details:
- Target Python 3 with type hints (Dict, List, Tuple, Optional, and built-in generics). Use pathlib, collections.defaultdict, shutil (for terminal width or similar layout if useful), sys, and argparse only; no third-party dependencies.
- The script should begin with a shebang line pointing to the Termux Python interpreter path (/data/data/com.termux/files/usr/bin/env python), and be runnable directly as a module entry point under a main guard that returns an exit code via sys.exit.
- Keep the code idiomatic and concise, with brief comments where logic is non-obvious.
---"""

import argparse
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    MAGENTA = "\033[35m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"
    HEADER_FG = BOLD + CYAN
    EXT_FG = BOLD + MAGENTA
    COUNT_FG = BOLD + GREEN
    DATA_FG = YELLOW


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    ".tox",
    "node_modules",
    ".next",
    "dist",
    "build",
    ".egg-info",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
    "htmlcov",
    ".tmp",
    ".cache",
}


def format_size(bytes_val: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


def should_skip(path: Path) -> bool:
    if path.is_symlink():
        return True
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    return False


def scan_extensions(show_size: bool = False) -> dict[str, tuple[list[Path], int]]:
    ext_map: dict[str, tuple[list[Path], int]] = defaultdict(lambda: ([], 0))
    cwd = Path.cwd()
    for file_path in cwd.rglob("*"):
        if should_skip(file_path):
            continue
        if file_path.is_file():
            ext = file_path.suffix or "<no-ext>"
            paths, total_size = ext_map[ext]
            file_size = file_path.stat().st_size if show_size else 0
            ext_map[ext] = (paths + [file_path], total_size + file_size)
    return ext_map


def generate_report(
    ext_map: dict[str, tuple[list[Path], int]],
    show_size: bool = False,
    max_examples: int = 3,
) -> list[tuple[str, int, str]]:
    report_data = []
    for ext in sorted(ext_map.keys(), key=lambda x: -len(ext_map[x][0])):
        paths, total_size = ext_map[ext]
        count = len(paths)
        if show_size:
            info = format_size(total_size)
        else:
            examples = ", ".join(str(p.relative_to(Path.cwd())) for p in paths[:max_examples])
            info = examples
        report_data.append((ext, count, info))
    return report_data


def format_table(
    report_data: list[tuple[str, int, str]],
    term_width: int,
    show_size: bool = False,
    use_color: bool = True,
) -> str:
    col1_width = max(10, int(term_width * 0.15))
    col2_width = 12
    col3_width = max(25, term_width - col1_width - col2_width - 5)
    lines = []
    col3_label = "Total Size" if show_size else "Example Files"
    header = f"{'Extension':<{col1_width}} | {'Count':>{col2_width}} | {col3_label:<{col3_width}}"
    if use_color:
        header = (
            f"{Colors.HEADER_FG}{'Extension':<{col1_width}}{Colors.RESET} | "
            f"{Colors.HEADER_FG}{'Count':>{col2_width}}{Colors.RESET} | "
            f"{Colors.HEADER_FG}{col3_label:<{col3_width}}{Colors.RESET}"
        )
    lines.append(header)
    lines.append(f"{Colors.DIM}{'-' * len(header)}{Colors.RESET}" if use_color else "-" * len(header))
    for ext, count, info in report_data:
        if len(info) > col3_width:
            info = info[: col3_width - 3] + "..."
        if use_color:
            row = (
                f"{Colors.EXT_FG}{ext:<{col1_width}}{Colors.RESET} | "
                f"{Colors.COUNT_FG}{count:>{col2_width}}{Colors.RESET} | "
                f"{Colors.DATA_FG}{info:<{col3_width}}{Colors.RESET}"
            )
        else:
            row = f"{ext:<{col1_width}} | {count:>{col2_width}} | {info:<{col3_width}}"
        lines.append(row)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Report file extensions in current directory recursively.")
    parser.add_argument(
        "-s",
        "--size",
        action="store_true",
        help="Show total size per extension instead of example files",
    )
    parser.add_argument("--no-color", action="store_true", help="Disable color output")
    args = parser.parse_args()
    try:
        term_width = shutil.get_terminal_size(fallback=(80, 24)).columns
        use_color = not args.no_color and sys.stdout.isatty()
        mode_str = "size mode" if args.size else "example files mode"
        cwd_str = str(Path.cwd())
        if use_color:
            print(f"Scanning {Colors.BOLD}{cwd_str}{Colors.RESET} ({mode_str})...\n")
        else:
            print(f"Scanning {cwd_str} ({mode_str})...\n")
        ext_map = scan_extensions(show_size=args.size)
        if not ext_map:
            print("No files found.")
            sys.exit(0)
        report_data = generate_report(ext_map, show_size=args.size)
        table = format_table(report_data, term_width, show_size=args.size, use_color=use_color)
        print(table)
        total_files = sum(count for _, count, _ in report_data)
        total_exts = len(report_data)
        if args.size:
            total_bytes = sum(ext_map[ext][1] for ext in ext_map)
            summary = (
                (
                    f"\n{Colors.GRAY}✓ Total unique extensions: {total_exts}{Colors.RESET}\n"
                    f"{Colors.GRAY}✓ Total files: {total_files}{Colors.RESET}\n"
                    f"{Colors.GRAY}✓ Total size: {format_size(total_bytes)}{Colors.RESET}"
                )
                if use_color
                else (
                    f"\n✓ Total unique extensions: {total_exts}\n"
                    f"✓ Total files: {total_files}\n"
                    f"✓ Total size: {format_size(total_bytes)}"
                )
            )
        else:
            summary = (
                (
                    f"\n{Colors.GRAY}✓ Total unique extensions: {total_exts}{Colors.RESET}\n"
                    f"{Colors.GRAY}✓ Total files: {total_files}{Colors.RESET}"
                )
                if use_color
                else (f"\n✓ Total unique extensions: {total_exts}\n✓ Total files: {total_files}")
            )
        print(summary)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
