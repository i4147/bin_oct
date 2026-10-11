#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to recreate a Python command-line tool that splits PDF files page by page and extracts per-page text, using a multiprocessing pool with several dispatch strategies, loguru logging, and pypdf. Describe the purpose, CLI inputs and outputs, file naming scheme with zero-padding, the four pool methods (map, starmap, imap_unordered, apply_async), the fixed worker count of 8, the default output directory, the task and result type aliases, the Termux shebang, and the error handling and edge cases implied by the code (including single-page PDFs, empty pages, and output directory creation), without including any code.
[Tool: think]
  Params: {"content":"The user wants a prompt only, in English, no code snippets, no preamble. The script is partially shown (truncated in extract_text_by_page), so I should describe what is visible and note reasonable inferred behavior carefully, without overclaiming. I'll write the prompt directly."}
Create a Python command-line tool that splits PDF files into per-page PDFs and extracts text per page, with parallel processing. Requirements:

**Purpose**
Given one or more input PDF files, the tool produces one output file per page. Two operations are supported: splitting each page into its own standalone PDF, and extracting each page's text into its own text file. Work on multiple input files is distributed across a process pool.

**Environment and dependencies**
- Target Python 3, with a Termux-style shebang line pointing to the Termux Python binary.
- Use `from __future__ import annotations`.
- Dependencies: `pypdf` (use `PdfReader` and `PdfWriter`, with a `# type: ignore[import-untyped]` comment on the import) and `loguru` for logging. Use only the standard library otherwise (`argparse`, `multiprocessing.pool` for `Pool` and `AsyncResult`, `pathlib.Path`, `typing`).
- Guard type-only imports (such as `Sequence`) behind `TYPE_CHECKING`.

**Constants and type aliases**
- `POOL_WORKERS`: a Final integer constant set to 8.
- `POOL_METHODS`: a Final tuple of strings listing the dispatch strategies: `"map"`, `"starmap"`, `"imap_unordered"`, `"apply_async"`.
- `DEFAULT_OUTPUT_DIR`: a Final string set to `"output"`.
- `SplitTask`: a type alias for a tuple of (input path, output directory path, boolean flag).
- `SplitResult`: a type alias for a tuple of (input path, integer page count).

**Core functions**
1. `split_pdf_by_page(pdf_path, output_dir) -> int`
   - Read the PDF with `PdfReader`, take the file stem, and count pages.
   - Compute zero-padding width as the number of digits in the total page count.
   - For each page (1-based numbering), write a new single-page PDF using `PdfWriter` to `output_dir / f"{stem}_{page_number zero-padded}.pdf"`, opened in binary write mode.
   - Return the total page count.

2. `extract_text_by_page(pdf_path, output_dir) -> int`
   - Same reading, stem, page count, and padding logic as the split function.
   - For each page, extract its text and write it to a text file named with the same `{stem}_{padded number}` pattern (use a `.txt` extension), then return the total page count.
   - Implement the rest of this function's behavior consistently with the split function, including handling pages whose extracted text is empty or None (write an empty file rather than failing).

3. A worker dispatcher that receives a `SplitTask` and runs the selected operation (split or text extraction) based on the boolean flag, returning a `SplitResult`. This dispatcher is what is passed to the pool.

4. A `main`-style entry point built on `argparse` that:
   - Accepts one or more input PDF paths as positional arguments.
   - Accepts an optional output directory argument defaulting to `"output"`.
   - Accepts an option selecting the operation (split pages to PDFs versus extract text), and an option selecting the pool dispatch method from `POOL_METHODS`, defaulting to a sensible choice such as `"map"`.
   - Creates the output directory (including parents) if missing.
   - Builds a list of tasks, one per input file, and runs them through a `multiprocessing.pool.Pool` with `POOL_WORKERS` processes.
   - Dispatches using the chosen method: `map` and `starmap` return results directly, `imap_unordered` iterates results as they complete, and `apply_async` submits each task asynchronously and collects `AsyncResult` objects, calling `.get()` on each.
   - Logs progress and per-file results (input name and page count) with loguru, and logs errors without crashing the whole batch where practical.

**Behavior and edge cases**
- Validate that input paths exist and are PDF files; log and skip invalid entries with a clear message rather than aborting the batch.
- Handle a single-page PDF: padding width is 1 and the output is a single correctly named file.
- Handle an empty or zero-page PDF gracefully: produce no output files and report zero pages.
- Padding must scale with page count so filenames sort correctly (e.g., a 120-page document uses 3-digit numbers).
- Output filenames derive from the input file's stem, so inputs with the same stem may overwrite each other; mention this in the code comments or docs.
- Ensure file handles are closed by using context managers when writing outputs.
- Exit with a non-zero status if any task failed; exit zero otherwise.
- Use the `if __name__ == "__main__":` guard, which is required for multiprocessing to work safely.

