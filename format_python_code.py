#!/data/data/com.termux/files/usr/bin/python3.12
"""
Merged Python source code formatting/rewriting tool.

Third-party dependencies (all optional, per-subcommand):
  astor     - astor subcommand
  black     - format --style black (default)
  isort     - format --style isort
  autoflake - format --style autoflake
  autopep8  - format --style autopep
  yapf      - format --style yapf
  ruff      - external binary for ruff subcommand

Usage examples:
  python merged.py fixcode FILE.py
  python merged.py fixindent FILE.py --indent 4
  python merged.py tokenformat FILE.py
  python merged.py reflow FILE.py --width 35
  python merged.py astor FILE.py --backup
  python merged.py ruff ./mydir
  python merged.py sort FILE.py
  python merged.py format --style black

Mapping:
  fixcode.py        -> python merged.py fixcode FILE.py
  fixindent.py      -> python merged.py fixindent FILE.py
  format_py_code.py -> python merged.py tokenformat FILE.py
  p45.py            -> python merged.py reflow FILE.py
  rrw.py            -> python merged.py astor FILE.py
  rufbin.py         -> python merged.py ruff [DIR]
  sort_pyfile.py    -> python merged.py sort FILE.py
  yap.py            -> python merged.py format --style black
"""

from __future__ import annotations

import argparse
import ast
import io
import re
import subprocess
import sys
import time
import tokenize
import unicodedata
from functools import partial
from pathlib import Path
from textwrap import fill as _fill
from typing import Any, Dict, List, Optional, Tuple

_ANSI = {
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "magenta": "\x1b[35m",
    "cyan": "\x1b[36m",
    "white": "\x1b[37m",
    "grey": "\x1b[90m",
}
_DOC_TOKENS = ('"""', "'''")
_FORMAT_STYLES = ("black", "isort", "autoflake", "autopep", "yapf")


def _cprint(text: str, color: Optional[str] = None, end: str = "\n") -> None:
    code = _ANSI.get(color, "")
    reset = "\x1b[0m" if code else ""
    print(f"{code}{text}{reset}", end=end)


def _format_time(seconds: float) -> str:
    return f"{seconds:.2f}s"


def _fsz(size: float) -> str:
    size = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.2f}{unit}"
        size /= 1024
    return f"{size:.2f}TB"


def _is_binary(path: Path) -> bool:
    try:
        return b"\x00" in path.read_bytes()[:1024]
    except Exception:
        return True


def _get_pyfiles(root: Path) -> list[Path]:
    return [p for p in Path(root).rglob("*.py") if p.is_file()]


def _get_files(root: Path) -> list[Path]:
    return [p for p in Path(root).iterdir() if p.is_file()]


def _mpf_async(func, items: list[Any]) -> list[Any]:
    import multiprocessing

    if not items:
        return []
    with multiprocessing.Pool() as pool:
        return pool.map(func, items)


_FIXCODE_HEAD = re.compile(r"^\s*(def|class)\s+")
_FIXCODE_MAIN = re.compile(r"^\s*if\s+__name__\s*==\s*['\"]__main__['\"]\s*:")
_FIXCODE_CTRL = re.compile(
    r"""
    ^\s*
    (
        if\s+|
        elif\s+|
        else\s*:|
        for\s+|
        while\s+|
        try\s*:|
        except\s+|
        finally\s*:|
        with\s+
    )
    """,
    re.VERBOSE,
)


def _fixcode_can(s: str) -> bool:
    if not s:
        return True
    return (
        s.startswith(
            (
                "def ",
                "class ",
                "if ",
                "elif ",
                "else:",
                "for ",
                "while ",
                "try:",
                "except ",
                "finally:",
                "with ",
                "return",
                "import ",
                "from ",
                "@",
                "#",
            )
        )
        or "=" in s
        or "(" in s
        or s.endswith(":")
    )


