#!/data/data/com.termux/files/usr/bin/env python
"""Prompt:

"Create a Python 3.12 command-line script intended to run under Termux (shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that recursively scans the current working directory for text/source files and builds a word-frequency index, intended to help populate or update a personal spell-check dictionary.

Main behavior and requirements:

1. **Purpose**: Walk the current directory tree, read all non-binary, reasonably-sized text files, extract English-like word tokens, count their frequencies across the whole codebase/project, and output a consolidated frequency report. The intended use is to surface frequently-occurring words (e.g., project-specific identifiers, jargon) that could be added to a personal dictionary for a spell checker.

2. **Inputs**:
   - No required positional arguments; operates on the current working directory (`Path.cwd()`) by default.
   - Should support command-line arguments (via `argparse`) to control behavior (e.g., output file path, verbosity, number of worker processes, minimum word length/frequency threshold, etc. — use reasonable flags consistent with the rest of the script's logic).
   - Reads an existing personal dictionary file located at `~/.personal_dict` (one word per line) if present, so already-known words can be excluded or treated differently from new/unknown words.

3. **File handling / filtering**:
   - Skip common non-source directories such as `.git`, `node_modules`, `.venv`, `venv`, `__pycache__`, `target`, `build`, `dist`, `.mypy_cache`, `.pytest_cache`, `.tox`, `.idea`, `.vscode`, `.eggs`.
   - Skip files whose extensions match a large predefined list of binary/media/archive/compiled formats (images, audio, video, archives, executables, fonts, databases, pickled/numpy data files, lock files, etc.).
   - Skip files larger than a maximum size limit (5 MB).
   - Only process files that pass these filters, reading them as text (handling encoding errors gracefully).

4. **Word extraction**:
   - Use a regular expression to extract alphabetic word tokens of at least 2 letters (`[A-Za-z]{2,}`) from file contents.
   - Optionally leverage NLTK's tokenizer (`punkt`/`punkt_tab`) for more accurate tokenization, ensuring the required NLTK data is downloaded on demand if missing (handle lookup/download errors silently without crashing).

5. **Performance**:
   - Use Python's `multiprocessing` module to process files in parallel across multiple worker processes for speed on large directory trees, merging per-file word counts into a single global `collections.Counter`.

6. **Output**:
   - Write the aggregated word frequency results as JSON to `word_freq.json` in the current working directory (word → count mapping), sorted or filtered as appropriate.
   - Optionally print a summary to stdout (e.g., top N most frequent unknown words) to help the user decide what to add to their personal dictionary.

7. **Robustness**:
   - Handle file read errors, permission errors, and decoding errors without stopping the whole scan.
   - Use `contextlib.suppress` or similar patterns for non-critical failures (like NLTK data l well-structured Python script using `argparse`, `multiprocessing`, `re`, `json`, `pathlib.Path`, and optionally `nltk`, following the constants and structure implied above (`CWD`, `DICT_PATH`, `JSON_PATH`, `SKIP_DIRS`, `BINARY_EXT`, `MAX_BYTES`, `WORD_RE`)."
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/NBVrt7eH4StQSRRAT5Cn9A"""

from __future__ import annotations
import argparse
import contextlib
import json
import multiprocessing as mp
import os
import re
from collections import Counter
from pathlib import Path

CWD = Path.cwd()
DICT_PATH = Path.home() / ".personal_dict"
JSON_PATH = CWD / "word_freq.json"
SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "target",
    "build",
    "dist",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".idea",
    ".vscode",
    ".eggs",
}
BINARY_EXT = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tiff",
    ".webp",
    ".ico",
    ".svgz",
    ".pdf",
    ".zip",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".tar",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".a",
    ".o",
    ".obj",
    ".bin",
    ".pyc",
    ".pyo",
    ".class",
    ".jar",
    ".war",
    ".mp3",
    ".mp4",
    ".m4a",
    ".wav",
    ".flac",
    ".ogg",
    ".avi",
    ".mkv",
    ".mov",
    ".webm",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".iso",
    ".img",
    ".dmg",
    ".pkl",
    ".npy",
    ".npz",
    ".h5",
    ".parquet",
    ".lock",
}
MAX_BYTES = 5 * 1024 * 1024
WORD_RE = re.compile(r"[A-Za-z]{2,}")
_TOKENIZER = None


def _ensure_punkt():
    import nltk

    for res in ("tokenizers/punkt", "tokenizers/punkt_tab"):
        try:
            nltk.data.find(res)
        except LookupError:
            with contextlib.suppress(Exception):
                nltk.download(res.split("/")[-1], quiet=True)


def _make_regex():
    def tok(text):
        return [m.group().lower() for m in WORD_RE.finditer(text)]

    return tok


def _make_nltk():
    from nltk.tokenize import word_tokenize

    _ensure_punkt()

    def tok(text):
        try:
            return [t.lower() for t in word_tokenize(text) if t.isalpha() and len(t) > 1]
        except Exception:
            return []

    return tok


