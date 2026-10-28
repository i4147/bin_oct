#!/usr/bin/env python3
"""Run ruff, pylint, mypy and ty over the standalone scripts and build reports.

The point of this pass is to find errors that *stop a script from running*:
syntax errors, undefined names, illegal control flow and broken call
signatures.  Import problems caused by modules that are not installed are
explicitly excluded (they are an environment issue, not a code defect).

Nothing is executed: every script is only read, parsed and statically checked.

Outputs (in --out-dir, default: directory of this script):

    ruff_report.json        every ruff diagnostic
    pylint_report.json      every pylint diagnostic
    mypy_report.json        every mypy diagnostic
    ty_report.json          every ty diagnostic
    blocking_errors.json    unified, de-duplicated blocking error report
    error_report.md         readable summary of all of the above
    raw/                    untouched stdout of each tool (audit trail)

Usage:
    python3 run_error_checks.py                       # auto-detect tools
    python3 run_error_checks.py --tools-dir /path/to/bin
    python3 run_error_checks.py --skip pylint        # skip one slow tool

Install the tools once with:
    python3 -m venv .venv && .venv/bin/pip install ruff pylint mypy ty
"""

from __future__ import annotations

import argparse
import ast
import collections
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_KINDS = ("ruff", "pylint", "mypy", "ty")

# Exact tool invocations (file names are appended at run time).  Kept here so
# the full run and `--from-raw` report the same, reproducible command.
TOOL_PREFIX = {
    "ruff": ["check"],
    "pylint": [],
    "mypy": [],
    "ty": ["check"],
}
COMMAND_FLAGS = {
    "ruff": ["--no-cache", "--exit-zero", "--target-version", "py311",
             "--output-format", "json", "--select", "E4,E7,E9,F,W,PLE,B"],
    "pylint": ["--exit-zero", "--reports=n", "--score=n",
               "--output-format=json2", "--disable=all", "--enable=E,F,W",
               "--disable=E0401,E0611,W0611,W0612,W0613,W0621,W0703,W0718,"
               "W1514,W3101,W0719,W0123,W0102,W0122"],
    "mypy": ["--no-incremental", "--cache-dir=/tmp/bin_oct_mypy_cache",
             "--no-color-output", "--no-error-summary", "--show-column-numbers",
             "--show-error-codes", "--ignore-missing-imports",
             "--follow-imports=skip", "--scripts-are-modules",
             "--check-untyped-defs", "--python-version", "3.11"],
    "ty": ["--output-format", "concise", "--no-progress",
           "--no-respect-ignore-files", "--python-version", "3.11", "--exit-zero"],
}

# --------------------------------------------------------------------------- #
# classification policy
# --------------------------------------------------------------------------- #
# (category, tier, suggested_fix).  tier: blocking / runtime_risk / non_blocking
FIX = {
    "syntax_error": "Fix the syntax error. If it is PEP 695/701 syntax, use "
                    "Python >= 3.12 or rewrite it for 3.11.",
    "undefined_name": "Define or import the missing name, or delete the reference.",
    "call_signature": "Correct the call: supply missing arguments / remove "
                      "extra or unknown ones / call a callable object.",
    "invalid_flow": "Move the return / yield / break / continue into a valid scope.",
    "invalid_expression": "Rewrite the invalid expression or f-string.",
    "attribute_error": "Guard the attribute/subscript access or fix the value type.",
    "type_mismatch": "Align the value with the declared/expected type.",
    "redefinition": "Remove or rename the duplicate definition.",
}

