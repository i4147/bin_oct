#!/usr/bin/env python3
"""Insert module docstrings into the repository's Python scripts.

Prose lives in ``arena/summaries/*.json``, keyed by file name::

    {"afk.py": {"summary": "Find unused imports ...",
                "details": ["Longer explanation ..."],
                "usage": "afk [options] [paths ...]",
                "example": ["$ afk src/ --check"]}}

Everything that can be derived from the module itself is generated: the usage
line, positional arguments, option flags with their help strings, subcommands,
a fallback example and an entry-point note.

Usage:
    python arena/apply_module_docs.py --show afk.py
    python arena/apply_module_docs.py --write
    python arena/apply_module_docs.py --check
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUMMARY_DIR = ROOT / "arena" / "summaries"
WRAP = 88
OPTION_LIMIT = 10
DANGLING = re.compile(r"[\(\[\{,;:]\s*(?:e\.g\.|i\.e\.|etc\.)?\s*$")


def load_summaries() -> dict[str, dict]:
    data: dict[str, dict] = {}
    if SUMMARY_DIR.is_dir():
        for path in sorted(SUMMARY_DIR.glob("*.json")):
            data.update(json.loads(path.read_text(encoding="utf-8")))
    return data


def _clean(text: str) -> str:
    return " ".join(str(text or "").split())


def _capitalize(text: str) -> str:
    if text and text[0].islower():
        return text[0].upper() + text[1:]
    return text


def _shorten(text: str, limit: int = 220) -> str:
    """Trim a help string on a sentence or word boundary."""
    text = _clean(text)
    if len(text) <= limit:
        return text
    head = text[:limit]
    for sep in (". ", "? ", "! "):
        idx = head.rfind(sep)
        if idx > 40:
            return head[: idx + 1]
    cut = head.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:") + "..."


def _tidy_help(text: str) -> str:
    text = _shorten(_clean(text))
    text = DANGLING.sub("", text).strip()
    text = text.rstrip()
    return _capitalize(text)


def collect(tree: ast.AST) -> dict:
    """Collect parser description, positionals, options and subcommands."""
    info: dict = {"desc": "", "positionals": [], "options": [], "subs": []}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        kw = {k.arg: k.value for k in node.keywords if k.arg}

        def const(key):
            if key not in kw:
                return None
            try:
                return ast.literal_eval(kw[key])
            except Exception:
                return None

        if name == "ArgumentParser":
            desc = const("description")
            if desc is None and node.args:
                try:
                    desc = ast.literal_eval(node.args[0])
                except Exception:
                    desc = None
            if isinstance(desc, str) and desc.strip() and desc.strip() != "__doc__":
                info["desc"] = _clean(desc)
        elif name == "add_argument":
            flags = []
            for arg in node.args:
                try:
                    value = ast.literal_eval(arg)
                except Exception:
                    continue
                if isinstance(value, str):
                    flags.append(value)
            if not flags:
                continue
            help_text = const("help")
            entry = {
                "flags": flags,
                "help": _tidy_help(help_text) if isinstance(help_text, str) else "",
                "nargs": const("nargs"),
                "required": bool(const("required")),
            }
            if flags[0].startswith("-"):
                info["options"].append(entry)
            else:
                info["positionals"].append(entry)
        elif name == "add_parser":
            sub = const("name")
            if sub is None and node.args:
                try:
                    sub = ast.literal_eval(node.args[0])
                except Exception:
                    sub = None
            if not isinstance(sub, str):
                continue
            help_text = const("help") or const("description")
            info["subs"].append(
                {"name": sub, "help": _tidy_help(help_text) if isinstance(help_text, str) else ""}
            )

    def dedup(entries):
        seen, out = set(), []
        for entry in entries:
            key = tuple(entry["flags"])
            if key in seen or set(entry["flags"]) <= {"-h", "--help"}:
                continue
            seen.add(key)
            out.append(entry)
        return out

    info["options"] = dedup(info["options"])
    info["positionals"] = dedup(info["positionals"])
    seen, subs = set(), []
    for sub in info["subs"]:
        if sub["name"] in seen:
            continue
        seen.add(sub["name"])
        subs.append(sub)
    info["subs"] = subs
    return info


def usage_lines(prog: str, cli: dict, override: str | None) -> list[str]:
    if override:
        return [override.strip()]
    if cli["subs"]:
        names = "|".join(s["name"] for s in cli["subs"][:4])
        more = "|..." if len(cli["subs"]) > 4 else ""
        return [f"{prog} [options] <{names}{more}> [args ...]"]
    parts = [prog]
    if cli["options"]:
        parts.append("[options]")
    for pos in cli["positionals"]:
        name = pos["flags"][0].upper() if pos["nargs"] in ("*", "+") else pos["flags"][0]
        if pos["nargs"] in ("*", "+"):
            name += " ..."
        parts.append(name if pos["required"] else f"[{name}]")
    return [" ".join(parts)]


def _wrap(text: str, indent: str = "") -> list[str]:
    """Wrap text at ``WRAP`` columns, keeping ``double-backtick`` spans intact."""
    spans: list[str] = []

    def protect(match: re.Match) -> str:
        spans.append(match.group(0))
        return "\x00%d\x01" % (len(spans) - 1)

    masked = re.sub(r"``.+?``", protect, text)
    out = textwrap.wrap(
        masked,
        width=WRAP,
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return [re.sub(r"\x00(\d+)\x01", lambda m: spans[int(m.group(1))], line) for line in out]


def build_docstring(prog: str, meta: dict, cli: dict) -> str:
    summary = _clean(meta.get("summary") or cli["desc"])
    if not summary:
        raise SystemExit(f"missing summary for {prog}.py")
    if not summary.endswith((".", "?", "!")):
        summary += "."
    lines = ['"""' + summary]
    for para in meta.get("details") or []:
        lines.append("")
        lines.extend(_wrap(_clean(para)))

    lines.append("")
    usage = usage_lines(prog, cli, meta.get("usage"))
    lines.extend(_wrap("Usage: " + usage[0]))
    for extra in usage[1:]:
        lines.extend(_wrap(extra, "    "))

    if cli["positionals"] or meta.get("positionals_note"):
        lines.append("")
        lines.append("Positional arguments:")
        for pos in cli["positionals"]:
            name = pos["flags"][0]
            if pos["nargs"] in ("*", "+"):
                name += " ..."
            lines.append("    " + name)
            if pos["help"]:
                lines.extend(_wrap(pos["help"], "        "))
        if meta.get("positionals_note"):
            lines.extend(_wrap(_clean(meta["positionals_note"]), "    "))

    if cli["subs"]:
        lines.append("")
        lines.append("Subcommands:")
        for sub in cli["subs"]:
            lines.append("    " + sub["name"])
            if sub["help"]:
                lines.extend(_wrap(sub["help"], "        "))

    if cli["options"]:
        lines.append("")
        lines.append("Options:")
        for opt in cli["options"][:OPTION_LIMIT]:
            lines.append("    " + ", ".join(opt["flags"]))
            if opt["help"]:
                lines.extend(_wrap(opt["help"], "        "))
        rest = len(cli["options"]) - OPTION_LIMIT
        if rest > 0:
            lines.append(f"    ... plus {rest} more; run ``{prog} --help`` for the full list.")

    examples = meta.get("example") or []
    if isinstance(examples, str):
        examples = [examples]
    if not examples:
        placeholders = [
            (p["flags"][0].upper() if p["nargs"] in ("*", "+") else p["flags"][0])
            for p in cli["positionals"]
        ]
        if placeholders:
            examples.append("$ " + prog + " " + " ".join(placeholders))
        if cli["subs"]:
            examples.append(f"$ {prog} {cli['subs'][0]['name']} --help")
        else:
            examples.append(f"$ {prog} --help")
    if examples:
        lines.append("")
        lines.append("Examples:")
        for example in examples:
            lines.extend(_wrap(_clean(example), "    "))

    note = meta.get("notes")
    if note is None:
        if cli["subs"] or cli["options"] or cli["positionals"]:
            note = (
                f"Command-line script: run ``python {prog}.py`` or the ``{prog}`` "
                "command. The module is importable as well."
            )
        else:
            note = (
                f"Runs as a script (``python {prog}.py``) in the directory it should "
                "act on; the module can also be imported."
            )
    if note:
        lines.append("")
        lines.extend(_wrap(_clean(note)))
    lines.append('"""')
    return _escape_docstring("\n".join(lines))


