#!/usr/bin/env python3
"""Compare a rewritten tree against its originals on ruff lint and format status.

The point of the docstring task was to add documentation **without** introducing
any new lint or formatting debt. This script proves that by running ruff over
both trees and comparing the result sets per file.

Usage
    python3 arena/check_parity.py [--orig DIR] [--new DIR] [--ruff PATH]

Exit status is 0 when both trees are identical in lint histogram and in the set
of files ruff-format would change, 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE = re.compile(r"\b([A-Z]+[0-9]{3,4})\b")
FORMAT_TARGET = re.compile(r"--> ([^:]+):\d+:\d+")


def ruff_path(explicit: str | None) -> str:
    """Return the ruff executable to use, or exit with a clear message."""
    candidates = [
        explicit,
        os.environ.get("ARENA_RUFF"),
        "/tmp/uvenv/bin/ruff",
        "/tmp/tools/bin/ruff",
        shutil.which("ruff"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise SystemExit(
        "ruff not found; pass --ruff PATH or set ARENA_RUFF "
        "(e.g. python3 -m pip install --user ruff)"
    )


def lint_histogram(ruff: str, target: Path, excludes: list[str]) -> Counter[str]:
    """Return a ``{code: count}`` histogram for one tree."""
    cmd = [ruff, "check", str(target), "--output-format", "concise"]
    for name in excludes:
        if (target / name).is_dir():
            cmd += ["--exclude", name]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    histogram: Counter[str] = Counter()
    for line in (result.stdout + result.stderr).splitlines():
        match = CODE.search(line)
        if match:
            histogram[match.group(1)] += 1
    return histogram


def format_targets(ruff: str, paths: list[Path]) -> set[str]:
    """Return the file names ruff-format would rewrite."""
    if not paths:
        return set()
    result = subprocess.run(
        [ruff, "format", "--check", *[str(p) for p in paths]],
        capture_output=True,
        text=True,
        timeout=900,
    )
    return {Path(name).name for name in FORMAT_TARGET.findall(result.stdout + result.stderr)}


def main(argv: list[str] | None = None) -> int:
    """Run both comparisons and report the outcome."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--orig", type=Path, default=ROOT, help="original tree")
    parser.add_argument("--new", type=Path, default=ROOT / "documented", help="rewritten tree")
    parser.add_argument("--ruff", default=None, help="ruff executable")
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="subtree of --orig to ignore (repeatable); defaults to the rewritten "
        "tree plus refactored/ and arena/",
    )
    args = parser.parse_args(argv)

    excludes = args.exclude or sorted(
        {args.new.name if args.new.parent == args.orig else "", "refactored", "arena"} - {""}
    )
    ruff = ruff_path(args.ruff)
    original_histogram = lint_histogram(ruff, args.orig, excludes)
    rewritten_histogram = lint_histogram(ruff, args.new, [])

    print(f"originals  : {sum(original_histogram.values())} findings (excluding {', '.join(excludes)})")
    print(f"rewritten  : {sum(rewritten_histogram.values())} findings")

    introduced = {
        code: rewritten_histogram[code] - original_histogram[code]
        for code in set(original_histogram) | set(rewritten_histogram)
        if rewritten_histogram[code] != original_histogram[code]
    }
    if introduced:
        print("lint differences (code: delta):")
        for code, delta in sorted(introduced.items()):
            print(f"  {code}: {delta:+d}")
    else:
        print("lint histograms identical")

    originals = sorted(args.orig.glob("*.py"))
    rewritten = sorted(args.new.glob("*.py"))
    original_unformatted = format_targets(ruff, originals)
    rewritten_unformatted = format_targets(ruff, rewritten)
    differing = sorted(original_unformatted ^ rewritten_unformatted)

    print(f"format: {len(original_unformatted)} originals unformatted, "
          f"{len(rewritten_unformatted)} rewritten unformatted")
    if differing:
        print(f"format status differs for {len(differing)} files: {differing[:10]}")

    return 0 if not introduced and not differing else 1


if __name__ == "__main__":
    raise SystemExit(main())
