#!/usr/bin/env python3
"""Fix the small, mechanical errors found by the linter reports, in place.

SAFE by default: this script does a **dry run** and changes nothing.  Pass
``--apply`` to edit files.  Every file is re-compiled after editing and any
change that breaks it is reverted automatically.

What it fixes
-------------
stdlib (always available, no third-party dependency):
  * W291/W293  trailing whitespace / whitespace on blank lines
  * W292       missing (or duplicated) final newline
  * W605       invalid escape sequences in non-raw, non-f string literals,
               e.g. ``"\\d"`` -> ``"\\\\d"`` (identical value, no warning)

ruff (optional, auto-detected; skipped if ruff is not installed):
  * F401       unused imports
  * F541       f-string prefix with no placeholders

What it deliberately does NOT fix
---------------------------------
  * undefined names / broken call signatures (need human judgement)
  * PEP 695 ``type X = ...`` and PEP 701 multiline f-strings (need Python
    >= 3.12 or a real rewrite)
  * any file that does not already compile on the running interpreter
    (those are listed in the report as ``skipped_unparsable``)

Usage
-----
    python3 reports/fix_small_errors.py                    # dry run + report
    python3 reports/fix_small_errors.py --apply            # fix in place
    python3 reports/fix_small_errors.py --apply --backup   # keep .bak copies
    python3 reports/fix_small_errors.py --files a.py b.py  # limit scope
    python3 reports/fix_small_errors.py --no-ruff          # stdlib fixes only
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tokenize
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUFF_RULES = "F401,F541"          # ruff rules with safe, behaviour-preserving fixes
VALID_STR_ESCAPES = set("\\'\"abfnrtv01234567xuUN\n")
VALID_BYTES_ESCAPES = set("\\'\"abfnrtv01234567x\n")


def discover_files(root: pathlib.Path, only: list[str] | None
                   ) -> list[pathlib.Path]:
    if only:
        return [root / n for n in only if n.endswith(".py")]
    try:
        out = subprocess.run(["git", "ls-files", "*.py"], cwd=root,
                             capture_output=True, text=True, check=True,
                             timeout=30).stdout.splitlines()
        files = [root / p for p in out if "/" not in p and p.endswith(".py")]
    except (OSError, subprocess.SubprocessError):
        files = []
    if not files:
        files = [p for p in root.glob("*.py") if p.is_file()]
    return sorted(p for p in files if p.is_file())


def find_ruff(explicit: str | None) -> str | None:
    if explicit:
        return explicit if shutil.which(explicit) or os.path.isfile(explicit) else None
    found = shutil.which("ruff")
    if found:
        return found
    for d in (os.environ.get("ANALYSIS_TOOLS_DIR"),
              str(pathlib.Path.home() / ".venv" / "bin"),
              str(ROOT / ".venv" / "bin")):
        if d:
            p = pathlib.Path(d) / "ruff"
            if p.is_file() and os.access(p, os.X_OK):
                return str(p)
    return None


def compiles(text: str, filename: str) -> bool:
    try:
        compile(text, filename, "exec")
        return True
    except (SyntaxError, ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- #
# stdlib fixes
# --------------------------------------------------------------------------- #
def _multiline_string_lines(text: str) -> set[int]:
    """Physical lines whose trailing spaces are part of a string literal."""
    protected: set[int] = set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.STRING and tok.end[0] > tok.start[0]:
                # the first physical line of a triple-quoted string also holds
                # string content, so it must be protected too
                protected.update(range(tok.start[0], tok.end[0] + 1))
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        pass
    return protected


def fix_whitespace(text: str) -> tuple[str, int]:
    """Strip trailing whitespace and normalise the final newline."""
    lines = text.splitlines(keepends=True)
    protected = _multiline_string_lines(text)
    changed = 0
    out: list[str] = []
    for idx, ln in enumerate(lines, 1):
        if idx in protected:
            out.append(ln)
            continue
        if ln.endswith("\r\n"):
            body, eol = ln[:-2], "\r\n"
        elif ln.endswith("\n"):
            body, eol = ln[:-1], "\n"
        elif ln.endswith("\r"):
            body, eol = ln[:-1], "\r"
        else:
            body, eol = ln, ""
        stripped = body.rstrip(" \t")
        if stripped != body:
            changed += 1
        out.append(stripped + eol)
    new = "".join(out)
    eol = "\r\n" if "\r\n" in text and text.count("\r\n") > text.count("\n") / 2 else "\n"
    if not new:
        return "", changed
    while new.endswith("\n\n") or new.endswith("\r\n\r\n"):
        new = new[:-1] if new.endswith("\n\n") else new[:-2]
        changed += 1
    if not new.endswith(("\n", "\r")):
        new += eol
        changed += 1
    return new, changed


def _line_offsets(text: str) -> list[int]:
    offs, total = [0], 0
    for ln in text.splitlines(keepends=True):
        total += len(ln)
        offs.append(total)
    return offs


def fix_invalid_escapes(text: str) -> tuple[str, int]:
    """Double backslashes of invalid escapes inside normal string literals.

    ``"\\d"`` and ``"\\\\d"`` have the same value; the second one does not
    emit a SyntaxWarning / DeprecationWarning.  Raw strings and f-strings are
    left alone because editing their contents is not always semantics-safe.
    """
    offsets = _line_offsets(text)
    edits: list[tuple[int, int, str]] = []
    try:
        toks = tokenize.generate_tokens(io.StringIO(text).readline)
        for tok in toks:
            if tok.type != tokenize.STRING:
                continue
            s = tok.string
            # prefix = letters/r/b/u/f before the first quote
            q = re.search(r"['\"]", s)
            if not q:
                continue
            prefix = s[:q.start()].lower()
            if "r" in prefix or "f" in prefix:
                continue
            is_bytes = "b" in prefix
            quote = s[q.start()]
            triple = s[q.start():q.start() + 3] in ("'''", '"""')
            qlen = 3 if triple else 1
            body_start = q.start() + qlen
            body_end = len(s) - qlen
            body = s[body_start:body_end]
            valid = VALID_BYTES_ESCAPES if is_bytes else VALID_STR_ESCAPES
            out: list[str] = []
            i, count = 0, 0
            while i < len(body):
                ch = body[i]
                if ch == "\\" and i + 1 < len(body):
                    nxt = body[i + 1]
                    if nxt in valid:
                        out.append(body[i:i + 2])
                        i += 2
                        continue
                    out.append("\\\\")   # neutralise the invalid escape
                    count += 1
                    i += 1
                    continue
                out.append(ch)
                i += 1
            if not count:
                continue
            new_s = s[:body_start] + "".join(out) + s[body_end:]
            a = offsets[tok.start[0] - 1] + tok.start[1]
            b = offsets[tok.end[0] - 1] + tok.end[1]
            if text[a:b] == s:
                edits.append((a, b, new_s))
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        return text, 0
    for a, b, new_s in sorted(edits, reverse=True):
        text = text[:a] + new_s + text[b:]
    return text, len(edits)