def _make_blingfire():
    import blingfire

    def tok(text):
        try:
            raw = blingfire.text_to_words(text)
        except Exception:
            return []
        return [w.lower() for w in raw.split() if w.isalpha() and len(w) > 1]

    return tok


def _make_sacremoses():
    from sacremoses import MosesTokenizer

    mt = MosesTokenizer(lang="en")

    def tok(text):
        try:
            toks = mt.tokenize(text, return_str=False)
        except Exception:
            return []
        return [w.lower() for w in toks if w.isalpha() and len(w) > 1]

    return tok


def _make_spacy():
    import spacy

    try:
        nlp = spacy.load(
            "en_core_web_sm",
            disable=["ner", "parser", "lemmatizer", "tagger", "attribute_ruler"],
        )
    except OSError:
        nlp = spacy.blank("en")

    def tok(text):
        try:
            doc = nlp(text)
        except Exception:
            return []
        return [t.text.lower() for t in doc if t.is_alpha and len(t.text) > 1]

    return tok


def _make_pyonmttok():
    import pyonmttok

    tokenizer = pyonmttok.Tokenizer("conservative", joiner_annotate=False)

    def tok(text):
        try:
            tokens, _ = tokenizer.tokenize(text)
        except Exception:
            return []
        return [w.lower() for w in tokens if w.isalpha() and len(w) > 1]

    return tok


TOKENIZER_FACTORIES = {
    "regex": _make_regex,
    "nltk": _make_nltk,
    "blingfire": _make_blingfire,
    "sacremoses": _make_sacremoses,
    "spacy": _make_spacy,
    "pyonmttok": _make_pyonmttok,
}


def _init_worker(mode):
    global _TOKENIZER
    _TOKENIZER = TOKENIZER_FACTORIES[mode]()


def decode_bytes(data):
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return ""


def walk(root):
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for e in it:
                    try:
                        if e.is_dir(follow_symlinks=False):
                            if e.name in SKIP_DIRS:
                                continue
                            stack.append(Path(e.path))
                        elif e.is_file(follow_symlinks=False):
                            yield Path(e.path)
                    except OSError:
                        continue
        except OSError:
            continue


def process_file(path_str):
    try:
        data = Path(path_str).read_bytes()
    except OSError:
        return Counter()
    if b"\x00" in data[:8192]:
        return Counter()
    text = decode_bytes(data)
    if not text:
        return Counter()
    return Counter(_TOKENIZER(text))


def atomic_write_text(path, text):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_json_stream(path, pairs):
    tmp = path.with_name(path.name + ".tmp")
    n = len(pairs)
    with tmp.open("w", encoding="utf-8") as f:
        f.write("[\n")
        for i, (w, c) in enumerate(pairs):
            f.write("  ")
            f.write(json.dumps([w, c], ensure_ascii=False))
            if i < n - 1:
                f.write(",")
            f.write("\n")
        f.write("]\n")
    os.replace(tmp, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--tokenizer",
        choices=tuple(TOKENIZER_FACTORIES),
        default="nltk",
    )
    args = parser.parse_args()
    skip = {DICT_PATH.resolve(), JSON_PATH.resolve()}
    candidates = []
    for p in walk(CWD):
        try:
            rp = p.resolve()
        except OSError:
            continue
        if rp in skip:
            continue
        if p.suffix.lower() in BINARY_EXT:
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size == 0 or size > MAX_BYTES:
            continue
        candidates.append((str(p), size))
    candidates.sort(key=lambda x: -x[1])
    paths = [c[0] for c in candidates]
    counter = Counter()
    if paths:
        procs = min(8, mp.cpu_count() or 1)
        with mp.Pool(
            processes=procs,
            initializer=_init_worker,
            initargs=(args.tokenizer,),
        ) as pool:
            for c in pool.imap_unordered(process_file, paths, chunksize=1):
                counter.update(c)
    from spellchecker import SpellChecker

    spell = SpellChecker()
    known = spell.word_frequency.words()
    custom = {w: c for w, c in counter.items() if w not in known}
    words_sorted = sorted(custom)
    atomic_write_text(
        DICT_PATH,
        "\n".join(words_sorted) + ("\n" if words_sorted else ""),
    )
    pairs = sorted(custom.items(), key=lambda kv: (-kv[1], kv[0]))
    write_json_stream(JSON_PATH, pairs)
    print(f"Tokenizer:                        {args.tokenizer}")
    print(f"Files scanned:                    {len(paths)}")
    print(f"Unique tokens found:              {len(counter)}")
    print(f"Words added to custom dictionary: {len(words_sorted)}")
    print(f"Dictionary written to:            {DICT_PATH}")
    print(f"Word+freq JSON written to:        {JSON_PATH}")


if __name__ == "__main__":
    main()
