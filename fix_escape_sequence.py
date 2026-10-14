#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line tool for detecting and automatically repairing invalid escape sequences in Python source files. The tool should accept one or more file or directory paths as input, recursively scan directories for Python files while skipping common non-source folders (such as version control, virtual environment, cache, and build directories), and analyze the string literals in each file using Python's tokenizer so that only string and f-string contents are examined, never comments or code outside of literals.
For every string literal that contains an unrecognized backslash escape (for example, a regex pattern like "\\d" written without a raw prefix), the script should convert the invalid sequence into a properly escaped form that preserves the original intended text, while leaving valid escape sequences, raw strings, byte strings where appropriate, and already-correct content untouched. The repair must handle both regular and f-string literals, including tokenizer differences across Python versions, and must avoid corrupting multi-line strings, line continuations, or Unicode escapes.
The tool should support a dry-run or check mode that reports each problematic location (file, line, column, and the offending sequence) without modifying anything, and an apply mode that rewrites affected files in place. Its output should be a clear, human-readable summary listing every fix or issue found, along with a final count of files scanned, files changed, and total fixes made. The script should exit with a nonzero status code when issues are found in check mode, and zero otherwise. Processing should be robust: files that cannot be decoded, parsed, or read should be reported as warnings and skipped without stopping the overall run. Where practical, the script should use parallel processing to speed up scanning of large codebases, suppress or handle Python syntax warnings emitted during analysis, and never attempt to modify its own source file.
---"""

from __future__ import annotations
import argparse
import io
import multiprocessing as mp
from pathlib import Path
import sys
import tokenize
import warnings

VALID_ESCAPES: frozenset[str] = frozenset("\\'\"abfnrtv\n\r01234567xNuU")
HAS_FSTRING_TOKENS: bool = hasattr(tokenize, "FSTRING_START")
SKIP_DIRS: frozenset[str] = frozenset({
    "__pycache__",
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    "venv",
    "env",
    "virtualenv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".cache",
    "build",
    "dist",
    ".eggs",
    ".idea",
    ".vscode",
})
SELF_PATH: Path = Path(__file__).resolve()
Fix = tuple[tuple[int, int], tuple[int, int], str]
Result = tuple[str, str, int, int]


def _fix_body(body: str) -> str | None:
    out: list[str] = []
    changed = False
    i, n = 0, len(body)
    while i < n:
        c = body[i]
        if c == "\\" and i + 1 < n:
            nxt = body[i + 1]
            if nxt in VALID_ESCAPES:
                out.append(c)
                out.append(nxt)
            else:
                out.append("\\\\")
                out.append(nxt)
                changed = True
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out) if changed else None


def _fix_string_literal(tok_src: str) -> str | None:
    i = 0
    while i < len(tok_src) and tok_src[i].isalpha():
        i += 1
    prefix, rest = tok_src[:i], tok_src[i:]
    if not rest or rest[0] not in ('"', "'"):
        return None
    q = rest[0]
    quote = q * 3 if rest.startswith(q * 3) else q
    if len(rest) < 2 * len(quote) or not rest.endswith(quote):
        return None
    if "r" in prefix.lower():
        return None
    body = rest[len(quote) : -len(quote)]
    new_body = _fix_body(body)
    if new_body is None:
        return None
    return prefix + quote + new_body + quote


def fix_source(src: str) -> str:
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return src
    fixes: list[Fix] = []
    fstring_raw: list[bool] = []
    for tok in tokens:
        t = tok.type
        if t == tokenize.STRING:
            fixed = _fix_string_literal(tok.string)
            if fixed is not None and fixed != tok.string:
                fixes.append((tok.start, tok.end, fixed))
        elif HAS_FSTRING_TOKENS and t == tokenize.FSTRING_START:
            fstring_raw.append("r" in tok.string[:-1].lower())
        elif HAS_FSTRING_TOKENS and t == tokenize.FSTRING_END:
            if fstring_raw:
                fstring_raw.pop()
        elif HAS_FSTRING_TOKENS and t == tokenize.FSTRING_MIDDLE:
            if not (fstring_raw and fstring_raw[-1]):
                nb = _fix_body(tok.string)
                if nb is not None and nb != tok.string:
                    fixes.append((tok.start, tok.end, nb))
    if not fixes:
        return src
    lines = src.splitlines(keepends=True)
    for (sr, sc), (er, ec), new in sorted(fixes, key=lambda f: f[0], reverse=True):
        if sr == er:
            line = lines[sr - 1]
            lines[sr - 1] = line[:sc] + new + line[ec:]
        else:
            first = lines[sr - 1][:sc]
            last = lines[er - 1][ec:]
            lines[sr - 1 : er] = [first + new + last]
    return "".join(lines)


def syntax_warnings(src: str, filename: str) -> list[str] | None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            compile(src, filename, "exec")
        except SyntaxError:
            return None
        return [str(w.message) for w in caught if issubclass(w.category, SyntaxWarning)]


def _is_self(p: Path) -> bool:
    try:
        return p.resolve() == SELF_PATH
    except OSError:
        return False


def iter_py_files(root: Path) -> list[Path]:
    root = root.resolve()
    out: list[Path] = []
    for p in sorted(root.rglob("*.py")):
        if p.is_symlink():
            continue
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if _is_self(p):
            continue
        out.append(p)
    return out


def process_file(path_str: str, dry_run: bool, quiet: bool) -> Result:
    p = Path(path_str)
    if p.is_symlink() or _is_self(p):
        return (path_str, "skipped", 0, 0)
    try:
        src = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return (path_str, "skipped", 0, 0)
    warns = syntax_warnings(src, path_str)
    if warns is None:
        return (path_str, "error", 0, 0)
    if not warns:
        return (path_str, "clean", 0, 0)
    fixed = fix_source(src)
    if fixed == src:
        return (path_str, "unfixable", len(warns), len(warns))
    remaining = syntax_warnings(fixed, path_str)
    if remaining is None:
        return (path_str, "error", len(warns), len(warns))
    if not dry_run:
        try:
            p.write_text(fixed, encoding="utf-8")
        except OSError:
            return (path_str, "error", len(warns), len(warns))
    status = "fixed" if not remaining else "partial"
    return (path_str, status, len(warns), len(remaining))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("-n", "--dry-run", action="store_true")
    ap.add_argument("-q", "--quiet", action="store_true")
    ap.add_argument("-j", "--jobs", type=int, default=8)
    args = ap.parse_args(argv)
    targets: list[str] = []
    for p in args.paths:
        if p.is_dir():
            targets.extend(str(x) for x in iter_py_files(p))
        elif p.is_file():
            if p.is_symlink() or _is_self(p):
                continue
            targets.append(str(p))
        else:
            print(f"error: not found: {p}", file=sys.stderr)
    if not targets:
        print("no files to process")
        return 0
    tasks: list[tuple[str, bool, bool]] = [(t, args.dry_run, args.quiet) for t in targets]
    with mp.Pool(args.jobs) as pool:
        results: list[Result] = pool.starmap(process_file, tasks)
    counts: dict[str, int] = {}
    for path, status, before, after in results:
        counts[status] = counts.get(status, 0) + 1
        if args.quiet:
            continue
        if status == "fixed":
            print(f"fixed: {path}")
        elif status == "partial":
            print(f"partial: {path}  ({after} warning(s) remain)", file=sys.stderr)
        elif status == "unfixable":
            print(f"unfixable: {path}  ({before} warning(s))")
        elif status == "error":
            print(f"error: {path}", file=sys.stderr)
    print("summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    bad = counts.get("error", 0) + counts.get("partial", 0) + counts.get("unfixable", 0)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
