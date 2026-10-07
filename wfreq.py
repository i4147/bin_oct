#!/data/data/com.termux/files/usr/bin/env python
"""Design a cross-platform Python 3.12 command-line tool (intended to run under Termux on Android, with a `/data/data/com.termux/files/usr/bin/python3.12` shebang) that scans one or more given directories recursively, extracts words from all readable text-like files, and builds a "personal dictionary" of words that are not recognized by a spellchecker — intended to be used as a custom/personal word list (e.g., for seeding a spellchecker's personal dictionary) at `~/.personal_dict`.

Key requirements:

1. **Purpose**: Walk a directory tree, read the textual content of files, tokenize words, check each unique word against a standard English spellchecker (using the `pyspellchecker` library's `SpellChecker` class), and collect/report wordsagged as misspelled/unknown — under the assumption that many of these are actually legitimate project-specific terms, names, identifiers, or jargon worth adding to a personal dictionary.

2. **Word extraction**: Use a Unicode-aware regex to match words, defined as sequences of alphabetic characters (excluding digits and underscores) that may include internal apostrophes (both `'` and the Unicode `’` character) joining letter sequences (ctly capture contractions/possessives like "don't" or "O'Brien").

3. **File filtering / binary detection**:
   - Maintain a set of directory names to skip entirely during traversal (version control folders like `.git`, `.svn`, `.hg`, `.bzr`; editor/IDE folders like `.idea`, `.vscode`, `.vs`; caches like `__pycache__`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.cache`, `.tox`; dependency/package folders like `node_modules`, `bower_components`, `vendor`, `site-packages`, `dist-packages`, `Pods`, `DerivedData`; virtual environments like `venv`, `.venv`, `env`, `.env`, `virtualenv`, `.virtualenv`; build output folders like `dist`, `build`, `target`, `out`, `.next`, `.nuxt`, `.svelte-kit`, `.parcel-cache`, `coverage`, `htmlcov`; and misc tool caches like `.gradle`, `.m2`, `.terraform`).
   - Maintain a set of file extensions/suffixes to skip becausenon code (`.pyc`, `.pyo`, `.pyd`, `.so`, `.dylib`, `.dll`, `.exe`, `.bin`, `.o`, `.a`, `.lib`, `.class`, `.jar`, `.war`), archives (`.zip`, `.tar`, `.gz`, `.bz2`, `.xz`, `.7z`, `.rar`), images (`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.webp`, `.ico`, `.tif`, `.tiff`, `.svg`), audio/video (`.mp3`, `.mp4`, `.m4a`, `.wav`, `.ogg`, `.flac`, `.avi`, `.mkv`, `.mov`, `.webm`), and documents/office formats (`.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, and similarly other common office/binary formats).
   - Additionally perform a content-based binary/text heuristic: define a set/table of byte values considered "text characters" (tab, newline, carriage return, form feed, escape, and printable byte range 0x20–0xFF excluding 0x7F) and use it to sniff a sample of a file's bytes to decide whether the file is text or binary, skipping binary files even if their extension wasn't already excluded.

4. **Concurrency**: Use the `multiprocessing` module to parallelize scanning/reading of files across available CPU cores for performance on large directory trees, with appropriate type hints (`Iterable`, `Iterator`) for the generator/collection functions involved.

5. **Output**: Write the resulting list of unknown/flagged words (deduplicated, likely sorted) to the file `~/.personal_dict` (one word similar simple format su file), also print relevant progress/summary information to standard output (and errors to standard error as appropriate).

6. **CLI behavior**: Accept one or more paths via command-line arguments (`sys.argv`), validate that they exist and are directories, and process each; handle errors gracefully (e.g., unreadable files, permission errors) without crashing the whole scan.

7. **Code style**: Use `from __future__ import annotations`, modern type hints, module-level constants for the skip-sets and regex, and organize logic into clear, reusable functions suitable for a single-file script distributed for Termux/Android but portable to any POSIX Python 3.12 environment.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/RqqBgwfA4Xnn8rdTg6JkLf"""

from __future__ import annotations
import multiprocessing as mp
import re
import sys
from pathlib import Path
from typing import Iterable, Iterator
from spellchecker import SpellChecker

