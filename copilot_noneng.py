#!/data/data/com.termux/files/usr/bin/env python
"""You are writing a Python 3 command-line script from scratch. Produce a single, self-contained file that meets the specification below. Match the style of a modern, idiomatic Python script: type hints throughout, `from __future__ import annotations`, a Termux-style shebang line (`#!/data/data/com.termux/files/usr/bin/env python`), and concise docstrings or comments only where they add value.

## Purpose
The script scans text files for language content and reports the detected natural language of each file's text. It uses three detectors in combination (gcld3, pycld2, and langdetect) and produces per-file results, optionally aggregated into a single JSON output. It is designed to run on Android under Termux, so it should avoid dependencies that are unavailable there and tolerate limited resources.

## Dependencies
- Standard library only beyond the following third-party packages: `gcld3`, `pycld2`, and `langdetect`.
- A helper module named `dh` providing an `is_binary(path)` function that returns True when a file appears to be binary. Import it as-is; do not reimplement it.
- Standard modules to use: `argparse`, `json`, `multiprocessing`, `sys`, `threading`, `pathlib`, and `typing` (`Any`, plus `Iterable`/`Iterator` imported only under `TYPE_CHECKING`).

## Module-level setup
- Seed langdetect deterministically by setting `DetectorFactory.seed = 0` at import time.
- Create two module-level `threading.Lock` objects: one guarding console printing, one guarding the shared results list.
- Maintain a module-level list of result dictionaries typed `list[dict[str, Any]]`.
- Create one module-level gcld3 detector: `NNetLanguageIdentifier` with `min_num_bytes=0` and `max_num_bytes=1000`.

## Functions to implement

### `iter_files(paths: Iterable[Path]) -> Iterator[Path]`
- For each input path, expand the user home directory (`~`).
- Skip symbolic links entirely (both for top-level inputs and during recursion).
- If the path is a regular file and `is_binary` returns False, yield it.
- If the path is a directory, recursively walk all entries with `rglob("*")`, skip symlinks, and yield regular files that are not binary.
- Silently ignore paths that are neither files nor directories (e.g., missing paths).

### `read_text_lines(path: Path) -> Iterator[str]`
- Try decoding the file as UTF-8 first, then fall back to Latin-1, using strict error handling.
- Stream lines, stripping only the trailing newline (`\\n`) from each line.
- If a `UnicodeDecodeError` occurs, move on to the next encoding. Once a encoding succeeds fully, return.
- For any other exception, stop trying further encodings and return without yielding anything further for that file (fail quietly for that file).
- If both encodings fail, yield nothing.

### Detection helpers
Implement helper functions that each take the full text (or a sample of it) and return a detected language code or a structured result:
- **gcld3 detection**: use the module-level detector's language prediction; return the language code and its probability/reliability as reported by gcld3, handling empty or whitespace-only input by returning no result.
- **pycld2 detection**: call `cld2.detect` with the text, requesting best-effort detection; handle `cld2.error` (raised for unsupported or invalid input, including text too long or with bad encoding) by returning no result, and catch that the input may need to be sanitized (e.g., remove non-printable characters) before retrying once.
- **langdetect detection**: call `detect_langs` on the text, catching exceptions (such as the library's language-detection failure for too-short or featureless text) and returning no result in that case. Return the top candidate and its probability.

Each helper should return `None` (or an empty/absent result) rather than raising for unusable input.

### Result aggregation
- Combine the three detector outputs for a file into a single result record containing: the file path (as a string), the per-detector language codes and confidences, and a consensus language chosen by majority agreement among detectors that returned a result (ties broken by the highest reported confidence). If no detector produced a result, the consensus is null.
- Append each record to the shared results list while holding the results lock.

### Per-file processing
- For one file, read its lines via `read_text_lines`, join them into a text sample, and limit the sample size (for example, the first few thousand characters) to keep detection fast.
- Skip files that contain no non-whitespace text.
- Run the three detectors on the sample and build a result record.
- Wrap processing in error handling so that a failure on one file is reported (via the print lock, to stderr) and does not stop processing of other files.

### Printing
- Provide a thread-safe print helper that acquires the print lock before writing to stdout or stderr.
- Print one concise line per file showing the path and the consensus language (or a "unknown" marker when none was detected).

### `main()`
Use `argparse` with:
- A required-or-optional positional argument accepting one or more paths (files or directories); default to the current directory if none given.
- `-j` / `--jobs`: number of worker processes (default: CPU count via `multiprocessing.cpu_count()`), where 1 means run sequentially in the main process.
- `-o` / `--output`: optional path to write the aggregated results as JSON (UTF-8, pretty-printed with an indent of 2 and `ensure_ascii=False`).
- `--min-len`: optional minimum number of characters a file's text must have to be analyzed (default small, e.g. 20); shorter files are skipped.
- A `--quiet` flag that suppresses per-file console lines (results still go to the output file if given).

Execution flow:
1. Parse arguments and resolve the input paths.
2. Collect candidate files with `iter_files`.
3. Process files either sequentially or with a `multiprocessing.Pool` of the requested size, using `imap_unordered` so output streams as work completes. Ensure the pool is properly closed and joined.
4. After processing, if an output path was given, write the accumulated results as JSON, creating parent directories as needed.
5. Print a brief summary to stdout: total files scanned, files analyzed, files skipped (binary, too short, or empty), and errors encountered.
6. Return exit code 0 on normal completion; return a non-zero code (e.g., 1) if no files were found or an unrecoverable error occurred. Use `sys.exit(main())` under the usual `if __name__ == "__main__":` guard.

## Error handling and edge cases to honor
- Handle symlinks, missing paths, binary files, unreadable files, and encoding failures gracefully without aborting the run.
- Handle empty files, whitespace-only files, and files shorter than the minimum length by skipping them.
- Handle detector failures independently; one detector failing must not prevent the others from contributing.
- Guard the shared results list and console output with their locks when used across threads.
- Do not let worker processes crash the whole run; catch exceptions per file.
- Keep all output deterministic given the same inputs (the langdetect seed ensures this).

## Style requirements
- Use type hints on all functions and module-level variables where helpful.
- Use `Path` objects rather than raw strings for filesystem work.
- Keep functions focused and short; prefer clear names over comments.
- Output the complete script as a single file with no external configuration.

---"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

import gcld3
import pycld2 as cld2
from dh import is_binary
from langdetect import DetectorFactory, detect_langs

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
DetectorFactory.seed = 0
_print_lock = threading.Lock()
_results_lock = threading.Lock()
_results: list[dict[str, Any]] = []
_gcld3_detector = gcld3.NNetLanguageIdentifier(min_num_bytes=0, max_num_bytes=1000)


def iter_files(paths: Iterable[Path]) -> Iterator[Path]:
    for p in paths:
        p = p.expanduser()
        if p.is_symlink():
            continue
        if p.is_file():
            if not is_binary(p):
                yield p
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_symlink():
                    continue
                if f.is_file() and not is_binary(f):
                    yield f


def read_text_lines(path: Path) -> Iterator[str]:
    for enc in ("utf-8", "latin-1"):
        try:
            with path.open("r", encoding=enc, errors="strict") as fh:
                for ln in fh:
                    yield ln.rstrip("\n")
            return
        except UnicodeDecodeError:
            continue
        except Exception:
            return


def detect_gcld3(text: str) -> str | None:
    try:
        res = _gcld3_detector.FindLanguage(text[:1000])
        return getattr(res, "language", None)
    except Exception:
        return None


def detect_pycld2(text: str) -> str | None:
    try:
        _, _, details = cld2.detect(text)
        return details[0][1]
    except Exception:
        return None


def detect_langdetect(text: str) -> str | None:
    try:
        langs = detect_langs(text)
        if langs:
            return langs[0].lang
    except Exception:
        return None


def normalize(code: str | None) -> str:
    return "unknown" if not code else code.lower()


def combine_votes(g3: str | None, p2: str | None, ld: str | None) -> dict[str, Any]:
    votes = {
        "gcld3": normalize(g3),
        "pycld2": normalize(p2),
        "langdetect": normalize(ld),
    }
    print(votes)

    def is_en(v: str) -> bool:
        return v.startswith("en")

    non_en_votes = sum(1 for v in votes.values() if v != "unknown" and not is_en(v))
    known_votes = sum(1 for v in votes.values() if v != "unknown")
    if non_en_votes >= 2:
        decision = True
    elif non_en_votes == 1 and known_votes == 1:
        if (votes["gcld3"] != "unknown" and not is_en(votes["gcld3"])) or (
            votes["pycld2"] != "unknown" and not is_en(votes["pycld2"])
        ):
            decision = True
        else:
            decision = False
    else:
        decision = False
    return {"votes": votes, "non_english": decision}


def detect_line(path: Path, lineno: int, line: str, max_len: int) -> dict[str, Any] | None:
    if not line.strip():
        return None
    text = line if len(line) <= max_len else line[:max_len] + "…"
    g3 = detect_gcld3(text)
    p2 = detect_pycld2(text)
    ld = detect_langdetect(text)
    combined = combine_votes(g3, p2, ld)
    if combined["non_english"]:
        rec = {
            "file": str(path),
            "line_no": lineno,
            "text": text,
            "detectors": combined["votes"],
            "non_english": True,
        }
        return rec
    return None


def process_file_sequential(path: Path, max_len: int) -> list[dict[str, Any]]:
    local: list[dict[str, Any]] = []
    for lineno, raw in enumerate(read_text_lines(path), start=1):
        rec = detect_line(path, lineno, raw, max_len)
        if rec:
            with _print_lock:
                print(f"{rec['file']}:{rec['line_no']}: {rec['text']}")
                print(f"  detectors: {rec['detectors']}")
            local.append(rec)
    return local


def process_file_per_line_parallel(path: Path, max_len: int, workers: int) -> list[dict[str, Any]]:
    local: list[dict[str, Any]] = []
    lines = list(read_text_lines(path))
    if not lines:
        return local
    with mp.Pool(processes=8) as ex:
        futures = {
            ex.apply_async(
                detect_line,
                args=(
                    path,
                    lineno,
                    line,
                    max_len,
                ),
            ): lineno
            for lineno, line in enumerate(lines, start=1)
            if line.strip()
        }
        for fut in as_completed(futures):
            try:
                rec = fut.get()
                if rec:
                    with _print_lock:
                        print(f"{rec['file']}:{rec['line_no']}: {rec['text']}")
                        print(f"  detectors: {rec['detectors']}")
                    local.append(rec)
            except Exception as e:
                with _print_lock:
                    print(f"Error in per-line task for {path}: {e}", file=sys.stderr)
    return local


def run_per_file(files: list[Path], workers: int, max_len: int):
    with mp.Pool(processes=8) as ex:
        futures = {
            ex.apply_async(
                process_file_sequential,
                args=(
                    f,
                    max_len,
                ),
            ): f
            for f in files
        }
        for fut in as_completed(futures):
            try:
                res = fut.get()
                if res:
                    with _results_lock:
                        _results.extend(res)
            except Exception as e:
                print(f"Error processing {futures[fut]}: {e}", file=sys.stderr)


def run_per_line(files: list[Path], workers: int, max_len: int):
    with mp.Pool(processes=8) as ex_files:
        futures = {
            ex_files.apply_async(
                process_file_per_line_parallel,
                args=(
                    f,
                    max_len,
                    workers,
                ),
            ): f
            for f in files
        }
        for fut in as_completed(futures):
            try:
                res = fut.get()
                if res:
                    with _results_lock:
                        _results.extend(res)
            except Exception as e:
                print(f"Error in per-line mode for {futures[fut]}: {e}", file=sys.stderr)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Detect non-English lines in text files.")
    parser.add_argument("paths", default=".", nargs="*", help="Files or directories (default: .)")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Worker threads.")
    parser.add_argument("--out", "-o", default="noneng.json", help="Output JSON file.")
    parser.add_argument("--max-line-length", type=int, default=2000, help="Max chars per line.")
    parser.add_argument(
        "--parallel-mode",
        choices=["file", "line"],
        default="file",
        help="Parallelism mode: file (default) or line (inside each file).",
    )
    args = parser.parse_args(argv)
    input_paths = [Path(p) for p in args.paths] if args.paths else [Path()]
    files = list(iter_files(input_paths))
    if not files:
        print("No suitable text files found.", file=sys.stderr)
        return 1
    if args.parallel_mode == "file":
        run_per_file(files, args.workers, args.max_line_length)
    else:
        run_per_line(files, args.workers, args.max_line_length)
    with Path(args.out).open("w", encoding="utf-8") as fh:
        json.dump(_results, fh, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(_results)} non-English lines to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
