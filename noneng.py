#!/data/data/com.termux/files/usr/bin/env python
"""Write a prompt that recreates a Python CLI tool that scans text files for non-English content, using pluggable language-detection backends, parallel processing, and sanitized output. Describe purpose, inputs/outputs, dependencies, logic, error handling, and edge cases without code.

Create a self-contained prompt for an AI coding agent to build a Python 3 command-line utility named for detecting non-English text in text-based files. Target environment: Termux on Android (shebang uses the Termux Python path), so the script must run under standard CPython with the `from __future__ import annotations` import and no platform-specific APIs.

**Purpose**
The tool recursively scans files and directories given on the command line and reports which files contain text written in languages other than English. It should be usable as a quick auditing or linting utility for source trees, documentation, or data dumps.

**Command-line interface**
- Use `argparse` with the description "Detect non-English text in text-based files."
- Positional argument `paths`: zero or more paths, each converted to `pathlib.Path`. When none are given, default to the current directory.
- Option `-b` / `--backend`: one of `pycld2`, `gcld3`, `langdetect`, `lingua`, `fast_langdetect`, `fasttext`. Default `pycld2`. Help text: "Language-detection backend. Defaults to pycld2."
- Parse and return the namespace from a `parse_arguments` function.

**Constants to define at module level**
- Worker process count: 8.
- Read chunk size: 64 KiB.
- Detection sample size: 4000 characters.
- Minimum number of alphabetic letters required before attempting detection: 20.
- A module-level backend name string and a detector placeholder, both initialized empty/None, to be set once per worker process.
- A frozen set of directory names to skip during traversal: version-control folders (.git, .hg, .svn, .bzr), caches and tool folders (__pycache__, .mypy_cache, .pytest_cache, .ruff_cache, .tox), virtual environments (.venv, venv, env, .env), node_modules, and IDE folders (.idea, .vscode).

**Data model**
A frozen dataclass `ScanResult` with fields: `path` (Path), `found` (bool, whether non-English text was detected), `languages` (tuple of language code strings), and `error` (optional string).

**Core behavior**
1. Expand the input paths: files are scanned directly; directories are walked recursively, skipping any directory whose name is in the skip set. Ignore symlinks or handle them safely to avoid cycles.
2. Filter to text-based files. Detect binary files (e.g., presence of null bytes or failed decoding) and skip them. Read files in fixed-size chunks.
3. Decode content incrementally using an incremental UTF-8 decoder so multi-byte characters split across chunk boundaries are handled correctly. Tolerate invalid bytes gracefully (replace or ignore) rather than crashing.
4. Take up to the detection sample size of decoded text. If it contains fewer than the minimum number of alphabetic letters, report it as not containing non-English text without invoking the detector.
5. Invoke the selected backend's detector on the sample. Map results to language codes. A file is flagged `found` when any detected language is not English (code `en`). Normalize codes to lowercase and ignore unreliable or unknown results.
6. Process files in parallel using a process pool with 8 workers. Each worker initializes its backend once (via a pool initializer that sets the module-level backend name and loads the detector), so the detector is not reloaded per file.
7. Lazily import the backend library only when selected. Backends and their pip packages: pycld2 (`pycld2`), gcld3 (`gcld3`), langdetect (`langdetect`), lingua (`lingua-language-detector`), fast_langdetect (`fast-langdetect`), fasttext (`fasttext` plus a downloaded language-ID model such as `lid.176.ftz`). If the required package is missing, raise a clear error explaining which package to install.

**Output**
- Use `loguru`'s `logger` for all output and diagnostics (not bare print for logs).
- For each file flagged as containing non-English text, log the path and the detected languages.
- Log per-file errors (unreadable files, permission errors, decode problems) as warnings or errors without aborting the whole run.
- At the end, log a summary: total files scanned and count of files with non-English text.
- Exit with status 0 when the scan completes; use a non-zero status for fatal configuration errors such as an unavailable backend.

**Error handling and edge cases**
- Nonexistent input paths: log an error and continue with the remaining paths.
- Empty files, whitespace-only files, and files with fewer than 20 letters: skip detection, not flagged.
- Very large files: never load the whole file; only read up to the chunk logic and the 4000-character sample.
- Keyboard interrupt: shut down the pool cleanly.
- Worker exceptions: catch per-file so one failure does not stop others.
- Keep the script importable: put execution under a `main` guard, and use `multiprocessing` safe patterns (a top-level worker function and picklable arguments).

**Execution**
Run with `python <script> [paths...] [-b BACKEND]`. Make the script executable with the Termux Python shebang line. Ensure the code is single-file, uses type hints with postponed annotations, and follows standard PEP 8 style with clear docstrings on public functions.
---"""

from __future__ import annotations

import argparse
import codecs
import multiprocessing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

from loguru import logger

WORKERS = 8
CHUNK_SIZE = 64 * 1024
DETECTION_SIZE = 4000
MIN_LETTERS = 20
_BACKEND: str = ""
_DETECTOR: Any = None
SKIP_DIRS = frozenset({
    ".git",
    ".hg",
    ".svn",
    ".bzr",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "node_modules",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
})