BLOCKING_RULES: dict[str, dict[str, tuple[str, str]]] = {
    "ruff": {
        "invalid-syntax": ("syntax_error", "blocking"),
        "E902": ("syntax_error", "blocking"),
        "E999": ("syntax_error", "blocking"),
        "F821": ("undefined_name", "blocking"),
        "F822": ("undefined_name", "blocking"),
        "F823": ("undefined_name", "blocking"),
        "F701": ("invalid_flow", "blocking"),
        "F702": ("invalid_flow", "blocking"),
        "F703": ("invalid_flow", "blocking"),
        "F704": ("invalid_flow", "blocking"),
        "F705": ("invalid_flow", "blocking"),
        "F706": ("invalid_flow", "blocking"),
        "F707": ("invalid_flow", "blocking"),
        "F621": ("invalid_expression", "blocking"),
        "F622": ("invalid_expression", "blocking"),
        "F623": ("invalid_expression", "blocking"),
        "F631": ("invalid_expression", "blocking"),
        "F632": ("invalid_expression", "blocking"),
        "F633": ("invalid_expression", "blocking"),
        "F634": ("invalid_flow", "blocking"),
        "PLE0100": ("invalid_flow", "blocking"),
        "PLE0101": ("invalid_flow", "blocking"),
        "PLE0116": ("invalid_flow", "blocking"),
        "PLE0117": ("undefined_name", "blocking"),
        "PLE0118": ("undefined_name", "blocking"),
        "PLE0604": ("invalid_expression", "blocking"),
        "PLE0605": ("invalid_expression", "blocking"),
        "F811": ("redefinition", "runtime_risk"),
    },
    "pylint": {
        "E0001": ("syntax_error", "blocking"),
        "E0601": ("undefined_name", "blocking"),
        "E0602": ("undefined_name", "blocking"),
        "E0603": ("undefined_name", "blocking"),
        "E0604": ("undefined_name", "blocking"),
        "E0606": ("undefined_name", "blocking"),
        "E0100": ("invalid_flow", "blocking"),
        "E0101": ("invalid_flow", "blocking"),
        "E0104": ("invalid_flow", "blocking"),
        "E0105": ("invalid_flow", "blocking"),
        "E0106": ("invalid_flow", "blocking"),
        "E0107": ("invalid_expression", "blocking"),
        "E0110": ("call_signature", "blocking"),
        "E0112": ("invalid_expression", "blocking"),
        "E0115": ("undefined_name", "blocking"),
        "E0117": ("undefined_name", "blocking"),
        "E1120": ("call_signature", "blocking"),
        "E1121": ("call_signature", "blocking"),
        "E1123": ("call_signature", "blocking"),
        "E1124": ("call_signature", "blocking"),
        "E1102": ("call_signature", "blocking"),
        "E0102": ("redefinition", "runtime_risk"),
        "E1101": ("attribute_error", "runtime_risk"),
        "E1135": ("attribute_error", "runtime_risk"),
        "E1136": ("attribute_error", "runtime_risk"),
    },
    "mypy": {
        "syntax": ("syntax_error", "blocking"),
        "name-defined": ("undefined_name", "blocking"),
        "used-before-def": ("undefined_name", "blocking"),
        "call-arg": ("call_signature", "blocking"),
        "no-redef": ("redefinition", "runtime_risk"),
        "attr-defined": ("attribute_error", "runtime_risk"),
        "union-attr": ("attribute_error", "runtime_risk"),
        "index": ("attribute_error", "runtime_risk"),
        "operator": ("type_mismatch", "runtime_risk"),
        "assignment": ("type_mismatch", "runtime_risk"),
        "arg-type": ("type_mismatch", "runtime_risk"),
        "var-annotated": ("type_mismatch", "runtime_risk"),
        "func-returns-value": ("type_mismatch", "runtime_risk"),
        "return-value": ("type_mismatch", "runtime_risk"),
        "call-overload": ("call_signature", "runtime_risk"),
        "misc": ("type_mismatch", "runtime_risk"),
        "valid-type": ("type_mismatch", "runtime_risk"),
        "override": ("type_mismatch", "runtime_risk"),
        "dict-item": ("type_mismatch", "runtime_risk"),
        "return": ("type_mismatch", "runtime_risk"),
        "str-bytes-safe": ("type_mismatch", "runtime_risk"),
        "type-var": ("type_mismatch", "runtime_risk"),
        "truthy-function": ("type_mismatch", "runtime_risk"),
        "exit-return": ("type_mismatch", "runtime_risk"),
    },
    "ty": {
        "invalid-syntax": ("syntax_error", "blocking"),
        "unresolved-reference": ("undefined_name", "blocking"),
        "missing-argument": ("call_signature", "blocking"),
        "too-many-positional-arguments": ("call_signature", "blocking"),
        "unknown-argument": ("call_signature", "blocking"),
        "call-non-callable": ("call_signature", "blocking"),
        "invalid-yield": ("invalid_flow", "blocking"),
        "invalid-context-manager": ("attribute_error", "blocking"),
        "not-iterable": ("attribute_error", "runtime_risk"),
        "not-subscriptable": ("attribute_error", "runtime_risk"),
        "no-matching-overload": ("call_signature", "runtime_risk"),
        "unresolved-attribute": ("attribute_error", "runtime_risk"),
        "invalid-argument-type": ("type_mismatch", "runtime_risk"),
        "invalid-assignment": ("type_mismatch", "runtime_risk"),
        "invalid-return-type": ("type_mismatch", "runtime_risk"),
        "unsupported-operator": ("type_mismatch", "runtime_risk"),
        "invalid-method-override": ("type_mismatch", "runtime_risk"),
        "invalid-attribute-override": ("type_mismatch", "runtime_risk"),
        "invalid-type-form": ("type_mismatch", "runtime_risk"),
        "invalid-parameter-default": ("type_mismatch", "runtime_risk"),
    },
}

IMPORT_RE = re.compile(
    r"(?i)(no module named|cannot resolve imported module|cannot find implementation "
    r"or library stub|skipping analyzing|unresolved-import|import-error|"
    r"no-name-in-module|import-not-found|import-untyped|cannot import .* due to |"
    r"missing (?:library )?stubs|dependency .*not installed|module .*not found|"
    r"is not installed|unable to import|c-extension-no-module)"
)

# Codes that are *always* about imports, even when the wording varies.
IMPORT_CODES = {
    ("ty", "unresolved-import"),
    ("pylint", "E0401"),
    ("pylint", "E0611"),
    ("mypy", "import-not-found"),
    ("mypy", "import-untyped"),
    ("mypy", "import"),
    ("ruff", "F401"),          # unused import: non-blocking, import-related
}

NAME_RE = re.compile(r"[`'\"]([A-Za-z_][A-Za-z0-9_.]*)[`'\"]")


def classify(tool: str, code: str, message: str) -> tuple[str, str, str]:
    """Return (tier, category, reason)."""
    if (tool, code) == ("ruff", "F401"):
        return "ignored_import", "import_issue", "unused import (import-related, non-blocking)"
    if (tool, code) in IMPORT_CODES or IMPORT_RE.search(message or ""):
        return "ignored_import", "import_issue", "missing / unresolvable module (excluded by request)"
    entry = BLOCKING_RULES.get(tool, {}).get(code)
    if entry:
        return entry[1], entry[0], ""
    return "non_blocking", "other", ""


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def discover_files(root: pathlib.Path) -> list[pathlib.Path]:
    try:
        out = subprocess.run(["git", "ls-files", "*.py"], cwd=root,
                             capture_output=True, text=True, check=True,
                             timeout=30).stdout.splitlines()
        files = [root / p for p in out if "/" not in p and p.endswith(".py")]
    except (OSError, subprocess.SubprocessError):
        files = []
    if not files:
        files = [p for p in root.glob("*.py") if p.is_file()]
    return sorted(files)