def _fixcode_apply(source: str) -> str:
    out: list[str] = []
    indent = 0
    seen_def = False
    for raw in source.splitlines():
        line = raw.rstrip()
        if not line.strip():
            out.append("")
            continue
        if _FIXCODE_HEAD.match(line):
            seen_def = True
        if not seen_def and not _fixcode_can(line):
            out.append("# " + line.strip())
            continue
        stripped = line.strip()
        if _FIXCODE_HEAD.match(stripped):
            indent = 0
            out.append(stripped)
            indent = 1
            continue
        if _FIXCODE_MAIN.match(stripped):
            indent = 1
            out.append('if __name__=="__main__":')
            continue
        if stripped.startswith(("return", "pass", "break", "continue", "raise")):
            out.append("    " * indent + stripped)
            indent = max(indent - 1, 0)
            continue
        if _FIXCODE_CTRL.match(stripped):
            out.append("    " * indent + stripped)
            indent += 1
            continue
        out.append("    " * indent + stripped)
    return "\n".join(out)


def _validate_python(source: str) -> tuple[bool, Optional[str]]:
    try:
        ast.parse(source)
        return True, None
    except SyntaxError as exc:
        return False, f"{exc.msg} (line {exc.lineno}, col {exc.offset})"


def cmd_fixcode(args: argparse.Namespace) -> int:
    src = Path(args.file)
    text = src.read_text(encoding="utf-8", errors="ignore")
    fixed = _fixcode_apply(text)
    ok, err = _validate_python(fixed)
    src.write_text(fixed, encoding="utf-8")
    if ok:
        print(f"✔ AST valid → {src}")
    else:
        print("✘ AST validation failed")
        print(err)
        print("Wrote for inspection")
    return 0


def _fixindent_apply(path: Path, output: Optional[Path], indent_size: int) -> bool:
    if not path.exists():
        print(f"خطا:فایل ورودی یافت نشد:{path}")
        return False
    keywords = [
        "def",
        "class",
        "if",
        "for",
        "while",
        "with",
        "try",
        "except",
        "finally",
        "elif",
        "else",
    ]
    terminators = ["return", "break", "continue", "pass", "raise"]
    out: list[str] = []
    level = 0
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s:
            out.append("\n")
            continue
        if any(s.startswith(k) for k in terminators) and level > 0 and i > 0 and not lines[i - 1].strip().endswith(":"):
            level = max(0, level - 1)
        out.append(" " * (level * indent_size) + s + "\n")
        if s.endswith(":"):
            head = s.split(" ")[0]
            if head in keywords or (head == "lambda" and ":" in s):
                level += 1
    dest = output or path
    try:
        dest.write_text("".join(out), encoding="utf-8")
        print(f"فایل با موفقیت اصلاح شد:{dest}")
        return True
    except OSError as exc:
        print(f"خطا در نوشتن فایل خروجی:{exc}")
        return False


def cmd_fixindent(args: argparse.Namespace) -> int:
    src = Path(args.file)
    out = Path(args.output) if args.output else src.with_stem(src.stem + "_fixed")
    if not _fixindent_apply(src, out, args.indent):
        print("There was an error modifying the file.")
        return 1
    return 0