@dataclass(frozen=True)
class ScanResult:
    path: Path
    found: bool
    languages: tuple[str, ...]
    error: str | None


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect non-English text in text-based files.")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or directories to scan. Defaults to the current directory.",
    )
    parser.add_argument(
        "-b",
        "--backend",
        choices=(
            "pycld2",
            "gcld3",
            "langdetect",
            "lingua",
            "fast_langdetect",
            "fasttext",
        ),
        default="pycld2",
        help="Language-detection backend. Defaults to pycld2.",
    )
    return parser.parse_args()


def create_detector(backend: str) -> Any:
    if backend == "pycld2":
        import pycld2

        return pycld2
    if backend == "gcld3":
        import gcld3

        return gcld3.NNetLanguageIdentifier(
            min_num_bytes=0,
            max_num_bytes=DETECTION_SIZE,
        )
    if backend == "langdetect":
        from langdetect import DetectorFactory

        DetectorFactory.seed = 0
        return DetectorFactory
    if backend == "lingua":
        from lingua import LanguageDetectorBuilder

        return LanguageDetectorBuilder.from_all_languages().build()
    if backend == "fast_langdetect":
        from fast_langdetect import detect

        return detect
    if backend == "fasttext":
        import fasttext

        model_path_text = __import__("os").environ.get("FASTTEXT_MODEL")
        if not model_path_text:
            msg = (
                "The fasttext backend requires FASTTEXT_MODEL to point to a "
                "valid fastText language-identification model."
            )
            raise RuntimeError(msg)
        model_path = Path(model_path_text).expanduser()
        if not model_path.is_file():
            msg = f"FASTTEXT_MODEL does not point to a readable file: {model_path}"
            raise RuntimeError(msg)
        return fasttext.load_model(str(model_path))
    msg = f"Unsupported backend: {backend}"
    raise RuntimeError(msg)


def validate_backend(backend: str) -> None:
    create_detector(backend)
    logger.info("Language backend validated: {}", backend)


def initialize_worker(backend: str) -> None:
    global _BACKEND, _DETECTOR
    _BACKEND = backend
    _DETECTOR = create_detector(backend)


def detect_language(text: str) -> str:
    if _BACKEND == "pycld2":
        _, _, details = _DETECTOR.detect(text, bestEffort=True)
        if not details:
            return "unknown"
        return str(details[0][1]).lower()
    if _BACKEND == "gcld3":
        result = _DETECTOR.FindLanguage(text)
        return str(result.language).lower()
    if _BACKEND == "langdetect":
        from langdetect import detect

        return str(detect(text)).lower()
    if _BACKEND == "lingua":
        language = _DETECTOR.detect_language_of(text)
        if language is None:
            return "unknown"
        return str(language.name).lower()
    if _BACKEND == "fast_langdetect":
        result = _DETECTOR(text)
        if isinstance(result, dict):
            language = result.get("lang") or result.get("language")
            return str(language or "unknown").lower()
        return str(result).lower()
    if _BACKEND == "fasttext":
        labels, _ = _DETECTOR.predict(text.replace("\n", " "), k=1)
        if not labels:
            return "unknown"
        return str(labels[0]).removeprefix("__label__").lower()
    msg = f"Worker backend is not initialized: {_BACKEND}"
    raise RuntimeError(msg)


def is_english(language: str) -> bool:
    normalized = language.strip().lower()
    return normalized in {"en", "eng", "english"} or normalized.startswith("en_")


def is_usable_text(text: str) -> bool:
    if not text:
        return False
    letters = sum(character.isalpha() for character in text)
    if letters < MIN_LETTERS:
        return False
    printable = sum(character.isprintable() or character in "\n\r\t" for character in text)
    return printable / len(text) >= 0.85


