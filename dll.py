#!/data/data/com.termux/files/usr/bin/env python

import sys
from pathlib import Path


def delete_lines_from_file() -> None:
    if len(sys.argv) not in (3, 4):
        raise SystemExit(f"Usage: {sys.argv[0]} <file> <start_line> [end_line]")
    filename = sys.argv[1]
    path = Path(filename)
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        fromline = int(sys.argv[2])
        toline = int(sys.argv[3]) if len(sys.argv) == 4 else len(lines)
    except ValueError:
        raise SystemExit("Line numbers must be integers") from None
    if fromline < 1 or toline < fromline:
        raise SystemExit("Line range must start at 1 or greater and end on or after the start")
    new_lines = lines[: fromline - 1] + lines[toline:]
    path.write_text("\n".join(new_lines), encoding="utf-8")
    print(f"remained: {len(new_lines)} lines")


if __name__ == "__main__":
    delete_lines_from_file()
