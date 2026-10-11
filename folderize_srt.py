#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python script which detects the dominant language of subtitle (.srt) files in a directory using a multiprocessing pool and a language-detection library, with majority voting. Describe the full behavior without including code.

Create a Python command-line script that scans a directory for subtitle files and determines the dominant language of each one using majority voting over per-line language detection.

**Purpose:** For every `.srt` subtitle file in a given directory, read its dialogue text, detect the language of each line, and report the language that appears most often (the majority vote) for that file.

**Dependencies:**
- Python 3 with `from __future__ import annotations` for type hints.
- Standard library: `collections.Counter`, `multiprocessing.Pool` and `cpu_count`, `pathlib.Path`.
- Third-party: the `lingua` library (`lingua-language-detector`), using `LanguageDetectorBuilder.from_all_languages().build()`.

**Shebang and target environment:** Use a shebang pointing to the Termux Python interpreter at `/data/data/com.termux/files/usr/bin/env python`, so the script runs on Android under Termux.

**Constants and globals:**
- `BATCH_SIZE = 8`, the number of lines grouped into each batch.
- A module-level `_detector` variable initialized to `None`, set per worker process.

**Worker initialization:** Define an initializer function that, when each pool worker starts, builds the lingua detector once and stores it in the module-level `_detector` global. This avoids rebuilding the detector for every line.

**Batch detection:** Define a function that takes a list of text lines and returns a list of tuples. For each line, call the detector's language detection. If a language is found, return the line, the language's English name, and its ISO 639-1 code (as a string name). If no language is determined, return the line with `None` for both values. Any exception raised during detection for a line must be caught, and that line returned with `None` values, so one failure never aborts the batch.

**File discovery:** Define a function that returns all `*.srt` files directly inside a given directory (non-recursive), as a list of `Path` objects.

**Per-file majority vote:** Define a function that takes a file path and a shared `Pool`:
1. Open the file with UTF-8 encoding and read all lines. Handle decoding and I/O errors gracefully (catch exceptions and return `None` for that file rather than crashing).
2. Filter lines: strip whitespace; skip empty lines, SRT timestamp lines (those containing `-->`), and pure-digit lines (subtitle sequence numbers). Count skipped lines. Keep the remaining text lines.
3. If no text lines remain, return `None`.
4. Split the text lines into consecutive batches of `BATCH_SIZE`.
5. Submit the batches to the pool for parallel detection (e.g., via `imap` or `map`), collecting the results.
6. Flatten the results and count the detected languages with `Counter`, ignoring lines whose language is `None`. Determine the most common language name (and code) as the majority vote. If nothing was detected, return `None`.
7. Return a result that includes the winning language, its ISO code, the number of lines that voted for it, the total number of text lines considered, and the skipped-line count, so the caller can report confidence.

