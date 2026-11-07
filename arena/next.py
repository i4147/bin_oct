#!/usr/bin/env python3
"""Show the next undocumented modules that still need an authored summary.

Usage:
    python arena/next.py --limit 15 [--source] [--offset 0]
"""

from __future__ import annotations
import argparse
import pathlib
import sys


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import apply_module_docs as docs  # noqa: E402
import gist  # noqa: E402
import signals  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--source", action="store_true", help="also print sources shorter than 70 lines")
    ap.add_argument("--only", default="", help="'weak' (no argparse description) or 'desc'")
    args = ap.parse_args(argv)
    summaries = docs.load_summaries()
    todo = []
    for path in sorted(p for p in pathlib.Path(".").glob("*.py") if p.is_file()):
        info = signals.analyse(path)
        if info["docstring"] or info["error"]:
            continue
        if path.name in summaries:
            continue
        if args.only == "weak" and info["parser_desc"]:
            continue
        if args.only == "desc" and not info["parser_desc"]:
            continue
        todo.append((path, info))
    print(f"# {len(todo)} module(s) still need a summary")
    for path, info in todo[args.offset : args.offset + args.limit]:
        print(gist.digest(path))
        if args.source and len(path.read_text().splitlines()) <= 70:
            print("  --- source ---")
            print("  " + path.read_text().rstrip().replace("\n", "\n  "))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