def text_samples(path: Path) -> Iterator[str]:
    try:
        with path.open("rb") as handle:
            first_chunk = handle.read(CHUNK_SIZE)
            if not first_chunk:
                return
            if first_chunk.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
                encoding = "utf-16"
            elif first_chunk.startswith(codecs.BOM_UTF8):
                encoding = "utf-8-sig"
            else:
                if b"\x00" in first_chunk:
                    return
                encoding = "utf-8"
            decoder = codecs.getincrementaldecoder(encoding)(errors="replace")
            pending = ""
            for raw_chunk in (first_chunk, *iter(lambda: handle.read(CHUNK_SIZE), b"")):
                decoded = decoder.decode(raw_chunk)
                if not decoded:
                    continue
                pending += decoded
                while len(pending) >= DETECTION_SIZE:
                    sample = pending[:DETECTION_SIZE]
                    pending = pending[DETECTION_SIZE // 2 :]
                    if is_usable_text(sample):
                        yield sample
            pending += decoder.decode(b"", final=True)
            if is_usable_text(pending):
                yield pending[:DETECTION_SIZE]
    except UnicodeError:
        logger.error("Unable to decode file: {}", path)
    except OSError as error:
        msg = f"{path}: {error}"
        raise RuntimeError(msg) from error


def scan_file(path: Path) -> ScanResult:
    languages: set[str] = set()
    try:
        for sample in text_samples(path):
            try:
                language = detect_language(sample)
            except Exception as error:
                return ScanResult(
                    path=path,
                    found=False,
                    languages=(),
                    error=f"language detection failed: {error}",
                )
            if language != "unknown" and not is_english(language):
                languages.add(language)
        return ScanResult(
            path=path,
            found=bool(languages),
            languages=tuple(sorted(languages)),
            error=None,
        )
    except Exception as error:
        return ScanResult(
            path=path,
            found=False,
            languages=(),
            error=str(error),
        )


def collect_files(inputs: Iterable[Path]) -> list[Path]:
    files: dict[Path, Path] = {}
    pending: list[Path] = []
    for input_path in inputs:
        candidate = input_path.expanduser()
        if candidate.is_symlink():
            continue
        if not candidate.exists():
            msg = f"Input path does not exist: {candidate}"
            raise FileNotFoundError(msg)
        if candidate.is_file():
            resolved = candidate.resolve()
            files.setdefault(resolved, resolved)
            continue
        if candidate.is_dir():
            pending.append(candidate)
            continue
    while pending:
        directory = pending.pop()
        if directory.is_symlink():
            continue
        try:
            entries = directory.iterdir()
        except OSError as error:
            logger.error("Unable to inspect directory {}: {}", directory, error)
            continue
        try:
            for child in entries:
                try:
                    if child.is_symlink():
                        continue
                    if child.is_dir():
                        if child.name in SKIP_DIRS:
                            continue
                        pending.append(child)
                        continue
                    if child.is_file():
                        resolved = child.resolve()
                        files.setdefault(resolved, resolved)
                except OSError as error:
                    logger.error("Unable to inspect {}: {}", child, error)
        except OSError as error:
            logger.error("Unable to enumerate directory {}: {}", directory, error)
    return list(files.values())


def display_path(path: Path, base: Path) -> Path:
    try:
        return path.relative_to(base)
    except ValueError:
        return path


def print_result(
    result: ScanResult,
    base: Path,
    matches: list[Path],
    failures: list[ScanResult],
) -> None:
    shown_path = display_path(result.path, base)
    if result.error is not None:
        failures.append(result)
        logger.error("{}: {}", shown_path, result.error)
        return
    if result.found:
        matches.append(shown_path)
        print(
            f"{shown_path}: non-English text detected ({', '.join(result.languages)})",
            flush=True,
        )
        logger.info("Non-English text found in {}", shown_path)


def print_worker_error(
    error: BaseException,
    failures: list[ScanResult],
) -> None:
    logger.error("Worker failure: {}", error)
    failures.append(
        ScanResult(
            path=Path("<worker>"),
            found=False,
            languages=(),
            error=str(error),
        )
    )


def ask_to_save_report(matches: list[Path], report_path: Path) -> bool:
    if not matches:
        logger.info("No non-English text was detected.")
        return False
    try:
        answer = input(f"Save the report to {report_path}? [y/N] ").strip().lower()
    except EOFError:
        logger.error("Unable to read report confirmation from standard input.")
        return False
    return answer in {"y", "yes"}


def save_report(matches: list[Path], report_path: Path) -> None:
    try:
        unique_matches = sorted({str(path) for path in matches})
        with report_path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(unique_matches))
            handle.write("\n")
        logger.info("Report saved to {}", report_path)
    except OSError as error:
        logger.error("Unable to save report {}: {}", report_path, error)
        raise


def main() -> int:
    arguments = parse_arguments()
    base = Path.cwd()
    try:
        validate_backend(arguments.backend)
        inputs = arguments.paths or [base]
        files = collect_files(inputs)
    except Exception as error:
        logger.error("Initialization failed: {}", error)
        return 1
    if not files:
        logger.warning("No files were found to scan.")
        return 0
    logger.info(
        "Scanning {} file(s) with {} worker(s) using {}",
        len(files),
        WORKERS,
        arguments.backend,
    )
    matches: list[Path] = []
    failures: list[ScanResult] = []
    pool = multiprocessing.Pool(
        processes=WORKERS,
        initializer=initialize_worker,
        initargs=(arguments.backend,),
    )
    try:
        for file_path in files:
            pool.apply_async(
                scan_file,
                (file_path,),
                callback=lambda result: print_result(
                    result,
                    base,
                    matches,
                    failures,
                ),
                error_callback=lambda error: print_worker_error(error, failures),
            )
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        logger.error("Interrupted by user; terminating workers.")
        pool.terminate()
        pool.join()
        return 130
    except Exception as error:
        logger.error("Scanning failed: {}", error)
        pool.terminate()
        pool.join()
        return 1
    report_path = base / "noneng.txt"
    try:
        if ask_to_save_report(matches, report_path):
            save_report(matches, report_path)
    except Exception:
        return 1
    if failures:
        logger.error("{} file(s) failed during scanning.", len(failures))
        return 1
    logger.info(
        "Scan complete: {} file(s) contained non-English text.",
        len(matches),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
