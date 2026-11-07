#!/usr/bin/env python3
"""Dump compact structural signals for Python files in the repository.

Used to draft module docstrings during the documentation pass.

Usage:
    python arena/signals.py [--limit N] [--offset N] [--names a.py b.py]
"""

from __future__ import annotations
import argparse
import ast
import json
import pathlib


def _first_line(text):
    if not text:
        return ""
    for line in text.strip().splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def _const(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _arg_from_call(call):
    """Extract (flags, dest, help, default, action, choices) from parser.add_argument(...)."""
    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
        return None
    if call.func.attr not in ("add_argument", "add_option"):
        return None
    flags = []
    for a in call.args:
        v = _const(a)
        if isinstance(v, str):
            flags.append(v)
    kw = {k.arg: k.value for k in call.keywords if k.arg}
    info = {
        "flags": flags,
        "help": _first_line(_const(kw["help"])) if "help" in kw else "",
        "dest": _const(kw["dest"]) if "dest" in kw else "",
        "default": _const(kw["default"]) if "default" in kw else None,
        "action": _const(kw["action"]) if "action" in kw else "",
        "choices": _const(kw["choices"]) if "choices" in kw else None,
        "nargs": _const(kw["nargs"]) if "nargs" in kw else None,
        "required": _const(kw["required"]) if "required" in kw else None,
        "type": _const(kw["type"]) if "type" in kw else "",
    }
    return info


def analyse(path: pathlib.Path) -> dict:
    src = path.read_text(encoding="utf-8", errors="replace")
    lines = src.splitlines()
    info = {
        "file": path.name,
        "lines": len(lines),
        "shebang": lines[0] if lines and lines[0].startswith("#!") else "",
        "docstring": "",
        "comments": [],
        "imports": [],
        "defs": [],
        "classes": [],
        "constants": [],
        "parser_desc": "",
        "subcommands": [],
        "options": [],
        "main_calls": [],
        "decorated": [],
        "error": "",
    }
    # leading comment block
    for line in lines[1:] if info["shebang"] else lines:
        s = line.strip()
        if s.startswith("#") and not s.startswith("#!"):
            body = s.lstrip("#").strip()
            if body:
                info["comments"].append(body)
        elif s == "":
            continue
        else:
            break
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        info["error"] = f"{exc.msg} (line {exc.lineno})"
        return info
    info["docstring"] = ast.get_docstring(tree) or ""
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for a in node.names:
                    info["imports"].append(a.name.split(".")[0])
            else:
                info["imports"].append((node.module or "").split(".")[0] or ".")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sig = node.name + "(" + ", ".join(a.arg for a in node.args.args) + ")"
            info["defs"].append({
                "name": node.name,
                "sig": sig,
                "doc": _first_line(ast.get_docstring(node)),
                "decorators": [ast.unparse(d) for d in node.decorator_list],
                "priv": node.name.startswith("_"),
            })
        elif isinstance(node, ast.ClassDef):
            info["classes"].append({
                "name": node.name,
                "doc": _first_line(ast.get_docstring(node)),
                "bases": [ast.unparse(b) for b in node.bases],
            })
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    v = _const(node.value)
                    info["constants"].append(t.id if v is None else f"{t.id}={v!r}"[:80])
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id.isupper():
                info["constants"].append(node.target.id)
        elif isinstance(node, ast.If):
            test = ast.unparse(node.test)
            if "__main__" in test:
                for stmt in node.body:
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                        info["main_calls"].append(ast.unparse(stmt.value)[:100])
                    elif isinstance(stmt, ast.Assign):
                        info["main_calls"].append("assign " + ast.unparse(stmt)[:100])
                    elif isinstance(stmt, ast.For):
                        info["main_calls"].append(
                            "for " + ast.unparse(stmt.target) + " in " + ast.unparse(stmt.iter)[:80]
                        )
    # argparse details anywhere in tree
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            kw = {k.arg: k.value for k in node.keywords if k.arg}
            if name == "ArgumentParser":
                if "description" in kw:
                    info["parser_desc"] = _first_line(_const(kw["description"])) or ""
                elif node.args:
                    info["parser_desc"] = _first_line(_const(node.args[0])) or ""
            elif name == "add_parser":
                nm = _const(node.args[0]) if node.args else (_const(kw.get("name")) if "name" in kw else "")
                info["subcommands"].append({
                    "name": nm,
                    "help": _first_line(_const(kw["help"])) if "help" in kw else "",
                    "desc": _first_line(_const(kw["description"])) if "description" in kw else "",
                })
            elif name in ("add_argument", "add_option"):
                a = _arg_from_call(node)
                if a:
                    info["options"].append(a)
    # dedupe imports / constants short
    info["imports"] = sorted(set(i for i in info["imports"] if i))
    seen = set()
    opts = []
    for o in info["options"]:
        key = tuple(o["flags"])
        if key in seen:
            continue
        seen.add(key)
        opts.append(o)
    info["options"] = opts
    return info


def fmt(info: dict) -> str:
    if info["error"]:
        return f"## {info['file']} [PARSE ERROR: {info['error']}]"
    parts = [f"## {info['file']} ({info['lines']} lines)"]
    if info["docstring"]:
        parts.append("  doc: " + info["docstring"].strip().splitlines()[0])
    if info["comments"]:
        parts.append("  comments: " + " | ".join(info["comments"][:4])[:300])
    if info["parser_desc"]:
        parts.append("  argparse desc: " + info["parser_desc"][:300])
    if info["subcommands"]:
        subs = "; ".join(f"{s['name']}: {s['help'] or s['desc']}"[:90] for s in info["subcommands"])
        parts.append("  subcommands: " + subs[:600])
    if info["options"]:
        opts = "; ".join(
            (",".join(o["flags"])) + (f" ({o['help']})" if o["help"] else "")[:70] for o in info["options"][:12]
        )
        parts.append("  options: " + opts[:700])
    pub = [d for d in info["defs"] if not d["priv"]]
    if pub:
        parts.append(
            "  funcs: "
            + "; ".join(
                f"{d['name']}({')'.join([])}"[:0] or d["name"] + (f": {d['doc']}" if d["doc"] else "") for d in pub[:14]
            )
        )
    if info["classes"]:
        parts.append(
            "  classes: " + "; ".join(c["name"] + (f": {c['doc']}" if c["doc"] else "") for c in info["classes"][:8])
        )
    if info["constants"]:
        parts.append("  consts: " + ", ".join(info["constants"][:10]))
    if info["imports"]:
        parts.append("  imports: " + ", ".join(info["imports"][:18]))
    if info["main_calls"]:
        parts.append("  main: " + " ; ".join(info["main_calls"][:6])[:400])
    return "\n".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--names", nargs="*")
    args = ap.parse_args(argv)
    paths = sorted(p for p in pathlib.Path(".").glob("*.py") if p.is_file())
    if args.names:
        paths = [p for p in paths if p.name in args.names]
    infos = [analyse(p) for p in paths]
    if args.offset:
        infos = infos[args.offset :]
    if args.limit:
        infos = infos[: args.limit]
    if args.json:
        print(json.dumps(infos, indent=1, ensure_ascii=False))
    else:
        print("\n".join(fmt(i) for i in infos))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
