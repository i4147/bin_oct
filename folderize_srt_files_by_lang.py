#!/data/data/com.termux/files/usr/bin/env python
"""I'm going to write the prompt directly since it's a self-contained text-generation task.

Write a complete, self-contained Python 3 script (intended to run under Termux on Android, so the shebang points to the Termux Python path) that recursively scans a directory for subtitle files and organizes them into folders by detected language.

**Purpose:** Walk a directory tree, detect the language of each `.srt` subtitle file by analyzing its text content, and sort the files into per-language folders within the scanned directory.

**Dependencies:** Use `pathlib.Path` from the standard library and the third-party `pycld2` package (Compact Language Detector 2). Include `from __future__ import annotations` at the top for modern type hints such as `list[Path]`.

**Required functions:**

1. `get_srt_files(directory: Path) -> list[Path]` — returns every `.srt` file found recursively under the given directory, using a recursive glob.

2. `detect_language(file_path: Path)` — reads the file as UTF-8 and builds a text sample by keeping only lines that are non-empty after stripping whitespace, that are not purely numeric (subtitle index lines), and that do not contain the `-->` timestamp separator. If the resulting text is empty, return `None`. Otherwise pass the text to `pycld2.detect`, which returns a tuple of (is_reliable, text_bytes_found, details). If details are missing or the first entry is falsy, return `None`. Unpack the first detail entry into language name, language code, percent, and score. If the code is `"un"` or the name lowercased equals `"unknown"`, return `None`. Otherwise return a tuple of (language name, language code). Wrap the whole body in a try/except that catches any `Exception`, prints a warning line including the file's name and the error message (prefixed with a warning symbol and indented by two spaces), and returns `None`.

3. `organize_subtitles(directory: Path = Path.cwd()) -> None` — the main routine. Note that the default is evaluated at import time, so the current working directory is captured when the module loads.
   - Print a scanning header showing the absolute path of the directory, followed by a blank line.
   - Collect SRT files via `get_srt_files`. If none are found, print a "no .srt files found" message and return.
   - Print how many SRT files were found.
   - Print a separator line of 70 equals signs.
   - Maintain a dictionary `language_folders` mapping language names to lists or folder information for grouping.
   - For each file, print a progress line with the file name, detect its language, and group it. Files whose language cannot be determined should be handled gracefully (for example, placed in an "Unknown" group or skipped with a message) rather than crashing.
   - After detection, create one folder per detected language directly inside the scanned directory (named after the language), and move each file into its language's folder. Create folders with parent-tolerant, exist-ok semantics. Handle filename collisions in the destination by not silently overwriting existing files.
   - Print a final summary listing each language folder with its file count, and a completion message.

**Entry point:** Guard execution with `if __name__ == "__main__":` and call `organize_subtitles()` with no arguments.

**Behavior and edge cases to honor:**
- Use UTF-8 for all file reads; treat decoding failures as per-file errors that are reported and skipped, not fatal.
- Ignore files that yield no usable text or an undetectable language.
- The script should never crash the whole run because of a single bad file.
- Use emoji-prefixed console output (magnifying glass for scanning, document for each file, bar chart for counts, cross mark for errors, warning sign for warnings) and visually consistent separators, matching the style of a terminal progress report.
- Keep output in English.

**Usage:** Run the script directly from the directory containing the subtitles, or via `python` with the script's path; it operates on the current working directory by default. Make it executable with a Termux-compatible shebang.

Produce only the complete script as the deliverable, with clear, idiomatic code, concise comments where helpful, and no extra commentary.
---"""

from __future__ import annotations

from pathlib import Path

import pycld2 as cld2


def get_srt_files(directory: Path) -> list[Path]:
    return list(directory.rglob("*.srt"))


def detect_language(file_path: Path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.split("\n")
        subtitle_text = "\n".join(line for line in lines if line.strip() and not line.isdigit() and "-->" not in line)
        if not subtitle_text.strip():
            return None
        _is_reliable, _text_bytes_found, details = cld2.detect(subtitle_text)
        if not details or not details[0]:
            return None
        lang_name, lang_code, _percent, _score = details[0]
        if lang_code == "un" or lang_name.lower() == "unknown":
            return None
        return lang_name, lang_code
    except Exception as e:
        print(f"  ⚠ Error reading {file_path.name}: {e}")
    return None


def organize_subtitles(directory: Path = Path.cwd()) -> None:
    print(f"🔍 Scanning directory: {directory.absolute()}\n")
    srt_files = get_srt_files(directory)
    if not srt_files:
        print("❌ No .srt files found in the directory.")
        return
    print(f"📊 Found {len(srt_files)} SRT file(s)\n")
    print("=" * 70)
    language_folders = {}
    for file_path in srt_files:
        print(f"\n📄 Processing: {file_path.name}")
        result = detect_language(file_path)
        if result:
            lang_name, lang_code = result
            print(f"   ✓ Detected language: {lang_name} ({lang_code})")
            folder_name = f"{lang_name}_{lang_code}".lower()
            if folder_name not in language_folders:
                language_folders[folder_name] = []
            language_folders[folder_name].append(file_path)
        else:
            print(f"   ⚠ Could not detect language")
    print("\n" + "=" * 70)
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