def find_tools(arg: str | None) -> dict[str, str]:
    candidates: list[pathlib.Path] = []
    if arg:
        candidates.append(pathlib.Path(arg))
    if os.environ.get("ANALYSIS_TOOLS_DIR"):
        candidates.append(pathlib.Path(os.environ["ANALYSIS_TOOLS_DIR"]))
    candidates += [pathlib.Path.home() / ".venv" / "bin",
                   ROOT / ".venv" / "bin", pathlib.Path("/usr/local/bin")]
    tools: dict[str, str] = {}
    for name in OUT_KINDS:
        found = shutil.which(name)
        if not found:
            for d in candidates:
                p = d / name
                if p.is_file() and os.access(p, os.X_OK):
                    found = str(p)
                    break
        if found:
            tools[name] = found
    return tools


def version_of(path: str) -> str:
    try:
        out = subprocess.run([path, "--version"], capture_output=True,
                             text=True, timeout=20)
        return (out.stdout or out.stderr).strip().splitlines()[0][:100]
    except (OSError, subprocess.SubprocessError, IndexError):
        return "unknown"


def run(cmd: list[str], cwd: pathlib.Path, timeout: int = 1200
        ) -> tuple[str, str, int]:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       errors="replace", timeout=timeout)
    return p.stdout, p.stderr, p.returncode


def rel(path: str, root: pathlib.Path) -> str:
    try:
        return str(pathlib.Path(path).resolve().relative_to(root))
    except (ValueError, OSError):
        return pathlib.Path(path).name


def diag(tool: str, file: str, line: int, col: int, code: str, symbol: str,
         message: str, severity: str = "error", fixable: bool = False,
         extra: dict[str, Any] | None = None) -> dict[str, Any]:
    d: dict[str, Any] = {
        "tool": tool, "file": file, "line": line, "column": col,
        "code": code, "symbol": symbol, "severity": severity,
        "message": message.strip(), "fixable": fixable,
    }
    tier, category, reason = classify(tool, code, message)
    d["tier"] = tier
    d["category"] = category
    if reason:
        d["classification_reason"] = reason
    if extra:
        d.update(extra)
    return d


def write_json(path: pathlib.Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


# --------------------------------------------------------------------------- #
# parsers
# --------------------------------------------------------------------------- #
def parse_ruff(raw: str, root: pathlib.Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    out = []
    for x in data:
        code = x.get("code") or x.get("name") or "invalid-syntax"
        loc = x.get("location") or {}
        out.append(diag(
            "ruff", rel(x.get("filename", ""), root),
            int(loc.get("row") or 1), int(loc.get("column") or 1),
            code, x.get("name") or "", x.get("message", ""),
            x.get("severity", "error"),
            fixable=bool(x.get("fix")),
            extra={"fix_applicability": (x.get("fix") or {}).get("applicability")},
        ))
    return out


def parse_pylint(raw: str, root: pathlib.Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return []
    msgs = data.get("messages", []) if isinstance(data, dict) else data
    out = []
    for x in msgs:
        code = x.get("messageId") or x.get("symbol") or ""
        msg = x.get("message", "")
        # E0001 also covers "Cannot import X due to ..." which is an import
        # problem, not a syntax error in the reported file.
        if code == "E0001" and not msg.lower().startswith("parsing failed"):
            code, msg = "IMPORT-CASCADE", msg
        out.append(diag(
            "pylint", rel(x.get("path") or x.get("absolutePath") or "", root),
            int(x.get("line") or 1), int(x.get("column") or 1),
            code, x.get("symbol") or "", msg, x.get("type", "error"),
            extra={"confidence": x.get("confidence")},
        ))
    return out


MYPY_RE = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+)(?::(?P<col>\d+))?: "
    r"(?P<sev>error|warning|note): (?P<msg>.*?)"
    r"(?:\s{2}\[(?P<code>[a-z0-9-]+)\])?$"
)


def parse_mypy(raw: str, root: pathlib.Path) -> list[dict[str, Any]]:
    out = []
    for line in (raw or "").splitlines():
        m = MYPY_RE.match(line.strip())
        if not m:
            continue
        sev = m.group("sev")
        if sev == "note":
            continue
        code = m.group("code") or "other"
        out.append(diag("mypy", rel(m.group("file"), root),
                        int(m.group("line")), int(m.group("col") or 1),
                        code, code, m.group("msg"), sev))
    return out


TY_RE = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+): "
    r"(?P<sev>error|warning)\[(?P<code>[a-z0-9-]+)\] (?P<msg>.*)$"
)


def parse_ty(raw: str, root: pathlib.Path) -> list[dict[str, Any]]:
    out = []
    for line in (raw or "").splitlines():
        m = TY_RE.match(line.strip())
        if not m:
            continue
        out.append(diag("ty", rel(m.group("file"), root),
                        int(m.group("line")), int(m.group("col")),
                        m.group("code"), m.group("code"), m.group("msg"),
                        m.group("sev")))
    return out


# --------------------------------------------------------------------------- #
# ground-truth checks
# --------------------------------------------------------------------------- #
def compile_check(files: list[pathlib.Path], root: pathlib.Path
                  ) -> list[dict[str, Any]]:
    """CPython 3.11 parse/compile is the ground truth for 'cannot start'."""
    problems = []
    for p in files:
        try:
            raw = p.read_bytes()
        except OSError as exc:
            problems.append({"file": p.name, "kind": type(exc).__name__,
                             "line": 0, "message": str(exc),
                             "requires_python_312": False})
            continue
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            problems.append({"file": p.name, "kind": "UnicodeDecodeError",
                             "line": 0, "message": str(exc),
                             "requires_python_312": False})
            continue
        try:
            compile(text, p.name, "exec")
        except (SyntaxError, ValueError) as exc:
            line = exc.lineno if isinstance(exc, SyntaxError) else 0
            msg = exc.msg if isinstance(exc, SyntaxError) else str(exc)
            problems.append({"file": p.name, "kind": type(exc).__name__,
                             "line": line or 0, "message": msg,
                             "requires_python_312": False})
    return problems


