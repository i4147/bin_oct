#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python terminal PDF text pager for Termux, covering purpose, inputs/outputs, dependencies, logic, error handling, edge cases, and usage. Only the prompt is output.

Build a single-file Python 3 command-line tool, intended to run under Termux on Android (shebang pointing to the Termux Python path), that displays the extracted text of one or more PDF files in a scrollable, paged terminal viewer.

**Purpose**
The script accepts one or more PDF file paths, extracts text from every page, splits that text into terminal-sized screens, and lets the user page through them interactively with single-keypress navigation. It should also support a non-interactive mode for dumping or inspecting the content.

**Command-line interface**
Use argparse with the description "Display extracted PDF text in a scrollable terminal pager." Accept:
- One or more positional `paths` arguments naming PDF files.
- Options controlling the backend used for extraction, page range selection, the number of worker processes (default 8), and any flag that forces non-interactive output to stdout.
- Validate that each path exists and has a `.pdf` suffix (case-insensitive); report clear errors for missing or non-PDF inputs and exit with a non-zero status when no valid input remains.
- Parse arguments from a passed-in argument sequence so the entry point can be called with custom argv for testing.

**Dependencies**
- Standard library only, apart from `loguru` for logging (configure a sensible default sink and level; log warnings for skipped pages or backend fallbacks, errors for failures).
- Use `termios` and `tty` for raw single-character keyboard input on a Unix TTY; restore terminal attributes in a `finally` block no matter how the program exits.
- Use `subprocess` and `shutil` to invoke external PDF text tools (for example `pdftotext` from poppler, or `pdfinfo` for page counts) when they are available on `PATH`; detect availability with `shutil.which`. Support at least one backend, and fall back to an alternative or a pure-Python approach if the preferred tool is missing; if no backend exists, print a helpful installation hint (for Termux: `pkg install poppler`) and exit.
- Use `tempfile` for any intermediate files, cleaning them up afterwards.
- Use `concurrent.futures.ProcessPoolExecutor` to extract pages in parallel across the worker count, preserving original page order in the output regardless of completion order.
- Use `textwrap` to wrap long lines to the terminal width before splitting into screens.
- Use `from __future__ import annotations` and type hints throughout; `typing` helpers such as `Iterable`, `Iterator`, `Sequence`, and `TYPE_CHECKING` may be used.

**Data structures**
Use frozen dataclasses with `slots=True`:
- `InputFile`: path (Path), backend (str), page_count (int).
- `ScreenPart`: page_number, part_number, part_count, text. A page whose wrapped text exceeds the screen height is split into multiple parts.

**Core behavior**
1. For each input PDF, determine the page count and choose a backend; skip and log a warning for files that cannot be read or are encrypted without a usable password.
2. Extract text per page (in parallel), normalize line endings, strip trailing whitespace, and collapse excessive blank lines. Treat pages with no extractable text (e.g., scanned images) by showing a placeholder message rather than crashing.
3. Wrap text to the current terminal width (obtained via `shutil.get_terminal_size` with a fallback of 80×24 when not a TTY). Split each page into parts that fit the usable height, reserving rows for a header line and separator.
4. Build a flat list of screens across all files and pages. Each screen is rendered by:
   - Clearing the screen with an ANSI escape sequence (or `clear`).
   - Writing a header of the form "Page N | Part X/Y | Screen A/B" followed by a separator line whose length is the smaller of the header length and terminal width.
   - Writing the screen body text followed by a newline, then flushing stdout.
5. Interactive navigation via raw key reads:
   - Space / `f` / Down / `j` / Enter: next screen.
   - `b` / Up / `k`: previous screen.
   - `g` / `G`: first / last screen.
   - Number entry for jumping to a page, if feasible.
   - `q` or Ctrl-C: quit cleanly with exit status 0 and restore the terminal.
   - Handle arrow keys (multi-byte escape sequences) correctly.
   - Re-render on terminal resize where practical, by re-checking terminal size before each draw.