**Code style**
Use type hints throughout, `Final` for constants, `Path` objects instead of raw strings for file operations, and concise docstrings. Keep the module importable without side effects.
---"""

from __future__ import annotations

import argparse
from multiprocessing.pool import AsyncResult, Pool
from pathlib import Path
from typing import TYPE_CHECKING, Final, TypeAlias

from loguru import logger
from pypdf import PdfReader, PdfWriter  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from collections.abc import Sequence
POOL_WORKERS: Final[int] = 8
POOL_METHODS: Final[tuple[str, ...]] = (
    "map",
    "starmap",
    "imap_unordered",
    "apply_async",
)
DEFAULT_OUTPUT_DIR: Final[str] = "output"
SplitTask: TypeAlias = tuple[Path, Path, bool]
SplitResult: TypeAlias = tuple[Path, int]


def split_pdf_by_page(pdf_path: Path, output_dir: Path) -> int:
    reader = PdfReader(pdf_path)
    stem = pdf_path.stem
    total_pages = len(reader.pages)
    padding = len(str(total_pages))
    for page_num, page in enumerate(reader.pages, 1):
        writer = PdfWriter()
        writer.add_page(page)
        padded_num = str(page_num).zfill(padding)
        output_path = output_dir / f"{stem}_{padded_num}.pdf"
        with output_path.open("wb") as f:
            writer.write(f)
    return total_pages


def extract_text_by_page(pdf_path: Path, output_dir: Path) -> int:
    reader = PdfReader(pdf_path)
    stem = pdf_path.stem
    total_pages = len(reader.pages)
    padding = len(str(total_pages))
    for page_num, page in enumerate(reader.pages, 1):
        padded_num = str(page_num).zfill(padding)
        output_path = output_dir / f"{stem}_{padded_num}.txt"
        text = page.extract_text() or ""
        output_path.write_text(text, encoding="utf-8")
    return total_pages


def _process_pdf(task: SplitTask) -> SplitResult:
    pdf_path, output_dir, text_mode = task
    try:
        if text_mode:
            count = extract_text_by_page(pdf_path, output_dir)
        else:
            count = split_pdf_by_page(pdf_path, output_dir)
        return (pdf_path, count)
    except Exception as exc:
        logger.error(f"Error processing {pdf_path}: {exc}")
        return (pdf_path, 0)


def _process_pdf_tuple(item: tuple[SplitTask]) -> SplitResult:
    return _process_pdf(item[0])


def _run_pool(tasks: Sequence[SplitTask], method: str) -> list[SplitResult]:
    with Pool(processes=POOL_WORKERS) as pool:
        if method == "map":
            return pool.map(_process_pdf_tuple, [(task,) for task in tasks])
        if method == "starmap":
            return pool.starmap(_process_pdf, [(task,) for task in tasks])
        if method == "imap_unordered":
            return list(pool.imap_unordered(_process_pdf_tuple, [(task,) for task in tasks]))
        if method == "apply_async":
            async_results: list[AsyncResult[SplitResult]] = [pool.apply_async(_process_pdf, (task,)) for task in tasks]
            return [result.get() for result in async_results]
    msg = f"Unsupported pool method: {method}"
    raise ValueError(msg)


def collect_pdfs(input_paths: Sequence[str]) -> list[Path]:
    if not input_paths:
        return [p for p in Path.cwd().rglob("*.pdf") if p.is_file()]
    pdf_files: list[Path] = []
    for raw in input_paths:
        p = Path(raw)
        if p.is_file() and p.suffix.lower() == ".pdf":
            pdf_files.append(p)
        elif p.is_dir():
            pdf_files.extend(x for x in p.rglob("*.pdf") if x.is_file())
    return pdf_files


def process_pdfs(
    input_paths: Sequence[str] | None,
    output_dir: Path | None,
    pool_method: str,
    text_mode: bool,
) -> int:
    if output_dir is None:
        output_dir = Path.cwd() / DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = collect_pdfs(list(input_paths) if input_paths else [])
    if not pdf_files:
        logger.warning("No PDF files found.")
        return 0
    tasks: list[SplitTask] = [(pdf, output_dir, text_mode) for pdf in pdf_files]
    results = _run_pool(tasks, pool_method)
    for pdf_path, page_count in results:
        if page_count:
            logger.info(f"{pdf_path}: processed {page_count} pages")
    logger.info(f"Processing complete. Output files in: {output_dir}")
    return len(results)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        help="PDF files or directories to scan; defaults to CWD.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Directory to write outputs into (default: ./output).",
    )
    parser.add_argument(
        "-t",
        "--text",
        action="store_true",
        help="Extract per-page text to .txt files instead of splitting PDF pages.",
    )
    parser.add_argument(
        "--pool-method",
        choices=POOL_METHODS,
        default="map",
        help="Multiprocessing pool method to use for processing.",
    )
    return parser.parse_args()


def main() -> int:
    args: argparse.Namespace = parse_args()
    pool_method: str = args.pool_method
    text_mode: bool = bool(args.text)
    output_dir: Path | None = Path(args.output_dir) if args.output_dir is not None else None
    paths: list[str] = list(args.paths)
    process_pdfs(
        input_paths=paths or None,
        output_dir=output_dir,
        pool_method=pool_method,
        text_mode=text_mode,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
