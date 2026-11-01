#!/usr/bin/env python3
"""List tracked Python scripts with their line counts, smallest first.

This produced the batch manifests used during the refactor run: sorting by line
count keeps early batches verifiable and lets large scripts get the attention
they need.

Usage
    python3 arena/repo_inventory.py [--limit N] [--min-lines N] [--names-only]

Output is ``<lines> <path>`` by default, or bare paths with ``--names-only``
(suitable for feeding to other scripts).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_PREFIXES = ("documented/", "refactored/", "reqs/")


def tracked_python_files(root: Path) -> list[str]:
    """Return tracked ``*.py`` paths, minus the excluded subtrees."""
    result = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=root, capture_output=True, text=True, timeout=300, check=False
    )
    if result.returncode != 0:
        raise SystemExit(f"git ls-files failed: {result.stderr.strip()}")
    return [
        line
        for line in result.stdout.splitlines()
        if line and not line.startswith(EXCLUDED_PREFIXES)
    ]


def main(argv: list[str] | None = None) -> int:
    """Print the inventory and a short total."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=0, help="show only the first N files")
    parser.add_argument("--min-lines", type=int, default=0, help="skip files below this size")
    parser.add_argument("--names-only", action="store_true", help="print bare paths")
    args = parser.parse_args(argv)

    rows: list[tuple[int, str]] = []
    for name in tracked_python_files(ROOT):
        path = ROOT / name
        if not path.is_file():
            continue
        try:
            lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        except OSError as exc:
            print(f"cannot read {name}: {exc}", file=sys.stderr)
            continue
        if lines >= args.min_lines:
            rows.append((lines, name))

    rows.sort()
    shown = rows[: args.limit] if args.limit else rows
    for lines, name in shown:
        print(name if args.names_only else f"{lines:6d} {name}")

    total_lines = sum(lines for lines, _ in rows)
    print(
        f"# {len(rows)} files, {total_lines} lines"
        + (f", showing {len(shown)}" if args.limit else ""),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