**Main entry point:** Under the standard `__main__` guard:
- Determine the target directory. Use the current working directory by default; accept an optional command-line argument giving another directory path. Validate that the path exists and is a directory, printing a clear error and exiting with a non-zero status otherwise.
- Gather `.srt` files; if none are found, print a message and exit cleanly.
- Create a `multiprocessing.Pool` with `cpu_count()` workers, using `_init_worker` as the initializer.
- Process each file sequentially (the pool parallelizes within each file's batches), and print per-file results: file name, detected language name, ISO code, vote count out of total lines, and skipped count. Print a clear notice for files that yielded no result.
- Close and join the pool properly (use a context manager or explicit close/join), even if an error occurs.
- Print a final summary, such as a count of files processed and a tally of languages across files.

**Error handling and edge cases:**
- Empty directories, no `.srt` files, unreadable or non-UTF-8 files, files with only timestamps/numbers, and lines with undetectable language must all be handled without crashing.
- Ctrl+C (KeyboardInterrupt) should terminate the pool cleanly and exit.
- Keep the worker-side function and initializer at module top level so they are picklable for multiprocessing.

**Style:** Use type hints, concise docstrings or comments only where helpful, and keep the script a single file with no external configuration. Output human-readable console text only; no JSON output is required.

**Usage:** Run as `python script.py [directory]`, or execute directly on Termux since it has a shebang. The first run may be slow because the lingua model is loaded in each worker.
---"""

from __future__ import annotations

from collections import Counter
from multiprocessing import Pool, cpu_count
from pathlib import Path

from lingua import LanguageDetectorBuilder

BATCH_SIZE = 8
_detector = None


def _init_worker():
    global _detector
    _detector = LanguageDetectorBuilder.from_all_languages().build()


def _detect_batch(lines: list[str]):
    out = []
    for line in lines:
        try:
            d = _detector.detect_language_of(line)
            if d:
                out.append((line, d.name, d.iso_code_639_1.name))
            else:
                out.append((line, None, None))
        except Exception:
            out.append((line, None, None))
    return out


def get_srt_files(directory: Path) -> list[Path]:
    return list(directory.glob("*.srt"))


def detect_language_majority_vote(file_path: Path, pool: Pool):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
        text_lines = []
        skipped_count = 0
        for line in raw_lines:
            s = line.strip()
            if not s or "-->" in s or s.isdigit():
                skipped_count += 1
                continue
            text_lines.append(s)
        if not text_lines:
            return None
        batches = [text_lines[i : i + BATCH_SIZE] for i in range(0, len(text_lines), BATCH_SIZE)]
        batch_results = pool.map(_detect_batch, batches)
        line_count = 0
        lang_counter = Counter()
        iso_lookup = {}
        for batch in batch_results:
            for line, name, iso in batch:
                line_count += 1
                if name:
                    lang_counter[name] += 1
                    iso_lookup[name] = iso
                    print(f'      Line {line_count}: {name} - "{line[:50]}{"..." if len(line) > 50 else ""}"')
        if lang_counter:
            most_common_name, _ = lang_counter.most_common(1)[0]
            most_common_iso = iso_lookup[most_common_name]
            print(f"\n   📊 Statistics:")
            print(f"      Total lines processed: {line_count}")
            print(f"      Lines skipped: {skipped_count}")
            print(f"      Language votes:")
            for lang_name, count in lang_counter.most_common():
                pct = (count / line_count) * 100
                print(f"         {lang_name}: {count} votes ({pct:.1f}%)")
            return (most_common_name, most_common_iso)
    except Exception as e:
        print(f"  ⚠ Error reading {file_path.name}: {e}")
    return None


def organize_subtitles(directory: Path = Path.cwd()) -> None:
    print(f"🔍 Scanning directory: {directory.absolute()}\n")
    srt_files = get_srt_files(directory)
    if not srt_files:
        print("❌ No .srt files found in the directory.")
        return
    print(f"📊 Found {len(srt_files)} SRT file(s)")
    print(f"⚙️  Using {cpu_count()} worker processes (batch size = {BATCH_SIZE})\n")
    print("=" * 80)
    language_folders = {}
    with Pool(initializer=_init_worker) as pool:
        for file_path in srt_files:
            print(f"\n📄 Processing: {file_path.name}")
            print("─" * 80)
            detected = detect_language_majority_vote(file_path, pool)
            if detected:
                lang_name, lang_code = detected
                print(f"\n   ✅ FINAL RESULT: {lang_name} ({lang_code})")
                folder_name = f"{lang_name}_{lang_code}".lower()
                language_folders.setdefault(folder_name, []).append(file_path)
            else:
                print(f"\n   ⚠ Could not detect language")
            print("=" * 80)
    print(f"\n📁 Creating folders and moving files...\n")
    total_moved = 0
    for folder_name, files in sorted(language_folders.items()):
        folder_path = directory / folder_name
        folder_path.mkdir(exist_ok=True)
        print(f"📂 {folder_name.upper()} ({len(files)} file(s))")
        for file_path in files:
            new_path = folder_path / file_path.name
            file_path.rename(new_path)
            print(f"   ➜ {file_path.name}")
            total_moved += 1
    print(f"\n✅ Complete! Moved {total_moved} file(s) into {len(language_folders)} language folder(s).")


if __name__ == "__main__":
    organize_subtitles()