def _escape_docstring(text: str) -> str:
    """Escape the backslashes and the triple quotes of a generated docstring."""
    inner = text[3:-3]
    inner = inner.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    if inner.endswith('"'):
        inner = inner[:-1] + '\\"'
    return '"""' + inner + '"""'


def insert_docstring(src: str, docstring: str) -> str:
    lines = src.splitlines(keepends=True)
    idx = 0
    if lines and lines[0].startswith("#!"):
        idx = 1
    if idx < len(lines) and lines[idx].lstrip().startswith("#") and "coding" in lines[idx]:
        idx += 1
    head = "".join(lines[:idx])
    tail = "".join(lines[idx:])
    if head and not head.endswith("\n"):
        head += "\n"
    body = docstring + "\n"
    if tail and not tail.startswith("\n"):
        body += "\n"
    return head + body + tail


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="write the docstrings in place")
    ap.add_argument("--check", action="store_true", help="only report files without a docstring")
    ap.add_argument("--show", nargs="*", help="print the generated docstring for these files")
    args = ap.parse_args(argv)
    summaries = load_summaries()
    paths = sorted(p for p in ROOT.glob("*.py") if p.is_file())
    if args.show:
        paths = [p for p in paths if p.name in args.show]
    missing, written, skipped, unsummarised = [], [], [], []
    for path in paths:
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
            has_doc = bool(ast.get_docstring(tree))
        except SyntaxError:
            missing.append(path.name + " (unparsable)")
            continue
        if has_doc:
            skipped.append(path.name)
            continue
        missing.append(path.name)
        meta = summaries.get(path.name)
        if meta is None:
            unsummarised.append(path.name)
            continue
        cli = collect(tree)
        doc = build_docstring(path.stem, meta, cli)
        if args.show:
            print(doc + "\n")
        if args.write:
            path.write_text(insert_docstring(src, doc), encoding="utf-8")
            written.append(path.name)
    if args.check:
        print(f"{len(missing)} file(s) without a module docstring")
        print("\n".join(missing))
    if args.write:
        print(f"wrote {len(written)} docstring(s); skipped {len(skipped)} already documented")
        if unsummarised:
            print(f"still missing a summary: {len(unsummarised)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