6. Non-interactive mode (when stdout is not a TTY or a flag forces it): write all screens' text sequentially without clearing the screen or waiting for keys.

**Error handling and edge cases**
- Missing files, non-PDF files, unreadable or corrupt PDFs, password-protected PDFs, and empty documents must each produce a clear message via loguru without a traceback to the user.
- Handle `KeyboardInterrupt` gracefully everywhere, including during parallel extraction (shut down the process pool).
- Handle broken pipes when stdout is closed early (e.g., piped to `head`).
- If a subprocess call fails or times out, log the error and treat that page as empty rather than aborting the whole run.
- Very narrow terminals (width under ~20) and very short terminals (height under ~5) should still function without crashing; clamp minimums.
- Very large PDFs: avoid holding redundant copies of the full text; process page by page where possible.
- Non-UTF-8 extracted bytes should be decoded with `errors="replace"`.
- Ensure the terminal is restored to canonical mode even when an exception occurs.

**Execution details**
- The file begins with an executable shebang for the Termux Python interpreter and includes a `main()` function invoked under `if __name__ == "__main__":`, which exits with `sys.exit(main())` returning an integer status code.
- Keep the code modular: separate helpers for argument parsing, backend detection, page extraction, text wrapping and pagination, screen rendering, key reading, and the navigation loop.
- Use `WORKERS` and `PDF_SUFFIXES` as module-level constants (`PDF_SUFFIXES` a frozenset of `".pdf"`).
- Write concise docstrings and comments only where logic is non-obvious; match a clean, typed, idiomatic style.

**Usage examples to support**
- `pager.py book.pdf` — open an interactive pager for one file.
- `pager.py a.pdf b.pdf --pages 1-10` — several files with a page range (if the option is implemented).
- `pager.py report.pdf | less` — non-interactive output when piped.

Deliver the complete script as a single file.
---"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import termios
import textwrap
import tty
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Iterator, Sequence

from loguru import logger

if TYPE_CHECKING:
    import os
WORKERS: int = 8
PDF_SUFFIXES: frozenset[str] = frozenset({".pdf"})


@dataclass(frozen=True, slots=True)
class InputFile:
    path: Path
    backend: str
    page_count: int


@dataclass(frozen=True, slots=True)
class ScreenPart:
    page_number: int
    part_number: int
    part_count: int
    text: str