def _tokenformat_apply(path: Path) -> None:
    src = path.read_text(encoding="utf-8")
    if not src.endswith("\n"):
        src += "\n"
    tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
    out: list[str] = []
    level = 0
    at_line_start = True

    def emit(s: str) -> None:
        nonlocal at_line_start
        if at_line_start:
            out.append("    " * level)
            at_line_start = False
        out.append(s)

    def newline() -> None:
        nonlocal at_line_start
        while out and out[-1].endswith(" "):
            out.pop()
        if not out or not out[-1].endswith("\n"):
            out.append("\n")
        at_line_start = True

    prev: Optional[int] = None
    for tok in tokens:
        ttype = tok.type
        tstr = tok.string
        if ttype in (tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NL):
            continue
        if ttype == tokenize.INDENT:
            level += 1
            continue
        if ttype == tokenize.DEDENT:
            level = max(0, level - 1)
            continue
        if ttype == tokenize.NEWLINE:
            newline()
            prev = ttype
            continue
        if ttype == tokenize.COMMENT:
            if not at_line_start:
                out.append(" ")
            emit(tstr)
            newline()
            prev = ttype
            continue
        if tstr == ":":
            emit(":")
            newline()
            prev = ttype
            continue
        if (
            not at_line_start
            and prev in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING)
            and ttype in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING)
        ):
            out.append(" ")
        if tstr in {"=", "+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">="}:
            if out and not out[-1].endswith((" ", "\n")):
                out.append(" ")
            emit(tstr)
            out.append(" ")
        else:
            emit(tstr)
        prev = ttype
    result = "".join(out).rstrip() + "\n"
    path.write_text(result, encoding="utf-8")


def cmd_tokenformat(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1
    try:
        _tokenformat_apply(path)
    except (SyntaxError, tokenize.TokenError) as exc:
        print(f"Error: input is not valid tokenizable Python: {exc}", file=sys.stderr)
        return 1
    return 0


def _reflow_comment(text: str, indent: str, width: int) -> str:
    return _fill(
        text,
        width=width,
        initial_indent=indent + "# ",
        subsequent_indent=indent + "# ",
        break_long_words=False,
        break_on_hyphens=False,
    )


def _reflow_docstring(body: str, token: str, width: int) -> str:
    filled = _fill(
        body,
        width=width,
        initial_indent=token,
        subsequent_indent=token + " " * (len(token) - 1),
        break_long_words=False,
        break_on_hyphens=False,
    )
    if not filled.endswith(token):
        filled += token
    return filled


def _reflow_apply(path: Path, width: int) -> None:
    if not path.exists():
        print(f"Error: File not found at {path}", file=sys.stderr)
        return
    backup = path.with_name(path.name + ".bak")
    try:
        text = path.read_text(encoding="utf-8")
        backup.write_text(text, encoding="utf-8")
    except OSError as exc:
        print(f"Error creating backup file {backup.name}:{exc}", file=sys.stderr)
        return

    out: list[str] = []
    in_doc = False
    buf: list[str] = []
    token = ""
    for raw in text.splitlines():
        stripped = raw.strip()
        if "# type:" in stripped:
            continue
        if stripped.startswith("#!"):
            continue
        if stripped.startswith(_DOC_TOKENS):
            if not in_doc:
                in_doc = True
                token = stripped[:3]
                buf = [raw]
            else:
                buf.append(raw)
                if stripped.endswith(token) and len(stripped) > len(token):
                    joined = "\n".join(buf)
                    out.append(_reflow_docstring(joined[len(token) : -len(token)], token, width))
                    in_doc = False
                    buf = []
                    token = ""
            continue
        if in_doc:
            buf.append(raw)
            if stripped.endswith(token) and len(stripped) > len(token):
                joined = "\n".join(buf)
                out.append(_reflow_docstring(joined[len(token) : -len(token)], token, width))
                in_doc = False
                buf = []
                token = ""
            continue
        idx = raw.find("#")
        if idx != -1:
            before = raw[:idx]
            comment = raw[idx:].strip()
            if comment:
                indent = " " * (len(raw) - len(raw.lstrip()))
                body = comment[1:].strip()
                filled = _reflow_comment(body, indent, width)
                out.append(before + filled[len(indent + "# ") :])
            else:
                out.append(raw)
        else:
            out.append(raw)
    if in_doc:
        out.extend(buf)
    result = "\n".join(out)
    try:
        ast.parse(result)
        path.write_text(result, encoding="utf-8")
        print(f"Successfully formatted {path}. Backup created at {backup}")
    except SyntaxError as exc:
        tmp = Path("temporary.py")
        tmp.write_text(result, encoding="utf-8")
        print(
            f"Error: Formatted code is not parsable by AST. Aborting write operation for {path}.",
            file=sys.stderr,
        )
        print(f"AST Syntax Error: {exc}", file=sys.stderr)
        backup.replace(path)
        print(f"Restored {path} from backup.")


def cmd_reflow(args: argparse.Namespace) -> int:
    _reflow_apply(Path(args.file), args.width)
    return 0


def _astor_apply(path: Path, backup: bool) -> None:
    if _is_binary(path):
        return
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if backup:
            bak = path.with_suffix(path.suffix + ".bak")
            bak.write_text(text, encoding="utf-8")
        if path.suffix == ".py":
            try:
                tree = ast.parse(text)
                import astor

                new_src = astor.to_source(tree)
                path.write_text(new_src, encoding="utf-8")
                print(f"\x1b[0m[ \x1b[6;96m✓\x1b[0m ] {path.name} ")
                return
            except Exception:
                print(f"\x1b[0m[ \x1b[6;96m✘\x1b[0m ] {path.name} ")
                return
        normalized = unicodedata.normalize("NFD", text)
        path.write_text(normalized, encoding="utf-8")
    except Exception:
        return


def cmd_astor(args: argparse.Namespace) -> int:
    targets = [Path(f) for f in args.files] if args.files else _get_files(Path.cwd())
    for path in targets:
        _astor_apply(path, args.backup)
    return 0


def _looks_like_python(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            head = fh.read(1024)
        if head.startswith("#!") and "python" in head.lower():
            return True
        markers = [
            "def ",
            "class ",
            "import ",
            "from ",
            "async def",
            "if __name__==",
            "print(",
            "raise ",
            "try:",
            "except ",
            "__init__",
        ]
        low = head.lower()
        for marker in markers:
            if marker in low:
                return True
        return path.suffix.lower() == ".py"
    except Exception:
        return False


def _run_ruff(path: Path) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["ruff", "format", str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if not result.returncode:
            return True, ""
        return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Timeout (30s)"
    except FileNotFoundError:
        return False, "ruff not installed or not in PATH"
    except Exception as exc:
        return False, str(exc)


def cmd_ruff(args: argparse.Namespace) -> int:
    root = Path(args.directory)
    if not root.exists():
        print(f"Error: directory not found: {root}", file=sys.stderr)
        return 1
    candidates = [p for p in root.iterdir() if p.is_file() and _looks_like_python(p)]
    if not candidates:
        return 0
    ok = fail = 0
    errors: list[str] = []
    for path in candidates:
        good, err = _run_ruff(path)
        if good:
            ok += 1
        else:
            fail += 1
            errors.append(f"{path.name}: {err}")
    for line in errors:
        print(line, file=sys.stderr)
    return 0


def _is_main_guard(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.Eq)
        and len(node.test.comparators) == 1
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value == "__main__"
    )


def _sort_apply(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"Error reading {path}: {exc}")
        return
    lines = text.split("\n")
    shebang = ""
    start = 0
    if lines and lines[0].startswith("#!"):
        shebang = lines[0]
        start = 1
    body = "\n".join(lines[start:])
    try:
        tree = ast.parse(body)
    except SyntaxError as exc:
        print(f"Error parsing Python code in {path}: {exc}")
        return
    docstring = ""
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        docstring = ast.get_source_segment(body, tree.body[0]) or ""
        tree.body.pop(0)
    main_node: Optional[ast.AST] = None
    rest: list[ast.AST] = []
    for node in tree.body:
        if _is_main_guard(node):
            main_node = node
            continue
        rest.append(node)
    imports: list[ast.AST] = []
    consts: list[ast.AST] = []
    classes: list[ast.AST] = []
    funcs: list[ast.AST] = []
    others: list[ast.AST] = []
    for node in rest:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(node)
        elif isinstance(node, ast.Assign):
            if all(isinstance(t, ast.Name) and t.id.isupper() for t in node.targets):
                consts.append(node)
            else:
                others.append(node)
        elif isinstance(node, ast.ClassDef):
            classes.append(node)
        elif isinstance(node, ast.FunctionDef):
            funcs.append(node)
        else:
            others.append(node)
    consts.sort(key=lambda n: n.targets[0].id if n.targets else "")
    classes.sort(key=lambda n: n.name)
    funcs.sort(key=lambda n: n.name)
    chunks: list[str] = []
    if shebang:
        chunks.append(shebang)
    if docstring:
        chunks.append(docstring)
    for group in (imports, others, consts, classes, funcs):
        for node in group:
            seg = ast.get_source_segment(body, node)
            if seg:
                chunks.append(seg)
            else:
                print(f"Warning: Could not preserve source for {node}")
    if main_node is not None:
        seg = ast.get_source_segment(body, main_node)
        if seg:
            chunks.append(seg)
    result = "\n".join(chunks)
    dest = path.with_name(path.stem + "_sorted" + path.suffix)
    try:
        dest.write_text(result, encoding="utf-8")
        print(f"Successfully sorted and saved: {dest}")
    except Exception as exc:
        print(f"Error writing to {dest}: {exc}")


def cmd_sort(args: argparse.Namespace) -> int:
    _sort_apply(Path(args.file))
    return 0


def _format_with_style(text: str, style: str) -> str:
    if style == "autoflake":
        from autoflake import fix_code as fix_with_autoflake

        return fix_with_autoflake(text, remove_all_unused_imports=True)
    if style == "isort":
        from isort import code as fix_with_isort

        return fix_with_isort(text)
    if style == "black":
        from black import Mode, TargetVersion, format_str

        return format_str(
            text,
            mode=Mode(
                target_versions={TargetVersion.PY310, TargetVersion.PY313},
                line_length=120,
            ),
        )
    if style == "autopep":
        from autopep8 import fix_code as fix_with_autopep

        return fix_with_autopep(text, options={"aggressive": 2})
    if style == "yapf":
        from yapf.yapflib.yapf_api import FormatCode

        result, _ = FormatCode(text)
        return result
    from black import Mode, TargetVersion, format_str

    return format_str(
        text,
        mode=Mode(
            target_versions={TargetVersion.PY310, TargetVersion.PY313},
            line_length=120,
        ),
    )


def _format_one(path_str: str, style: str) -> bool:
    start = time.time()
    path = Path(path_str)
    try:
        size = path.stat().st_size
        text = path.read_text(encoding="utf-8")
        new_text = _format_with_style(text, style)
        new_size = len(new_text)
        diff = abs(size - new_size)
        elapsed = time.time() - start
        if diff:
            path.write_text(new_text, encoding="utf-8")
            pct = diff / size * 40 if size else 0
            _cprint(f"({_format_time(elapsed)})|{_fsz(diff)}|{pct:.1f}%", "cyan")
            return True
        print(f"{path.name} ", end=" ")
        _cprint(f"({_format_time(elapsed)})|(no change)", "grey")
        return True
    except Exception as exc:
        _cprint("[ERROR]", "red", end=" ")
        print(f"{path.name}: {exc}")
        return False


def cmd_format(args: argparse.Namespace) -> int:
    files = [str(p) for p in _get_pyfiles(Path.cwd())]
    worker = partial(_format_one, style=args.style)
    _mpf_async(worker, files)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Merged Python source code formatter/rewriter",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("fixcode", help="Regex-heuristic auto-indenter (writes in place)")
    p.add_argument("file")
    p.set_defaults(func=cmd_fixcode)

    p = sub.add_parser("fixindent", help="Simple colon-based re-indenter")
    p.add_argument("file")
    p.add_argument("--output", default=None)
    p.add_argument("--indent", type=int, default=4)
    p.set_defaults(func=cmd_fixindent)

    p = sub.add_parser("tokenformat", help="Token-based reformatter")
    p.add_argument("file")
    p.set_defaults(func=cmd_tokenformat)

    p = sub.add_parser("reflow", help="Reflow comments and docstrings to a width")
    p.add_argument("file")
    p.add_argument("--width", type=int, default=35)
    p.set_defaults(func=cmd_reflow)

    p = sub.add_parser("astor", help="Rewrite via astor (or NFKC-normalize non-py)")
    p.add_argument("files", nargs="*")
    p.add_argument("--backup", action="store_true")
    p.set_defaults(func=cmd_astor)

    p = sub.add_parser("ruff", help="Run ruff format on candidate files")
    p.add_argument("directory", nargs="?", default=".")
    p.set_defaults(func=cmd_ruff)

    p = sub.add_parser("sort", help="Sort top-level AST nodes; write *_sorted file")
    p.add_argument("file")
    p.set_defaults(func=cmd_sort)

    p = sub.add_parser("format", help="API-based formatter (black/isort/autoflake/autopep/yapf)")
    p.add_argument("--style", choices=_FORMAT_STYLES, default="black")
    p.set_defaults(func=cmd_format)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
