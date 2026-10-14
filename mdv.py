#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a terminal Markdown viewer. The tool should take a single optional command-line argument specifying the path to a Markdown file, defaulting to a file named README.md in the current directory when no path is given. It should read the file as UTF-8 text and render it attractively in the terminal, with proper formatting for headings, lists, code blocks, emphasis, and other common Markdown elements.
The viewer should display the content page by page, so that long documents fit the terminal height and the user can move forward and backward through the content using keyboard input, and quit at any time. If keyboard input capture is unavailable in the environment, the tool should gracefully fall back to a simpler, still-usable paging mode rather than crashing.
If the specified file does not exist, the tool should print a clear, human-readable error message to standard error and exit with a non-zero status code instead of showing a raw stack trace. On successful completion it should exit with status code zero. Include a helpful description and usage text for the command-line interface, including a short summary of what the tool does and how the file argument works.
Keep the implementation self-contained, handle terminal resizing gracefully, and ensure the output is readable on both light and dark terminal backgrounds.
---"""

from __future__ import annotations
import argparse
from pathlib import Path
import sys
from rich.console import Console
from rich.markdown import Markdown

try:
    from readchar import (
        key as RKEY,
        readkey,
    )

    HAVE_READCHAR = True
except Exception:
    HAVE_READCHAR = False


def read_markdown(path: str | Path) -> str:
    path = Path(path)
    if not path.is_file():
        msg = f"File not found: {path}"
        raise FileNotFoundError(msg)
    return path.read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mdview",
        description="View a Markdown file in the terminal, page by page.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="README.md",
        type=str,
        help="Path to a Markdown file (default: README.md)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    console = Console()
    err_console = Console(stderr=True)
    try:
        markdown_text = read_markdown(args.file)
    except FileNotFoundError as error:
        err_console.print(f"[red]Error:[/red] {error}")
        return 1
    except PermissionError:
        err_console.print(f"[red]Error:[/red] Permission denied: {args.file}")
        return 1
    except UnicodeDecodeError:
        err_console.print(f"[red]Error:[/red] {args.file} is not a valid UTF-8 text file.")
        return 1
    except OSError as error:
        err_console.print(f"[red]Error:[/red] {error}")
        return 1
    md = Markdown(markdown_text)
    with console.capture() as capture:
        console.print(md)
    rendered = capture.get()
    lines = rendered.splitlines()
    if not lines:
        console.print("[dim](empty file)[/dim]")
        return 0
    height = max(console.size.height - 2, 1)
    page_count = max((len(lines) + height - 1) // height, 1)
    current_page = 0
    while True:
        console.clear()
        start = current_page * height
        end = start + height
        for line in lines[start:end]:
            sys.stdout.write(line + "\n")
        sys.stdout.flush()
        try:
            if HAVE_READCHAR:
                k = readkey()
                if k in (RKEY.PAGE_DOWN, RKEY.SPACE, RKEY.RIGHT, RKEY.DOWN):
                    if current_page < page_count - 1:
                        current_page += 1
                    else:
                        console.print("[dim](already at last page)[/dim]")
                elif k in (RKEY.PAGE_UP, RKEY.LEFT, RKEY.UP):
                    if current_page > 0:
                        current_page -= 1
                    else:
                        console.print("[dim](already at first page)[/dim]")
                elif k in ("q", "Q"):
                    break
                else:
                    continue
        except (EOFError, KeyboardInterrupt):
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