def apply_stdlib(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    new, counts["W291/W292/W293"] = fix_whitespace(text)
    new, counts["W605"] = fix_invalid_escapes(new)
    return new, counts


def diff_line_count(a: str, b: str) -> int:
    return sum(1 for l in difflib.unified_diff(a.splitlines(), b.splitlines(), n=0)
               if l[:1] in "+-" and not l.startswith(("---", "+++")))


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=pathlib.Path, default=ROOT)
    ap.add_argument("--apply", action="store_true",
                    help="actually edit files in place (default: dry run)")
    ap.add_argument("--backup", action="store_true",
                    help="write <file>.bak before editing (only with --apply)")
    ap.add_argument("--no-ruff", action="store_true",
                    help="skip ruff-based fixes (F401, F541)")
    ap.add_argument("--ruff", default=None, help="path to the ruff binary")
    ap.add_argument("--files", nargs="*", default=None,
                    help="limit to these filenames (relative to --root)")
    ap.add_argument("--report", type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parent / "fix_report.json")
    ap.add_argument("--max-diff-lines", type=int, default=80)
    args = ap.parse_args()

    root = args.root.resolve()
    files = discover_files(root, args.files)
    ruff = None if args.no_ruff else find_ruff(args.ruff)
    mode = "apply" if args.apply else "dry-run"
    print(f"[{mode}] scanning {len(files)} .py files in {root}", flush=True)
    print(f"       ruff-based fixes: {'enabled (' + ruff + ')' if ruff else 'unavailable/skipped'}",
          flush=True)

    originals: dict[str, str] = {}
    skipped: list[dict[str, str]] = []
    for p in files:
        try:
            text = p.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as exc:
            skipped.append({"file": p.name, "reason": f"{type(exc).__name__}: {exc}"})
            continue
        if not compiles(text, p.name):
            skipped.append({"file": p.name,
                            "reason": "does not compile on this interpreter "
                                      "(e.g. Python 3.12-only syntax) — not touched"})
            continue
        originals[p.name] = text

    targets = [root / n for n in sorted(originals)]
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "mode": mode,
        "root": str(root),
        "python": sys.version.split()[0],
        "ruff": ruff,
        "rules": {
            "stdlib": ["W291/W292/W293 trailing whitespace / final newline",
                       "W605 invalid escape sequences"],
            "ruff": RUFF_RULES.split(",") if ruff else [],
            "never_attempted": [
                "undefined names", "broken call signatures",
                "PEP 695 `type` statements", "PEP 701 multiline f-strings",
                "any file that does not compile",
            ],
        },
        "skipped_unparsable": skipped,
        "files": [],
        "ruff_diff_preview": "",
    }

    # ------------------------------------------------------------ ruff phase
    ruff_changed: dict[str, bool] = {}
    if ruff and targets:
        cmd = [ruff, "check", "--no-cache", "--exit-zero", "--select", RUFF_RULES]
        cmd += (["--diff"] if not args.apply else ["--fix"])
        cmd += [p.name for p in targets]
        try:
            proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True,
                                  errors="replace", timeout=300)
            if not args.apply:
                diff_lines = proc.stdout.splitlines()
                report["ruff_diff_preview"] = "\n".join(
                    diff_lines[:args.max_diff_lines])
                for ln in diff_lines:
                    m = re.match(r"^--- (\S+\.py)$", ln)
                    if m:
                        ruff_changed[pathlib.Path(m.group(1)).name] = True
            else:
                for p in targets:
                    now = p.read_text(encoding="utf-8-sig")
                    ruff_changed[p.name] = now != originals[p.name]
                    if ruff_changed[p.name] and not compiles(now, p.name):
                        p.write_text(originals[p.name], encoding="utf-8")
                        ruff_changed[p.name] = False
        except (OSError, subprocess.SubprocessError) as exc:
            report["ruff_error"] = str(exc)

    # --------------------------------------------------------- stdlib phase
    total_lines_changed = 0
    rule_totals: dict[str, int] = {"W291/W292/W293": 0, "W605": 0}
    changed_files = 0
    for p in targets:
        name = p.name
        before = originals[name] if not args.apply else p.read_text(encoding="utf-8-sig")
        new, counts = apply_stdlib(before)
        differs = new != before
        if differs and not compiles(new, name):
            report["files"].append({
                "file": name, "applied": False,
                "reason": "proposed fix failed compile check — file left unchanged",
                "rules": counts, "ruff_changed": ruff_changed.get(name, False)})
            continue
        for k, v in counts.items():
            rule_totals[k] = rule_totals.get(k, 0) + v
        if differs or ruff_changed.get(name, False):
            changed_files += 1
            lines_changed = diff_line_count(before, new) if differs else 0
            total_lines_changed += lines_changed
        if args.apply and differs:
            if args.backup:
                bak = p.with_suffix(p.suffix + ".bak")
                bak.write_text(before, encoding="utf-8")
            mode_bits = p.stat().st_mode
            tmp = p.with_suffix(p.suffix + ".tmp-fix")
            tmp.write_text(new, encoding="utf-8")
            os.replace(tmp, p)
            os.chmod(p, mode_bits)
        report["files"].append({
            "file": name,
            "applied": bool(args.apply and (differs or ruff_changed.get(name, False))),
            "would_change": bool(differs or ruff_changed.get(name, False)),
            "stdlib_diff_lines": diff_line_count(before, new) if differs else 0,
            "rules": counts,
            "ruff_changed": ruff_changed.get(name, False),
            "sha256_before": hashlib.sha256(originals[name].encode()).hexdigest()[:16],
            "sha256_after": hashlib.sha256(
                (new if (differs or not args.apply) else before).encode()).hexdigest()[:16],
            "hash_note": ("dry run: ruff F401/F541 changes are not reflected in "
                          "sha256_after" if (not args.apply and
                                             ruff_changed.get(name)) else None),
        })

    report["summary"] = {
        "files_scanned": len(files),
        "files_eligible": len(targets),
        "files_skipped_unparsable": len(skipped),
        "files_changed_or_would_change": changed_files,
        "stdlib_lines_changed": total_lines_changed,
        "changes_by_rule": rule_totals,
        "ruff_files_changed": sum(1 for v in ruff_changed.values() if v),
        "mode": mode,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(f"       {changed_files} files {'changed' if args.apply else 'would change'}; "
          f"{len(skipped)} skipped (unparsable); "
          f"stdlib changes: {rule_totals}", flush=True)
    print(f"       report: {args.report}", flush=True)
    if not args.apply:
        print("       this was a DRY RUN — no file was modified. "
              "Re-run with --apply to fix in place.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