def cli_wrapped_names(files: list[pathlib.Path]
                      ) -> dict[str, set[str]]:
    """Functions wrapped by click/typer: their call signature is injected."""
    out: dict[str, set[str]] = {}
    for p in files:
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError, ValueError):
            continue
        names: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                d = _dotted(dec.func) if isinstance(dec, ast.Call) else _dotted(dec)
                low = d.lower()
                if (low.startswith(("click.", "typer.")) or
                        low.endswith((".command", ".group")) or
                        low in ("command", "group")):
                    names.add(node.name)
        if names:
            out[p.name] = names
    return out


def _dotted(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def module_level(files: list[pathlib.Path], root: pathlib.Path
                 ) -> dict[str, list[tuple[int, int]]]:
    """Line ranges of function bodies, for startup-vs-later classification."""
    ranges: dict[str, list[tuple[int, int]]] = {}
    for p in files:
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError, ValueError):
            ranges[p.name] = []
            continue
        spans = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.Lambda, ast.ClassDef)):
                lo = getattr(node, "lineno", 0)
                hi = getattr(node, "end_lineno", lo) or lo
                spans.append((lo, hi))
        ranges[p.name] = spans
    return ranges


# --------------------------------------------------------------------------- #
# report assembly
# --------------------------------------------------------------------------- #
def per_tool_report(tool: str, version: str, command: list[str],
                    diagnostics: list[dict[str, Any]], files: int,
                    rc: int, stderr: str, config: dict[str, Any]
                    ) -> dict[str, Any]:
    tiers = collections.Counter(d["tier"] for d in diagnostics)
    rules = collections.Counter(f"{d['code']}" for d in diagnostics)
    cmd = list(command)
    for i, c in enumerate(cmd):
        if str(c).endswith(".py"):
            cmd = cmd[:i] + [f"<{files} .py files>"]
            break
    cmd_text = " ".join(str(c) for c in cmd)
    if len(cmd_text) > 900:
        cmd_text = cmd_text[:900] + " ..."
    return {
        "tool": tool,
        "version": version,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "command": cmd_text,
        "config": config,
        "exit_code": rc,
        "stderr_tail": stderr.strip()[-800:],
        "files_analyzed": files,
        "total_diagnostics": len(diagnostics),
        "by_tier": dict(tiers),
        "by_rule": dict(rules.most_common()),
        "files_with_blocking_issues": len({d["file"] for d in diagnostics
                                           if d["tier"] == "blocking"}),
        "diagnostics": diagnostics,
    }


