#!/data/data/com.termux/files/usr/bin/python3.12
"""Merge a small multi-file Python package into a single annotated module.
Usage: script.py # scan current directory recursively script.py -f merged_input.py # read from a merged-file with # "# filename: relpath" sentinels script.py -o mypkg.py # choose output filename"""

from __future__ import annotations
import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Iterable

WORKERS: int = 6
FILENAME_SENTINEL = re.compile(r"^#\s*File:\s*(.+?)\s*$")
SIX_MOVES_MAP = {
    "six.moves.copyreg": "copyreg",
    "six.moves.urllib": "urllib",
    "six.moves.http_client": "http.client",
    "six.moves.cPickle": "pickle",
    "six.moves.input": "input",
    "six.moves.zip": "zip",
    "six.moves.map": "map",
    "six.moves.range": "range",
}
SIMPLE_TEXT_REWRITES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bfrom __future__ import [^\n]+\n"), ""),
    (re.compile(r"\bunicode\b(?!\s*=)"), "str"),
    (re.compile(r"\bbasestring\b"), "(str, bytes)"),
    (re.compile(r"\bstring_types\b"), "str"),
    (re.compile(r"\bbinary_type\b"), "bytes"),
    (re.compile(r"\bxrange\b"), "range"),
    (re.compile(r"\.iteritems\(\)"), ".items()"),
    (re.compile(r"\.iterkeys\(\)"), ".keys()"),
    (re.compile(r"\.itervalues\(\)"), ".values()"),
    (re.compile(r"\bsuper\(\s*\w+\s*,\s*self\s*\)"), "super()"),
    (re.compile(r"\bdef __unicode__\b"), "def __str__"),
]
OS_PATH_REWRITES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bos\.path\.exists\(([^()]*)\)"), r"Path(\1).exists()"),
    (re.compile(r"\bos\.path\.isdir\(([^()]*)\)"), r"Path(\1).is_dir()"),
    (re.compile(r"\bos\.path\.isfile\(([^()]*)\)"), r"Path(\1).is_file()"),
    (
        re.compile(r"\bos\.makedirs\(([^()]*)\)"),
        r"Path(\1).mkdir(parents=True, exist_ok=True)",
    ),
    (re.compile(r"\bos\.remove\(([^()]*)\)"), r"Path(\1).unlink()"),
    (re.compile(r"\bos\.listdir\(([^()]*)\)"), r"list(Path(\1).iterdir())"),
]
AMBIGUOUS_PATH_MARKERS = [
    re.compile(r"\bos\.path\.join\("),
    re.compile(r"\bos\.path\.split\("),
]


def find_source_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def parse_merged_file(merged_path: Path) -> dict[str, str]:
    files: dict[str, list[str]] = {}
    current: str | None = None
    for line in merged_path.read_text(encoding="utf-8").splitlines():
        m = FILENAME_SENTINEL.match(line)
        if m:
            current = m.group(1)
            files[current] = []
            continue
        if current is not None:
            files[current].append(line)
    return {name: "\n".join(lines) for name, lines in files.items()}


def load_sources(args: argparse.Namespace) -> dict[str, str]:
    if args.file:
        merged_path = Path(args.file).expanduser().resolve()
        if not merged_path.is_file():
            sys.exit(f"error: -f target not found: {merged_path}")
        sources = parse_merged_file(merged_path)
        if not sources:
            sys.exit("error: no '# filename: ...' sentinels found in -f input")
        return sources
    root = Path.cwd()
    py_files = find_source_files(root)
    if not py_files:
        sys.exit(f"error: no .py files found under {root}")
    return {str(p.relative_to(root)): p.read_text(encoding="utf-8") for p in py_files}


