#!/data/data/com.termux/files/usr/bin/python
"""s as an interactive terminal (TUI) file previewer for directory. The script should list all reg sorted alphabetically by name in a case-insensitive manner, and let the user browse them one at a time.
For each selected file, the script should display its name and position within the list (for example, "File 3/12: notes.txt") as a clearly visible header, followed by a preview of the file's first portion of lines (around 20 lines). Reading should be tolerant of text encoding problems, replacing undecodable characters rather than failing, and any read error should be shown gracefully within the preview area instead of crashing the program.
The interface should use color to distinguish elements such as the header, the body text, status or navigation hints, and error messages. The display should adapt to the terminal size, truncating long lines or content that does not fit the visible area without breaking the layout.
Users should be able to move forward and backward through the file list with keyboard controls (arrow keys and common alternatives such as vim-style keys), jump to the first or last file, and quit cleanly with a key such as "q" or Escape. The terminal should be restored to its normal state on exit, including when errors occur. Handle window resize events so the display redraws correctly.
Keep the implementation simple, robust, and dependency-free beyond the Python standard library, and include a brief on-screen key help line at the bottom of the interface.
---"""

from __future__ import annotations
import curses
from pathlib import Path

LINES_PER_FILE = 20


def list_files() -> list[Path]:
    return sorted([p for p in Path().iterdir() if p.is_file()], key=lambda p: p.name.lower())


def head_lines(path, n: int):
    lines = []
    try:
        with Path(path).open(encoding="utf-8", errors="replace") as f:
            for _ in range(n):
                line = f.readline()
                if not line:
                    break
                lines.append(line.rstrip("\n"))
    except Exception as e:
        lines = [f"[Error reading file: {e}]"]
    return lines


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)


def draw(stdscr, files: list[Path], idx: int) -> None:
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    header = f"File {idx + 1}/{len(files)}: {files[idx].name}"
    stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
    stdscr.addnstr(0, 0, header, w - 1)
    stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
    lines = head_lines(files[idx], LINES_PER_FILE)
    for i, line in enumerate(lines, start=2):
        if i >= h - 1:
            break
        if line.startswith("[Error"):
            stdscr.attron(curses.color_pair(4))
            stdscr.addnstr(i, 0, line, w - 1)
            stdscr.attroff(curses.color_pair(4))
        else:
            stdscr.attron(curses.color_pair(2))
            stdscr.addnstr(i, 0, line, w - 1)
            stdscr.attroff(curses.color_pair(2))
    footer = "PgDown: next | PgUp: prev | q: quit"
    stdscr.attron(curses.color_pair(3))
    stdscr.addnstr(h - 1, 0, footer, w - 1)
    stdscr.attroff(curses.color_pair(3))
    stdscr.refresh()


def main(stdscr) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)
    init_colors()
    files = list_files()
    if not files:
        stdscr.addstr(0, 0, "No files in directory.")
        stdscr.getch()
        return
    idx = 0
    draw(stdscr, files, idx)
    while True:
        key = stdscr.getch()
        if key in {ord("q"), ord("Q")}:
            break
        if key == curses.KEY_NPAGE:
            if idx < len(files) - 1:
                idx += 1
                draw(stdscr, files, idx)
        elif key == curses.KEY_PPAGE and idx > 0:
            idx -= 1
            draw(stdscr, files, idx)


if __name__ == "__main__":
    curses.wrapper(main)