def build_blocking_report(files: list[pathlib.Path], root: pathlib.Path,
                          all_diags: dict[str, list[dict[str, Any]]],
                          compile_problems: list[dict[str, Any]],
                          confirmed_312: set[str],
                          tool_meta: dict[str, Any],
                          threshold_note: str) -> dict[str, Any]:
    flat = [d for ds in all_diags.values() for d in ds]
    ignored = [d for d in flat if d["tier"] == "ignored_import"]
    blocking_src = [d for d in flat if d["tier"] == "blocking"]
    risk_src = [d for d in flat if d["tier"] == "runtime_risk"]

    func_spans = module_level(files, root)
    syntax_files = {p["file"] for p in compile_problems}

    # ---- false-positive filter #1: click/typer decorated entry points -----
    wrapped = cli_wrapped_names(files)
    source_cache: dict[str, list[str]] = {}
    def line_text(file: str, line: int) -> str:
        if file not in source_cache:
            try:
                source_cache[file] = (root / file).read_text(
                    encoding="utf-8", errors="replace").splitlines()
            except OSError:
                source_cache[file] = []
        ls = source_cache[file]
        return ls[line - 1] if 0 < line <= len(ls) else ""
    dropped = 0
    for d in blocking_src + risk_src:
        if d["category"] not in ("call_signature", "type_mismatch"):
            continue
        names = wrapped.get(d["file"], set())
        if not names:
            continue
        src = line_text(d["file"], d["line"])
        if any(re.search(r"\b" + re.escape(n) + r"\s*\(", src) for n in names):
            d["tier"] = "non_blocking"
            d["category"] = "false_positive_filtered"
            d["classification_reason"] = (
                "call to a click/typer-wrapped entry point; the decorator "
                "injects the signature, pylint/mypy/ty cannot infer it")
            dropped += 1
    blocking_src = [d for d in blocking_src if d["tier"] == "blocking"]
    risk_src = [d for d in risk_src if d["tier"] == "runtime_risk"]

    def when(file: str, line: int) -> str:
        """A module-level failure stops startup; one inside a def is deferred."""
        if file in syntax_files:
            return "startup"
        for lo, hi in func_spans.get(file, []):
            if lo <= line <= hi:
                return "on execution"
        return "startup"

    def unify(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        groups: dict[tuple[Any, ...], dict[str, Any]] = {}
        for d in items:
            m = NAME_RE.search(d["message"])
            name = (m.group(1).lower() if m and d["category"] == "undefined_name"
                    else "")
            key = (d["file"], d["line"], d["category"], name)
            g = groups.setdefault(key, {
                "file": d["file"], "line": d["line"],
                "column": d["column"], "category": d["category"],
                "when": when(d["file"], d["line"]),
                "name": name or None,
                "messages": [], "tools": [], "codes": [],
                "suggested_fix": FIX.get(d["category"], "Review and fix."),
            })
            g["tools"].append(d["tool"])
            g["codes"].append(d["code"])
            g["messages"].append(d["message"])
            g["column"] = min(g["column"], d["column"])
        out = []
        for g in groups.values():
            g["tools"] = sorted(set(g["tools"]))
            g["codes"] = sorted(set(g["codes"]))
            g["messages"] = list(dict.fromkeys(g["messages"]))
            g["evidence_count"] = len(g["messages"])
            g["confidence"] = ("high" if len(g["tools"]) >= 2 or
                               g["category"] == "syntax_error" else "medium")
            out.append(g)
        out.sort(key=lambda x: (x["when"] != "startup", x["file"], x["line"]))
        return out

    blocking = unify(blocking_src)
    risks = unify(risk_src)

    # ---- false-positive filter #2: a single-tool call error is a risk -----
    # Type checkers cannot see decorator-injected or dynamically assigned
    # callables. Require two independent tools before calling it blocking.
    demoted_keys = {(b["file"], b["line"], b["category"], b["name"])
                    for b in blocking
                    if b["category"] == "call_signature" and len(b["tools"]) < 2}
    for b in blocking:
        if (b["file"], b["line"], b["category"], b["name"]) in demoted_keys:
            b["note"] = ("only one tool reported this call; it may be a "
                         "decorator/dynamic-call false positive — verify manually")
            risks.append(b)
    blocking = [b for b in blocking
                if (b["file"], b["line"], b["category"], b["name"])
                not in demoted_keys]
    risks.sort(key=lambda x: (x["file"], x["line"]))
    dropped += len(demoted_keys)

    # compile() ground truth: one authoritative entry per broken file
    for p in compile_problems:
        key_files = [b for b in blocking
                     if b["file"] == p["file"] and b["category"] == "syntax_error"]
        msgs = [f"CPython {sys.version.split()[0]}: {p['kind']}: {p['message']} "
                f"at line {p['line']}"]
        for b in key_files:
            msgs.extend(b["messages"])
        entry = {
            "file": p["file"], "line": p["line"], "column": 1,
            "category": "syntax_error", "when": "startup", "name": None,
            "messages": list(dict.fromkeys(msgs)),
            "tools": ["cpython-compile"] + sorted({t for b in key_files
                                                   for t in b["tools"]}),
            "codes": sorted({c for b in key_files for c in b["codes"]}),
            "evidence_count": len(set(msgs)), "confidence": "high",
            "suggested_fix": FIX["syntax_error"],
            "python_312_only": p["file"] in confirmed_312,
        }
        blocking = [b for b in blocking if b["file"] != p["file"]
                    or b["category"] != "syntax_error"]
        blocking.append(entry)
    blocking.sort(key=lambda x: (x["when"] != "startup", x["file"], x["line"]))

    by_file: dict[str, dict[str, Any]] = collections.defaultdict(
        lambda: {"blocking": [], "runtime_risks": []})
    for b in blocking:
        by_file[b["file"]]["blocking"].append(b)
    for r in risks:
        by_file[r["file"]]["runtime_risks"].append(r)
    files_out = []
    for name in sorted(by_file):
        b, r = by_file[name]["blocking"], by_file[name]["runtime_risks"]
        startup = any(x["when"] == "startup" for x in b)
        files_out.append({
            "file": name,
            "status": ("cannot start" if startup else
                       "crashes on an affected code path" if b else
                       "may fail at runtime"),
            "blocking_count": len(b), "runtime_risk_count": len(r),
            "blocking": b, "runtime_risks": r[:25],
        })

    cat_counts = collections.Counter(d["category"] for d in blocking)
    ignored_by_tool = collections.Counter(d["tool"] for d in ignored)
    ignored_by_rule = collections.Counter(f"{d['tool']}:{d['code']}" for d in ignored)
    non_blocking_by_rule = collections.Counter(
        f"{d['tool']}:{d['code']}" for d in flat if d["tier"] == "non_blocking")

    return {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "repository": "i4147/bin_oct",
        "python_interpreter": sys.version.split()[0],
        "policy": {
            "question": "Which errors stop a script from running?",
            "blocking_categories": ["syntax_error", "undefined_name",
                                    "call_signature", "invalid_flow",
                                    "invalid_expression"],
            "runtime_risk_categories": ["attribute_error", "type_mismatch",
                                        "redefinition"],
            "excluded": [
                "module not found / not installed (import-error, "
                "unresolved-import, no-name-in-module, missing stubs ...)",
                "unused imports and other style/lint warnings",
            ],
            "confidence": "high = >= 2 tools agree, or CPython compile() failure; "
                          "medium = one tool only",
            "false_positive_filters": {
                "description": "two conservative filters keep the blocking list honest",
                "click_typer_wrapped_calls": "calls to click/typer decorated "
                                             "entry points are not linted",
                "single_tool_call_errors": "a call-signature error seen by only "
                                           "one tool is demoted to runtime_risk",
                "diagnostics_filtered": dropped,
            },
            "note": threshold_note,
            "execution": "no script was executed; all findings are static",
        },
        "tools": tool_meta,
        "summary": {
            "files_analyzed": len(files),
            "files_with_blocking_errors": sum(1 for f in files_out
                                              if f["blocking_count"] > 0),
            "files_that_cannot_start": sum(1 for f in files_out
                                           if f["status"] == "cannot start"),
            "files_with_only_runtime_risks": sum(1 for f in files_out
                                                 if f["blocking_count"] == 0),
            "distinct_blocking_issues": len(blocking),
            "distinct_runtime_risks": len(risks),
            "blocking_by_category": dict(cat_counts),
            "python_312_only_syntax_files": len(confirmed_312),
            "ignored_import_issues": len(ignored),
            "non_blocking_diagnostics": sum(1 for d in flat
                                            if d["tier"] == "non_blocking"),
            "filtered_likely_false_positives": dropped,
            "raw_diagnostics_all_tools": len(flat),
        },
        "python_312_syntax": [
            {"file": p["file"], "line": p["line"], "cpython_error": p["message"],
             "diagnosis": "valid Python 3.12+ syntax (PEP 695 / PEP 701), "
                          "unparseable by the Python 3.11 interpreter here",
             "options": ["run with CPython >= 3.12",
                         "rewrite `type X = ...` as a plain assignment / "
                         "TypeAlias and move multiline f-string expressions "
                         "into variables"]}
            for p in compile_problems if p["file"] in confirmed_312
        ],
        "files": files_out,
        "blocking_issues": blocking,
        "runtime_risks": risks,
        "ignored_import_issues": {
            "total": len(ignored),
            "by_tool": dict(ignored_by_tool),
            "by_rule": dict(ignored_by_rule.most_common()),
            "note": "These are excluded from the error report by request.",
        },
        "non_blocking_by_rule": dict(non_blocking_by_rule.most_common(40)),
    }


# --------------------------------------------------------------------------- #
# markdown
# --------------------------------------------------------------------------- #
def render_error_markdown(rep: dict[str, Any], out: pathlib.Path) -> None:
    s = rep["summary"]
    L = [
        "# Error report — scripts that cannot run",
        "",
        f"Generated {rep['generated_at']} · Python "
        f"{rep['python_interpreter']} · **{s['files_analyzed']} scripts** checked.",
        "",
        "Static analysis only: no script was executed. Import failures caused "
        "by modules that are not installed are **excluded** by request.",
        "",
        "## Headline numbers",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Scripts analysed | {s['files_analyzed']} |",
        f"| Scripts with blocking errors | {s['files_with_blocking_errors']} |",
        f"| Scripts that cannot start | {s['files_that_cannot_start']} |",
        f"| Distinct blocking issues | {s['distinct_blocking_issues']} |",
        f"| Runtime risks (may crash) | {s['distinct_runtime_risks']} |",
        f"| Python-3.12-only syntax files | {s['python_312_only_syntax_files']} |",
        f"| Ignored import issues | {s['ignored_import_issues']} |",
        f"| Other non-blocking diagnostics | {s['non_blocking_diagnostics']} |",
        f"| Raw diagnostics from all 4 tools | {s['raw_diagnostics_all_tools']} |",
        "",
        "## Tools (reports saved separately)",
        "",
        "| Tool | Version | Diagnostics | Blocking | Report |",
        "|---|---|---:|---:|---|",
    ]
    for name in OUT_KINDS:
        t = rep["tools"].get(name, {})
        L.append(f"| {name} | {t.get('version', '?')} | "
                 f"{t.get('total_diagnostics', 0)} | "
                 f"{t.get('blocking', 0)} | `{name}_report.json` |")
    L += ["", "Commands and flags are recorded in each JSON report and in "
          "`reports/README.md`.", "",
          "## Blocking errors by category", "",
          "| Category | Issues | What it does |", "|---|---:|---|"]
    meaning = {
        "syntax_error": "script cannot be parsed/started",
        "undefined_name": "NameError at the reported line",
        "call_signature": "TypeError from a broken call",
        "invalid_flow": "SyntaxError / illegal control flow",
        "invalid_expression": "invalid expression at runtime",
        "attribute_error": "AttributeError risk",
        "type_mismatch": "TypeError risk",
        "redefinition": "silently overrides an earlier definition",
    }
    for k, v in sorted(s["blocking_by_category"].items(), key=lambda x: -x[1]):
        L.append(f"| `{k}` | {v} | {meaning.get(k, '')} |")

    L += ["", "## Python 3.12-only syntax (blocked only on Python 3.11)", "",
          f"{s['python_312_only_syntax_files']} files use PEP 695 "
          "(`type X = ...`, `def f[T]`) or PEP 701 (multiline / backslash f-string "
          "expressions). They are valid on CPython >= 3.12 but this environment "
          "runs 3.11, so they fail at startup. `ty --python-version 3.12` reports "
          "**zero** syntax diagnostics for them.", "",
          "| File | Line | CPython 3.11 error |", "|---|---:|---|"]
    for x in rep["python_312_syntax"]:
        L.append(f"| `{x['file']}` | {x['line']} | {x['cpython_error']} |")
    L += ["", "Options: run these scripts with CPython >= 3.12, or rewrite the "
          "`type` statements as `TypeAlias` assignments and move multiline "
          "f-string expressions into local variables.", ""]

    L += ["## Scripts that cannot start", "",
          "Files with a `startup` blocking issue (parse error or a module-level "
          "undefined name).", "",
          "| File | Status | Issues | Details |", "|---|---|---:|---|"]
    startup_files = [f for f in rep["files"] if f["status"] == "cannot start"]
    for f in startup_files[:80]:
        detail = "; ".join(
            f"L{b['line']} {b['category']}" for b in f["blocking"][:4])
        L.append(f"| `{f['file']}` | {f['status']} | {f['blocking_count']} | "
                 f"{detail} |")
    if len(startup_files) > 80:
        L.append(f"\n_…and {len(startup_files) - 80} more; see `blocking_errors.json`._")

    L += ["", "## Blocking issues (full list)", "",
          "| File | Line | Category | When | Tools | Message |",
          "|---|---:|---|---|---|---|"]
    for b in rep["blocking_issues"][:250]:
        msg = b["messages"][0].replace("|", "\\|")[:130]
        L.append(f"| `{b['file']}` | {b['line']} | `{b['category']}` | "
                 f"{b['when']} | {', '.join(b['tools'])} | {msg} |")
    if len(rep["blocking_issues"]) > 250:
        L.append(f"\n_…and {len(rep['blocking_issues']) - 250} more; "
                 "see `blocking_errors.json`._")

    L += ["", "## Runtime risks (not counted as blocking)", "",
          "Type/attribute errors can crash at runtime, but are frequently false "
          "positives with dynamic code or uninstalled libraries, so they are "
          "reported separately.", "",
          f"Total distinct runtime risks: **{s['distinct_runtime_risks']}**. "
          "The full list is in `blocking_errors.json → runtime_risks`.", "",
          "## Excluded import issues", "",
          f"**{s['ignored_import_issues']}** diagnostics about missing / "
          "unresolvable modules were excluded:", ""]
    for k, v in list(rep["ignored_import_issues"]["by_rule"].items())[:12]:
        L.append(f"- `{k}`: {v}")
    L += ["", "## How to fix", "",
          "1. Run `python3 reports/fix_small_errors.py` for a dry run of the "
          "safe, mechanical fixes (unused imports, stray `f` prefixes, trailing "
          "whitespace, missing final newline, invalid escape sequences).",
          "2. Add `--apply` to actually edit files in place (use `--backup` to "
          "keep `.bak` copies). The script re-compiles every file it touches and "
          "reverts any change that breaks it.",
          "3. Fix remaining blocking issues by hand using the file/line table "
          "above. `fix_small_errors.py` deliberately does not attempt semantic "
          "rewrites such as undefined names or PEP 695/701 syntax.", ""]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=pathlib.Path, default=ROOT)
    ap.add_argument("--out-dir", type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parent)
    ap.add_argument("--tools-dir", default=None,
                    help="directory containing ruff/pylint/mypy/ty binaries")
    ap.add_argument("--skip", action="append", default=[], choices=list(OUT_KINDS),
                    help="skip a tool (can be repeated)")
    ap.add_argument("--from-raw", action="store_true",
                    help="rebuild reports from existing raw/ outputs (no tool runs)")
    args = ap.parse_args()

    root = args.root.resolve()
    out_dir = args.out_dir.resolve()
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    files = discover_files(root)
    names = [p.name for p in files]
    print(f"analysing {len(files)} top-level .py files in {root}", flush=True)

    tools = find_tools(args.tools_dir)
    missing = [t for t in OUT_KINDS if t not in tools or t in args.skip]
    if missing:
        print(f"WARNING: tools not run: {', '.join(missing)}", flush=True)

    all_diags: dict[str, list[dict[str, Any]]] = {}
    tool_meta: dict[str, Any] = {}

    threshold_note = ("ruff and ty were pinned to Python 3.11 so that "
                      "Python-3.12-only syntax is reported as an error.")

    if args.from_raw:  # ------------------------------------------------ fast path
        print("rebuilding reports from raw/ outputs ...", flush=True)
        raw_files = {"ruff": ("ruff.json", parse_ruff),
                     "pylint": ("pylint.json", parse_pylint),
                     "mypy": ("mypy.txt", parse_mypy),
                     "ty": ("ty.txt", parse_ty)}
        for name, (fname, parser) in raw_files.items():
            fp = raw_dir / fname
            if not fp.exists():
                print(f"      missing {fp}; skipping {name}", flush=True)
                continue
            ds = parser(fp.read_text(encoding="utf-8"), root)
            all_diags[name] = ds
            old = out_dir / f"{name}_report.json"
            prev = json.loads(old.read_text()) if old.exists() else {}
            tool_meta[name] = {
                "version": prev.get("version", "unknown"),
                "total_diagnostics": len(ds),
                "blocking": sum(1 for d in ds if d["tier"] == "blocking"),
                "config": (prev.get("config") or {}).get("flags", ""),
                "_cmd": [prev.get("command", name)],
                "_rc": prev.get("exit_code", 0),
                "_stderr": prev.get("stderr_tail", ""),
            }
        p312 = raw_dir / "ty_py312.txt"
        if p312.exists():
            still_broken = {rel(m.group("file"), root) for ln in
                            p312.read_text(encoding="utf-8").splitlines()
                            if (m := TY_RE.match(ln.strip()))
                            and m.group("code") == "invalid-syntax"}
            syn = {d["file"] for d in all_diags.get("ty", [])
                   if d["code"] == "invalid-syntax"}
            confirmed_312 = syn - still_broken
        compile_problems = (json.loads((raw_dir / "compile_errors.json").read_text())
                            if (raw_dir / "compile_errors.json").exists() else [])
        for p in compile_problems:
            p["requires_python_312"] = p["file"] in confirmed_312
        clean_meta = {k: {kk: vv for kk, vv in v.items()
                          if not kk.startswith("_")} for k, v in tool_meta.items()}
        rep = build_blocking_report(files, root, all_diags, compile_problems,
                                    confirmed_312, clean_meta, threshold_note)
        for tool in OUT_KINDS:
            meta = tool_meta.get(tool, {})
            ds = all_diags.get(tool, [])
            write_json(out_dir / f"{tool}_report.json",
                       per_tool_report(tool, meta.get("version", ""),
                                       meta.get("_cmd", [tool]), ds, len(files),
                                       meta.get("_rc", -1), meta.get("_stderr", ""),
                                       {"flags": meta.get("config", ""),
                                        "note": "full raw output in raw/ directory"}))
        write_json(out_dir / "blocking_errors.json", rep)
        render_error_markdown(rep, out_dir / "error_report.md")
        print(f"done: {rep['summary']['files_with_blocking_errors']} files with "
              f"blocking errors", flush=True)
        return 0

    # ------------------------------------------------------------------ ruff
    if "ruff" in tools and "ruff" not in args.skip:
        print("[1/6] ruff ...", flush=True)
        cmd = [tools["ruff"]] + TOOL_PREFIX["ruff"] + COMMAND_FLAGS["ruff"] + names
        stdout, stderr, rc = run(cmd, root)
        (raw_dir / "ruff.json").write_text(stdout, encoding="utf-8")
        tool_meta["ruff"] = {"_cmd": cmd, "_rc": rc, "_stderr": stderr}
        ds = parse_ruff(stdout, root)
        all_diags["ruff"] = ds
        tool_meta["ruff"].update({"version": version_of(tools["ruff"]),
                             "total_diagnostics": len(ds),
                             "blocking": sum(1 for d in ds if d["tier"] == "blocking"),
                             "config": "--target-version py311 "
                                       "--select E4,E7,E9,F,W,PLE,B"})
        print(f"      {len(ds)} diagnostics", flush=True)

    # ---------------------------------------------------------------- pylint
    if "pylint" in tools and "pylint" not in args.skip:
        print("[2/6] pylint (this is the slow one) ...", flush=True)
        cmd = [tools["pylint"]] + TOOL_PREFIX["pylint"] + COMMAND_FLAGS["pylint"] + names
        stdout, stderr, rc = run(cmd, root, timeout=1500)
        (raw_dir / "pylint.json").write_text(stdout, encoding="utf-8")
        tool_meta["pylint"] = {"_cmd": cmd, "_rc": rc, "_stderr": stderr}
        ds = parse_pylint(stdout, root)
        all_diags["pylint"] = ds
        tool_meta["pylint"].update({"version": version_of(tools["pylint"]).split("\n")[0],
                               "total_diagnostics": len(ds),
                               "blocking": sum(1 for d in ds if d["tier"] == "blocking"),
                               "config": "error/fatal/warning checks only; "
                                         "E0401 import-error and E0611 "
                                         "no-name-in-module disabled"})
        print(f"      {len(ds)} diagnostics", flush=True)

    # ------------------------------------------------------------------ mypy
    if "mypy" in tools and "mypy" not in args.skip:
        print("[3/6] mypy ...", flush=True)
        cmd = [tools["mypy"]] + TOOL_PREFIX["mypy"] + COMMAND_FLAGS["mypy"] + names
        stdout, stderr, rc = run(cmd, root)
        (raw_dir / "mypy.txt").write_text(stdout, encoding="utf-8")
        tool_meta["mypy"] = {"_cmd": cmd, "_rc": rc, "_stderr": stderr}
        ds = parse_mypy(stdout, root)
        all_diags["mypy"] = ds
        tool_meta["mypy"].update({"version": version_of(tools["mypy"]),
                             "total_diagnostics": len(ds),
                             "blocking": sum(1 for d in ds if d["tier"] == "blocking"),
                             "config": "--check-untyped-defs --python-version 3.11 "
                                       "--ignore-missing-imports --follow-imports=skip "
                                       "--scripts-are-modules"})
        print(f"      {len(ds)} diagnostics", flush=True)

    # -------------------------------------------------------------------- ty

    if "ty" in tools and "ty" not in args.skip:
        print("[4/6] ty ...", flush=True)
        cmd = [tools["ty"]] + TOOL_PREFIX["ty"] + COMMAND_FLAGS["ty"] + names
        stdout, stderr, rc = run(cmd, root)
        (raw_dir / "ty.txt").write_text(stdout, encoding="utf-8")
        tool_meta["ty"] = {"_cmd": cmd, "_rc": rc, "_stderr": stderr}
        ds = parse_ty(stdout, root)
        all_diags["ty"] = ds
        tool_meta["ty"].update({"version": version_of(tools["ty"]),
                           "total_diagnostics": len(ds),
                           "blocking": sum(1 for d in ds if d["tier"] == "blocking"),
                           "config": "--python-version 3.11 --output-format concise"})
        print(f"      {len(ds)} diagnostics", flush=True)

        syn_files = sorted({d["file"] for d in ds if d["code"] == "invalid-syntax"})
        if syn_files:
            cmd12 = [tools["ty"]] + TOOL_PREFIX["ty"] + [
                f for f in COMMAND_FLAGS["ty"]
                if f not in ("3.11", "--python-version")] + [
                "--python-version", "3.12"] + syn_files
            out12, _, _ = run(cmd12, root)
            (raw_dir / "ty_py312.txt").write_text(out12, encoding="utf-8")
            still_broken = {m.group("file") for ln in out12.splitlines()
                            if (m := TY_RE.match(ln.strip()))
                            and m.group("code") == "invalid-syntax"}
            confirmed_312 = set(rel(f, root) for f in syn_files) - {
                rel(f, root) for f in still_broken}
            print(f"      {len(confirmed_312)} files parse fine on Python 3.12",
                  flush=True)

    print("[5/6] CPython compile check ...", flush=True)
    compile_problems = compile_check(files, root)
    for p in compile_problems:
        p["requires_python_312"] = p["file"] in confirmed_312
    write_json(raw_dir / "compile_errors.json", compile_problems)
    print(f"      {len(compile_problems)} files fail to compile", flush=True)

    # ------------------------------------------------------------- reporting
    print("[6/6] writing reports ...", flush=True)
    for tool in OUT_KINDS:
        ds = all_diags.get(tool, [])
        meta = tool_meta.get(tool, {})
        flags = meta.get("config", "(tool not run)")
        write_json(out_dir / f"{tool}_report.json",
                   per_tool_report(tool, meta.get("version", ""),
                                   meta.get("_cmd", [tool, "check", flags]), ds,
                                   len(files), meta.get("_rc", -1),
                                   meta.get("_stderr", ""),
                                   {"flags": flags,
                                    "note": "full raw output in raw/ directory"}))

    clean_meta = {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
                  for k, v in tool_meta.items()}
    rep = build_blocking_report(files, root, all_diags, compile_problems,
                                confirmed_312, clean_meta, threshold_note)
    write_json(out_dir / "blocking_errors.json", rep)
    render_error_markdown(rep, out_dir / "error_report.md")
    s = rep["summary"]
    print(f"done: {s['files_with_blocking_errors']} files with blocking errors, "
          f"{s['distinct_blocking_issues']} distinct issues, "
          f"{s['ignored_import_issues']} import issues ignored", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