def strip_six_and_py2(text: str) -> str:
    for pattern, repl in SIMPLE_TEXT_REWRITES:
        text = pattern.sub(repl, text)
    for six_path, native in SIX_MOVES_MAP.items():
        text = text.replace(six_path, native)
    text = re.sub(
        r"^\s*copyreg\.pickle\(types\.MethodType,.*\n(?:.*\n)*?"
        r"^\s*def _unpickle_method\b.*(?:\n(?:    .*)?)*\n?",
        "",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(r"^\s*def _pickle_method\b.*(?:\n(?:    .*)?)*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*@implements_to_string\s*\n", "", text, flags=re.MULTILINE)
    return text


def flag_ambiguous_paths(text: str) -> str:
    lines = text.splitlines()
    out = []
    for line in lines:
        if any(p.search(line) for p in AMBIGUOUS_PATH_MARKERS) and "TODO(manual-review)" not in line:
            out.append(
                line
                + "  # TODO(manual-review): confirm this is a filesystem path, not a URL, before converting to pathlib"
            )
        else:
            out.append(line)
    return "\n".join(out)


def rewrite_os_path(text: str) -> str:
    for pattern, repl in OS_PATH_REWRITES:
        text = pattern.sub(repl, text)
    return flag_ambiguous_paths(text)


def rewrite_parallelism(text: str) -> str:
    text = re.sub(
        r"from concurrent\.futures import[^\n]*\n",
        "import multiprocessing as mp\n",
        text,
    )
    text = re.sub(
        r"with\s+ProcessPoolExecutor\(\s*(?:max_workers\s*=\s*[^)]*)?\)\s+as\s+(\w+):\s*\n"
        r"((?:.*\n)*?)"
        r"\s*for\s+\w+\s+in\s+\1\.map\(([^,]+),\s*([^)]+)\):",
        lambda m: (
            f"with mp.Pool(WORKERS) as pool:\n"
            f"    for result in pool.imap_unordered({m.group(3).strip()}, {m.group(4).strip()}):"
        ),
        text,
    )
    text = re.sub(r"^.*--workers.*\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"^.*['\"]-w['\"].*\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"workers\s*=\s*\w+,?\s*", "", text)
    return text


def rewrite_logging(text: str) -> str:
    text = re.sub(r"^import logging\n", "from loguru import logger\n", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*logger\s*=\s*logging\.getLogger\([^)]*\)\n", "", text, flags=re.MULTILINE)
    text = re.sub(
        r"logging\.basicConfig\([^)]*\)",
        'logger.remove()\nlogger.add(sys.stderr, level="INFO", '
        'format="{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {file.name}:{line} {message}")',
        text,
    )
    return text


def strip_comments_and_docstrings(tree: ast.Module) -> ast.Module:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body.pop(0)
                if not body:
                    body.append(ast.Pass())
    return tree


def merge_sources(sources: dict[str, str]) -> str:
    order = sorted(sources.keys(), key=lambda n: (n.count("/"), n != "__init__.py", n))
    chunks = []
    for name in order:
        text = sources[name]
        text = strip_six_and_py2(text)
        text = rewrite_os_path(text)
        text = rewrite_parallelism(text)
        text = rewrite_logging(text)
        text = re.sub(r"^\s*from \.+\S*\s+import[^\n]*\n", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*import \.+\S*\n", "", text, flags=re.MULTILINE)
        chunks.append(f"# --- merged from: {name} ---\n{text}")
    return "\n\n".join(chunks)


def collect_and_dedup_imports(tree: ast.Module) -> tuple[list[str], list[ast.stmt]]:
    import_lines: list[str] = []
    seen: set[str] = set()
    remaining_body: list[ast.stmt] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            line = ast.unparse(node)
            if line not in seen:
                seen.add(line)
                import_lines.append(line)
        else:
            remaining_body.append(node)
    tree.body = remaining_body
    stdlib_like = sorted(l for l in import_lines if not l.startswith("from ."))
    return stdlib_like, remaining_body


def build_output(tree: ast.Module, workers_needed: bool, needs_pathlib: bool, needs_loguru: bool) -> str:
    import_lines, _ = collect_and_dedup_imports(tree)
    body_src = ast.unparse(tree)
    header_imports = ["import argparse", "import sys"]
    if needs_pathlib:
        header_imports.append("from pathlib import Path")
    if workers_needed:
        header_imports.append("import multiprocessing as mp")
    if needs_loguru:
        header_imports.append("from loguru import logger")
    all_imports = sorted(set(header_imports) | set(import_lines))
    module_doc = (
        '"""\n'
        "TODO(manual-review): replace this placeholder with a single prompt describing,\n"
        "in natural language, the full behavior of this module -- as if it were the\n"
        "instruction originally given to an AI agent to generate this exact code.\n"
        '"""\n'
    )
    workers_const = "\nWORKERS: int = 6\n" if workers_needed else ""
    return module_doc + "\n" + "\n".join(all_imports) + "\n" + workers_const + "\n\n" + body_src + "\n"


def determine_output_path(requested: str | None) -> Path:
    candidate = Path(requested) if requested else Path("out.py")
    if not candidate.exists():
        return candidate
    n = 1
    while True:
        alt = candidate.with_name(f"{candidate.stem}_{n}{candidate.suffix}")
        if not alt.exists():
            print(
                f"note: '{candidate}' already exists, writing to '{alt}' instead",
                file=sys.stderr,
            )
            return alt
        n += 1


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-f", "--file", help="merged input file with '# filename: relpath' sentinels")
    parser.add_argument("-o", "--output", help="output .py filename (default: out.py)")
    args = parser.parse_args(list(argv) if argv is not None else None)
    sources = load_sources(args)
    merged_text = merge_sources(sources)
    try:
        tree = ast.parse(merged_text)
    except SyntaxError as exc:
        sys.exit(f"error: merged source failed to parse ({exc}); manual fixup needed before AST pass")
    tree = strip_comments_and_docstrings(tree)
    workers_needed = "mp.Pool" in merged_text or "WORKERS" in merged_text
    needs_pathlib = "Path(" in merged_text
    needs_loguru = "logger" in merged_text
    output_src = build_output(tree, workers_needed, needs_pathlib, needs_loguru)
    out_path = determine_output_path(args.output)
    out_path.write_text(output_src, encoding="utf-8")
    print(f"wrote {out_path} ({len(sources)} source files merged)")
    if "TODO(manual-review)" in output_src:
        print(
            "note: manual-review TODOs were inserted for ambiguous os.path usages and the module docstring",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
