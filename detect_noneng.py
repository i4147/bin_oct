#!/data/data/com.termux/files/usr/bin/python
"""Write a self-contained prompt that describes a Python command-line tool for scanning a directory tree and reporting which text files contain CJK, Kana, Hangul, or Arabic characters. The prompt must cover purpose, inputs and outputs, dependencies, logic, error handling, edge cases, and usage, without including any code.

Create a Python 3 command-line script (intended to run in Termux on Android, with a shebang pointing to the Termux Python at /data/data/com.termux/files/usr/bin/python) that scans a directory tree and reports which text files contain non-Latin scripts. It must be runnable as a standalone file with no other project modules.

**Purpose**
Recursively scan a target directory for text files and detect whether they contain characters from four script families: CJK ideographs (Chinese/Japanese Kanji, including Extension A and the compatibility ideographs block), Japanese Kana (Hiragana and Katakana), Korean Hangul (Jamo, compatibility Jamo, and syllables), and Arabic (including Arabic Supplement, Presentation Forms A and B). Produce a categorized report and optionally act on the results.

**Dependencies**
- Standard library: argparse, re, shutil, sys, pathlib, concurrent.futures, and `from __future__ import annotations`.
- Third-party: the `rich` library, using Console, and Progress with the columns BarColumn, MofNCompleteColumn, SpinnerColumn, TextColumn, TimeElapsedColumn, and TimeRemainingColumn.
- Use `concurrent.futures.InterpreterPoolExecutor` if available; otherwise fall back to `ProcessPoolExecutor` under the same alias. Use `as_completed` to collect results.

**Constants**
- Compile four regular expressions matching the Unicode ranges above.
- A maximum file size of 10 MiB; files larger than this are skipped.
- A frozen set of directory names to skip during traversal, including version control folders (.git, .hg, .svn, .bzr), dependency and build folders (node_modules, dist, build, target, vendor), tool caches (__pycache__, .mypy_cache, .pytest_cache, .ruff_cache, .tox, .cache), virtual environments (.venv, venv, env), framework output (.next, .nuxt), and editor folders (.idea, .vscode).

**Text detection helper**
A function that takes raw bytes and decides whether they look like text: empty data is not text; any null byte in the first 8192 bytes means binary; otherwise sample the first 8192 bytes and count printable bytes (including common whitespace such as tab, newline, carriage return, form feed), treating the file as text only if the printable ratio is high (roughly 85% or more). Document the exact threshold you choose in the implementation as a named constant.

**Per-file analysis**
For each candidate file (within the size limit and not binary):
- Read the file as bytes, decode as UTF-8 with replacement for invalid sequences.
- Run each regex and count matches for each script category.
- Return a result containing the file path, the per-category counts, and the total count.
- Handle read errors (permission denied, I/O errors, disappearing files) by returning an error marker for that file rather than crashing; the run must continue.

**Traversal**
- Walk the target directory recursively, pruning any directory whose name is in the skip set.
- Skip symbolic links to avoid cycles.
- Collect only regular files.
- Process files in parallel using the executor, submitting each file's analysis and collecting results with `as_completed`.
- Show a live rich progress display (spinner, description, bar, count of completed/total, elapsed time, and estimated remaining time) during the scan.

**Command-line interface (argparse)**
- A positional argument for the directory to scan, defaulting to the current directory.
- Options to: choose which script categories to include in the report (any of CJK, Kana, Hangul, Arabic; default all); set a minimum match threshold below which files are not reported; output as a plain list versus a summary table; optionally delete or move matching files (requires an explicit confirmation flag and should never delete without it; preview by default); override the maximum file size; set the number of worker processes; and a quiet mode that suppresses the progress display.
- Validate arguments: the target must exist and be a directory; print a clear error to stderr and exit with a nonzero code otherwise. Clamp or reject invalid worker counts.

**Output**
- Use rich Console for colorized output to stdout, and stderr for errors.
- Report, for each matching file, its relative path and the counts per category, sorted by total matches descending.
- Print a final summary: number of files scanned, number matched, number skipped (binary, too large, or in skip directories), number with errors, and total elapsed time.
- If a summary table mode is selected, render the summary with a rich Table.
- Respect terminal width; if the terminal is not a TTY, disable colors and the live progress display automatically.

**Error handling and edge cases**
- Handle KeyboardInterrupt gracefully: cancel pending futures, print a message, and exit with code 130.
- Handle an empty directory or no matches with a clear message and exit code 0.
- Handle a nonexistent path, a file path given instead of a directory, and unreadable subdirectories without aborting.
- Treat zero-byte files as non-text and skip them.
- Handle file names containing non-ASCII characters and spaces correctly when printing.
- Do not follow symlinks; do not count files inside skipped directories.
- Ensure executor shutdown happens in all exit paths.

**Execution details**
- Include a main guard and a `main()` function returning an integer exit code, which is passed to `sys.exit`.
- Keep the script a single file with type hints compatible with `from __future__ import annotations`.
- Use docstrings and brief comments explaining the detection threshold, skip rules, and the deletion safety guard.
---"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from concurrent.futures import as_completed
from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

try:
    from concurrent.futures import InterpreterPoolExecutor
except ImportError:
    from concurrent.futures import ProcessPoolExecutor as InterpreterPoolExecutor


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
KANA_RE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]")
HANGUL_RE = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]")
ARABIC_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f\ufb50-\ufdff\ufe70-\ufeff]")

MAX_BYTES: int = 10 * 1024 * 1024
SKIP_DIRS: frozenset[str] = frozenset({
    ".git",
    ".hg",
    ".svn",
    ".bzr",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".cache",
    ".idea",
    ".vscode",
    "target",
    "vendor",
})


def _looks_like_text(data: bytes) -> bool:
    if not data:
        return False
    if b"\x00" in data[:8192]:
        return False
    sample = data[:8192]
    printable = sum(1 for b in sample if b >= 32 or b in (9, 10, 13))
    return printable / len(sample) > 0.90


def detect(path_str: str) -> tuple[str, list[str]] | None:
    path = Path(path_str)
    try:
        if path.is_symlink():
            return None
        size = path.stat().st_size
        if size == 0 or size > MAX_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None

    if not _looks_like_text(data):
        return None

    text = data.decode("utf-8", errors="ignore")

    has_kana = KANA_RE.search(text) is not None
    has_cjk = CJK_RE.search(text) is not None

    langs: list[str] = []
    if has_kana:
        langs.append("japanese")
    if has_cjk and not has_kana:
        langs.append("chinese")
    if HANGUL_RE.search(text):
        langs.append("korean")
    if ARABIC_RE.search(text):
        langs.append("persian")

    return (path_str, langs) if langs else None


def _walk(root: Path) -> list[str]:
    out: list[str] = []
    stack: list[Path] = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir():
                    if entry.name in SKIP_DIRS:
                        continue
                    stack.append(entry)
                elif entry.is_file():
                    out.append(str(entry))
            except OSError:
                continue
    return out


def _unique_dest(dest_dir: Path, name: str) -> Path:
    dest = dest_dir / name
    if not dest.exists():
        return dest
    stem, suffix = Path(name).stem, Path(name).suffix
    i = 1
    while True:
        candidate = dest_dir / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recursively detect Chinese/Persian/Japanese/Korean text in files. Dry run by default.",
    )
    parser.add_argument(
        "-c",
        "--copy",
        action="store_true",
        help="copy matched files into ~/tmp/langs/<lang>/ directories",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="root directory to scan (default: current dir)",
    )
    args = parser.parse_args()

    console = Console()
    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        console.print(f"[red]error:[/] not a directory: {root}", stderr=True)
        return 2

    with console.status(f"[bold cyan]Walking[/] {root} …") as status:
        files = _walk(root)
        status.update(f"[bold cyan]Walking done[/] — {len(files)} file(s)")

    hits: list[tuple[str, list[str]]] = []

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("[dim]{task.fields[found]} hits"),
        TimeElapsedColumn(),
        TextColumn("eta"),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )

    with progress:
        task = progress.add_task("Scanning", total=len(files), found=0)
        with InterpreterPoolExecutor() as ex:
            futures = {ex.submit(detect, f): f for f in files}
            for fut in as_completed(futures):
                try:
                    result = fut.result()
                except Exception:
                    result = None
                if result is not None:
                    hits.append(result)
                progress.update(
                    task,
                    advance=1,
                    found=len(hits),
                )

    dest_root = Path.home() / "tmp" / "langs"

    if hits:
        console.rule("[bold green]Matches")
        for path_str, langs in sorted(hits):
            src = Path(path_str)
            try:
                rel = src.relative_to(root)
            except ValueError:
                rel = src
            console.print(f"{rel} [bold magenta]→[/] {', '.join(langs)}")

        if args.copy:
            with console.status("[bold cyan]Copying …"):
                for path_str, langs in hits:
                    src = Path(path_str)
                    for lang in langs:
                        dest_dir = dest_root / lang
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        dest = _unique_dest(dest_dir, src.name)
                        shutil.copy2(src, dest)

    verb = "copied" if args.copy else "would copy (dry run)"
    console.print(
        f"\n[bold]Scanned[/] {len(files)} file(s); "
        f"[bold green]{len(hits)}[/] match(es). "
        f"[italic]{verb}[/] → {dest_root}/<lang>/"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