WORD_RE = re.compile(r"[^\W\d_]+(?:['\u2019][^\W\d_]+)*", re.UNICODE)
_TEXT_CHARS = bytes({7, 8, 9, 10, 12, 13, 27} | (set(range(0x20, 0x100)) - {0x7F}))
_OUTPUT_PATH = Path.home() / ".personal_dict"
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".bzr",
    ".idea",
    ".vscode",
    ".vs",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".cache",
    "__pycache__",
    "node_modules",
    "bower_components",
    "vendor",
    "venv",
    ".venv",
    "env",
    ".env",
    "virtualenv",
    ".virtualenv",
    "site-packages",
    "dist-packages",
    "dist",
    "build",
    "target",
    "out",
    ".next",
    ".nuxt",
    ".svelte-kit",
    ".parcel-cache",
    "coverage",
    "htmlcov",
    ".gradle",
    ".m2",
    "Pods",
    "DerivedData",
    ".terraform",
}
SKIP_FILE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dylib",
    ".dll",
    ".exe",
    ".bin",
    ".o",
    ".a",
    ".lib",
    ".class",
    ".jar",
    ".war",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".webp",
    ".ico",
    ".tif",
    ".tiff",
    ".svg",
    ".mp3",
    ".mp4",
    ".m4a",
    ".wav",
    ".ogg",
    ".flac",
    ".avi",
    ".mkv",
    ".mov",
    ".webm",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
    ".lock",
}


def _is_binary(file_path: Path, chunk_size: int = 1024, threshold: float = 0.30) -> bool:
    try:
        with file_path.open("rb") as f:
            chunk = f.read(chunk_size)
    except OSError:
        return True
    if not chunk:
        return False
    if b"\x00" in chunk:
        return True
    nontext = chunk.translate(None, _TEXT_CHARS)
    return (len(nontext) / len(chunk)) > threshold


def _extract_words(file_path: Path) -> set[str]:
    words: set[str] = set()
    try:
        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                for match in WORD_RE.findall(line):
                    token = match.strip("'\u2019").lower()
                    if len(token) > 1:
                        words.add(token)
    except OSError:
        return words
    return words


def _process_file(file_path_str: str) -> set[str]:
    path = Path(file_path_str)
    try:
        if path.is_symlink() or not path.is_file():
            return set()
        if path.suffix.lower() in SKIP_FILE_SUFFIXES:
            return set()
        if _is_binary(path):
            return set()
        return _extract_words(path)
    except OSError:
        return set()


def _iter_candidate_files(root: Path, skip: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in root.walk(follow_symlinks=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not (dirpath / d).is_symlink()]
        for name in filenames:
            entry = dirpath / name
            try:
                if entry == skip:
                    continue
                if entry.is_symlink() or not entry.is_file():
                    continue
                if entry.suffix.lower() in SKIP_FILE_SUFFIXES:
                    continue
            except OSError:
                continue
            yield entry


def collect_words(root_dir: Path, output_path: Path, workers: int | None = None) -> set[str]:
    all_words: set[str] = set()
    files = [str(p) for p in _iter_candidate_files(root_dir, output_path)]
    if not files:
        return all_words
    if workers is None:
        workers = max(1, mp.cpu_count() or 1)
    chunksize = max(1, len(files) // (workers * 8))
    with mp.Pool(processes=workers) as pool:
        try:
            for word_set in pool.imap_unordered(_process_file, files, chunksize=chunksize):
                all_words.update(word_set)
        except KeyboardInterrupt:
            pool.terminate()
            pool.join()
            raise
    return all_words


def filter_unknown_words(words: set[str]) -> set[str]:
    spell = SpellChecker()
    try:
        return set(spell.unknown(words))
    except Exception:
        unknown: set[str] = set()
        for word in words:
            try:
                if word not in spell:
                    unknown.add(word)
            except Exception:
                continue
        return unknown


def _load_existing(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return {line.strip() for line in f if line.strip()}
    except OSError:
        return set()


def save_words(words: Iterable[str], output_path: Path) -> int:
    merged = _load_existing(output_path)
    before = len(merged)
    merged.update(words)
    added = len(merged) - before
    text = "\n".join(sorted(merged))
    if text:
        text += "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(output_path)
    return added


def main() -> int:
    root_dir = Path.cwd()
    output_path = _OUTPUT_PATH
    try:
        all_words = collect_words(root_dir, output_path)
    except Exception as exc:
        print(f"error while collecting words: {exc}", file=sys.stderr)
        return 1
    try:
        unknown_words = filter_unknown_words(all_words)
    except Exception as exc:
        print(f"error while filtering words: {exc}", file=sys.stderr)
        return 1
    try:
        added = save_words(unknown_words, output_path)
    except OSError as exc:
        print(f"error while writing output: {exc}", file=sys.stderr)
        return 1
    print(f"Total unique words found: {len(all_words)}")
    print(f"Words not in pyspellchecker dictionary: {len(unknown_words)}")
    print(f"New words added to dictionary: {added}")
    print(f"Saved to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
