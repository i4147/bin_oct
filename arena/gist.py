#!/usr/bin/env python3
"""Print a compact per-file digest used while authoring module docstrings.

For every selected module the digest shows the leading comment block, the
argparse description, subcommands, public functions/classes (with the first
line of their docstrings), module constants, and the body of the
``__main__`` block.  This is just enough context to describe the module
accurately in one or two sentences.

Usage:
    python arena/gist.py --offset 0 --limit 30
    python arena/gist.py --names afk2.py alu.py
    python arena/gist.py --offset 400 --limit 40 --full   # include string literals
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import signals  # noqa: E402


def key_stmts(stmts, depth=0, limit=12):
    """Return short unparsed forms of a statement list."""
    out = []
    for stmt in stmts:
        try:
            text = ast.unparse(stmt)
        except Exception:
            continue
        text = " ".join(text.split())
        if len(text) > 130:
            text = text[:127] + "..."
        out.append(text)
        if len(out) >= limit:
            break
    return out


def strings(tree, limit=12):
    vals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value.strip()
            if 2 <= len(v) <= 60 and "\n" not in v and not v.startswith("%"):
                if v not in vals:
                    vals.append(v)
    return vals[:limit]


def digest(path: pathlib.Path, full: bool = False) -> str:
    info = signals.analyse(path)
    src = path.read_text(encoding="utf-8", errors="replace")
    head = [f"### {path.name} ({info['lines']} lines)"]
    if info["error"]:
        head.append(f"  PARSE ERROR: {info['error']}")
        body = src.splitlines()[:40]
        head.append("  " + "\n  ".join(body))
        return "\n".join(head)
    tree = ast.parse(src)
    try:
        main_if = next(
            n for n in tree.body
            if isinstance(n, ast.If) and "__main__" in ast.unparse(n.test)
        )
        head.append("  main-block: " + " | ".join(key_stmts(main_if.body, limit=8)))
    except StopIteration:
        pass
    toplevel = key_stmts(
        [n for n in tree.body if not isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))],
        limit=8,
    )
    if toplevel:
        head.append("  toplevel: " + " | ".join(toplevel))
    if info["comments"]:
        head.append("  comments: " + " | ".join(info["comments"][:3])[:200])
    if info["parser_desc"]:
        head.append("  desc: " + info["parser_desc"][:200])
    if info["subcommands"]:
        head.append(
            "  subs: " + "; ".join(f"{s['name']}={s['help'] or s['desc']}"[:80] for s in info["subcommands"])[:400]
        )
    if info["options"]:
        head.append(
            "  opts: "
            + "; ".join(",".join(o["flags"]) + (f":{o['help']}" if o["help"] else "") for o in info["options"])[:500]
        )
    if info["defs"]:
        head.append(
            "  funcs: "
            + "; ".join(d["name"] + (f"[{d['doc'][:60]}]" if d["doc"] else "") for d in info["defs"][:18])
        )
    if info["classes"]:
        head.append("  classes: " + "; ".join(c["name"] + (f"[{c['doc'][:50]}]" if c["doc"] else "") for c in info["classes"][:8]))
    if info["imports"]:
        head.append("  imports: " + ",".join(info["imports"][:16]))
    if full:
        s = strings(tree)
        if s:
            head.append("  strings: " + " | ".join(s))
    return "\n".join(head)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--names", nargs="*")
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args(argv)
    paths = sorted(p for p in pathlib.Path(".").glob("*.py") if p.is_file())
    paths = [p for p in paths if not signals.analyse(p)["docstring"]]
    if args.names:
        paths = [p for p in paths if p.name in args.names]
    else:
        paths = paths[args.offset : args.offset + args.limit]
    print("\n".join(digest(p, args.full) for p in paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