def render_screen(part: ScreenPart, screen_index: int, screen_count: int) -> None:
    clear_screen()
    title: str = (
        f"Page {part.page_number} | Part {part.part_number}/{part.part_count} "
        f"| Screen {screen_index + 1}/{screen_count}"
    )
    sys.stdout.write(f"{title}\n{'─' * min(len(title), terminal_size()[0])}\n")
    sys.stdout.write(part.text)
    sys.stdout.write("\n")
    sys.stdout.flush()


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Display extracted PDF text in a scrollable terminal pager."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="PDF files or directories. Defaults to the current directory.",
    )
    parser.add_argument(
        "-b",
        "--backend",
        default="pdfminer",
        choices=("pdfminer", "pypdf", "pymupdf", "system", "auto"),
        help=(
            "Text extraction backend. The default is pdfminer. 'auto' tries Python libraries and then system OCR tools."
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=WORKERS,
        help=f"Number of extraction workers; default: {WORKERS}.",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Do not recursively search directories for PDF files.",
    )
    parser.add_argument(
        "--log-level",
        choices=("TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        default="WARNING",
        help="Loguru log level; default: WARNING.",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logger.remove()
    logger.add(sys.stderr, level=level, enqueue=False)


def unique_paths(paths: Iterable[Path]) -> Iterator[Path]:
    seen: set[Path] = set()
    for raw_path in paths:
        path: Path = raw_path.expanduser()
        if path.is_symlink():
            logger.debug("Skipping symlink: {}", path)
            continue
        if path.is_file():
            if path.suffix.lower() in PDF_SUFFIXES:
                resolved: Path = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield resolved
            continue
        if not path.is_dir():
            logger.warning("Ignoring missing or unsupported path: {}", path)
            continue
        iterator: Iterable[Path] = path.rglob("*")
        for child in iterator:
            if child.is_symlink():
                continue
            if child.is_file() and child.suffix.lower() in PDF_SUFFIXES:
                resolved = child.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield resolved


def find_pdf_files(paths: Sequence[Path], recursive: bool) -> list[Path]:
    if not paths:
        paths = (Path.cwd(),)
    if not recursive:
        result: list[Path] = []
        seen: set[Path] = set()
        for raw_path in paths:
            path: Path = raw_path.expanduser()
            if path.is_symlink():
                continue
            if path.is_file() and path.suffix.lower() in PDF_SUFFIXES:
                resolved: Path = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    result.append(resolved)
                continue
            if path.is_dir():
                for child in path.iterdir():
                    if not child.is_symlink() and child.is_file() and child.suffix.lower() in PDF_SUFFIXES:
                        resolved = child.resolve()
                        if resolved not in seen:
                            seen.add(resolved)
                            result.append(resolved)
        return sorted(result)
    return sorted(unique_paths(paths))


def executable_exists(name: str) -> bool:
    return shutil.which(name) is not None


def importable(module_name: str) -> bool:
    try:
        __import__(module_name)
    except ImportError:
        return False
    return True


def usable_python_backends() -> list[str]:
    result: list[str] = []
    if importable("pdfminer"):
        result.append("pdfminer")
    if importable("pypdf"):
        result.append("pypdf")
    if importable("fitz"):
        result.append("pymupdf")
    return result


def usable_system_backend() -> bool:
    return executable_exists("gs") and executable_exists("tesseract")


def resolve_backend(requested: str) -> str:
    if requested == "auto":
        available: list[str] = usable_python_backends()
        if available:
            return available[0]
        if usable_system_backend():
            return "system"
        msg = (
            "No usable Python PDF library or system OCR tool was found. "
            "Install pdfminer.six, pypdf, or pymupdf; or install gs and tesseract."
        )
        raise RuntimeError(msg)
    if requested == "pdfminer" and importable("pdfminer"):
        return requested
    if requested == "pypdf" and importable("pypdf"):
        return requested
    if requested == "pymupdf" and importable("fitz"):
        return requested
    if requested == "system" and usable_system_backend():
        return requested
    if requested != "system" and usable_system_backend():
        logger.warning(
            "Requested backend '{}' is unavailable; using system OCR fallback.",
            requested,
        )
        return "system"
    msg = f"Backend '{requested}' is unavailable and no system OCR fallback exists."
    raise RuntimeError(msg)


def page_count_pdfminer(path: Path) -> int:
    from pdfminer.pdfpage import PDFPage

    with path.open("rb") as handle:
        count: int = sum(1 for _ in PDFPage.get_pages(handle))
    return count


def page_count_pypdf(path: Path) -> int:
    from pypdf import PdfReader

    reader: PdfReader = PdfReader(str(path), strict=False)
    return len(reader.pages)


def page_count_pymupdf(path: Path) -> int:
    import fitz

    document = fitz.open(str(path))
    try:
        return document.page_count
    finally:
        document.close()


def page_count_pdfinfo(path: Path) -> int:
    if not executable_exists("pdfinfo"):
        msg = "pdfinfo is required to count pages for system OCR."
        raise RuntimeError(msg)
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        ["pdfinfo", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in completed.stdout.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip().lower() == "pages":
            count: int = int(value.strip())
            if count > 0:
                return count
    msg = f"pdfinfo did not report a valid page count for {path}"
    raise RuntimeError(msg)


def get_page_count(path: Path, backend: str) -> int:
    if backend == "pdfminer":
        return page_count_pdfminer(path)
    if backend == "pypdf":
        return page_count_pypdf(path)
    if backend == "pymupdf":
        return page_count_pymupdf(path)
    if backend == "system":
        return page_count_pdfinfo(path)
    msg = f"Unknown backend: {backend}"
    raise RuntimeError(msg)


def extract_pdfminer_page(path: Path, page_number: int) -> str:
    from io import StringIO

    from pdfminer.high_level import extract_text_to_fp
    from pdfminer.layout import LAParams
    from pdfminer.pdfpage import PDFPage

    output: StringIO = StringIO()
    with path.open("rb") as handle:
        pages = PDFPage.get_pages(
            handle,
            pagenos={page_number - 1},
            check_extractable=False,
        )
        extract_text_to_fp(
            handle,
            output,
            laparams=LAParams(),
            page_numbers=[page_number - 1],
            codec="utf-8",
        )
    return output.getvalue()


def extract_pypdf_page(path: Path, page_number: int) -> str:
    from pypdf import PdfReader

    reader: PdfReader = PdfReader(str(path), strict=False)
    page = reader.pages[page_number - 1]
    return page.extract_text() or ""


def extract_pymupdf_page(path: Path, page_number: int) -> str:
    import fitz

    document = fitz.open(str(path))
    try:
        page = document.load_page(page_number - 1)
        return page.get_text("text") or ""
    finally:
        document.close()


def extract_system_page(path: Path, page_number: int) -> str:
    required_tools: tuple[str, ...] = ("gs", "tesseract")
    missing: list[str] = [tool for tool in required_tools if not executable_exists(tool)]
    if missing:
        msg = f"System OCR backend requires missing tools: {', '.join(missing)}"
        raise RuntimeError(msg)
    with tempfile.TemporaryDirectory(prefix="pdf-screen-") as temporary_directory:
        image_path: Path = Path(temporary_directory) / "page.png"
        gs_command: list[str] = [
            "gs",
            "-q",
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pnggray",
            "-r200",
            f"-dFirstPage={page_number}",
            f"-dLastPage={page_number}",
            f"-sOutputFile={image_path}",
            str(path),
        ]
        subprocess.run(
            gs_command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        tesseract_command: list[str] = [
            "tesseract",
            str(image_path),
            "stdout",
            "--dpi",
            "200",
            "--psm",
            "3",
        ]
        completed: subprocess.CompletedProcess[str] = subprocess.run(
            tesseract_command,
            check=True,
            capture_output=True,
            text=True,
            errors="replace",
        )
    return completed.stdout


def extract_page(task: tuple[str, int, str]) -> str:
    path_string, page_number, backend = task
    path: Path = Path(path_string)
    if backend == "pdfminer":
        return extract_pdfminer_page(path, page_number)
    if backend == "pypdf":
        return extract_pypdf_page(path, page_number)
    if backend == "pymupdf":
        return extract_pymupdf_page(path, page_number)
    if backend == "system":
        return extract_system_page(path, page_number)
    msg = f"Unknown backend: {backend}"
    raise RuntimeError(msg)


def terminal_size() -> tuple[int, int]:
    size: os.terminal_size = shutil.get_terminal_size((80, 24))
    columns: int = max(20, size.columns)
    rows: int = max(5, size.lines)
    return columns, rows


def wrap_text(value: str, width: int) -> list[str]:
    normalized: str = value.replace("\r\n", "\n").replace("\r", "\n")
    result: list[str] = []
    for line in normalized.split("\n"):
        if not line:
            result.append("")
            continue
        result.extend(
            textwrap.wrap(
                line,
                width=width,
                replace_whitespace=False,
                drop_whitespace=False,
                break_long_words=True,
                break_on_hyphens=False,
            )
            or [""]
        )
    while result and result[-1] == "":
        result.pop()
    return result or [""]


def split_into_screen_parts(
    page_number: int,
    text: str,
    columns: int,
    rows: int,
) -> list[ScreenPart]:
    header_lines: int = 2
    usable_lines: int = max(1, rows - header_lines)
    wrapped: list[str] = wrap_text(text, columns)
    parts: list[ScreenPart] = [
        ScreenPart(page_number, index + 1, 0, "\n".join(chunk))
        for index, start in enumerate(range(0, len(wrapped), usable_lines))
        for chunk in [wrapped[start : start + usable_lines]]
    ]
    part_count: int = len(parts)
    return [
        ScreenPart(
            page_number=part.page_number,
            part_number=part.part_number,
            part_count=part_count,
            text=part.text,
        )
        for part in parts
    ]


def make_screen_parts(page_text: Sequence[str]) -> list[ScreenPart]:
    columns, rows = terminal_size()
    result: list[ScreenPart] = []
    for page_number, text in enumerate(page_text, start=1):
        result.extend(
            split_into_screen_parts(
                page_number=page_number,
                text=text,
                columns=columns,
                rows=rows,
            )
        )
    return result


def clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")


def read_key() -> str:
    character: str = sys.stdin.read(1)
    if character != "\033":
        return character
    sequence: str = character + sys.stdin.read(1)
    if sequence == "\033[":
        sequence += sys.stdin.read(1)
        if sequence.endswith("5"):
            sequence += sys.stdin.read(1)
            return "pageup"
        if sequence.endswith("6"):
            sequence += sys.stdin.read(1)
            return "pagedown"
        if sequence.endswith("A"):
            return "up"
        if sequence.endswith("B"):
            return "down"
        if sequence.endswith("H"):
            return "home"
        if sequence.endswith("F"):
            return "end"
    return "escape"


def pager(parts: Sequence[ScreenPart]) -> None:
    if not parts:
        logger.warning("No text was extracted.")
        return
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        for part in parts:
            print(f"\n=== Page {part.page_number} ===")
            print(part.text)
        return
    file_descriptor: int = sys.stdin.fileno()
    original_settings = termios.tcgetattr(file_descriptor)
    try:
        tty.setcbreak(file_descriptor)
        index: int = 0
        while True:
            render_screen(parts[index], index, len(parts))
            key: str = read_key().lower()
            if key in {"q", "\x03"}:
                break
            if key in {"pagedown", "down", " "}:
                index = min(index + 1, len(parts) - 1)
            elif key in {"pageup", "up", "b"}:
                index = max(index - 1, 0)
            elif key == "home":
                index = 0
            elif key == "end":
                index = len(parts) - 1
    finally:
        termios.tcsetattr(file_descriptor, termios.TCSADRAIN, original_settings)
        clear_screen()


def extract_file(path: Path, backend: str, workers: int) -> list[str]:
    page_count: int = get_page_count(path, backend)
    logger.info(
        "Extracting {} pages from {} with {}",
        page_count,
        path,
        backend,
    )
    tasks: list[tuple[str, int, str]] = [(str(path), page_number, backend) for page_number in range(1, page_count + 1)]
    with ProcessPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(extract_page, tasks, chunksize=1))


def process_file(path: Path, requested_backend: str, workers: int) -> None:
    backend: str = resolve_backend(requested_backend)
    logger.info("Opening {} using backend {}", path, backend)
    try:
        page_text: list[str] = extract_file(path, backend, workers)
    except Exception:
        if requested_backend != "system" and usable_system_backend():
            logger.exception(
                "Backend '{}' failed for {}; retrying with system OCR.",
                backend,
                path,
            )
            page_text = extract_file(path, "system", workers)
        else:
            raise
    if len(page_text) == 0:
        msg = f"No pages found in PDF: {path}"
        raise RuntimeError(msg)
    print(f"\n{path}\n")
    pager(make_screen_parts(page_text))


def main(argv: Sequence[str]) -> int:
    arguments: argparse.Namespace = parse_arguments(argv)
    configure_logging(arguments.log_level)
    if arguments.workers < 1:
        msg = "--workers must be at least 1"
        raise ValueError(msg)
    paths: list[Path] = find_pdf_files(
        arguments.paths,
        recursive=not arguments.no_recursive,
    )
    if not paths:
        msg = "No PDF files were found."
        raise FileNotFoundError(msg)
    for path in paths:
        process_file(
            path=path,
            requested_backend=arguments.backend,
            workers=arguments.workers,
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        logger.error("Interrupted.")
        raise SystemExit(130)
    except Exception:
        logger.exception("Fatal error.")
        raise SystemExit(1)
