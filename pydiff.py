#!/data/data/com.termux/files/home/.local/bin/python
"""
Generate a Python CLI script that compares two text files and reports the
lines unique to each file plus the number of common lines.

The generated script should:
- Accept two file paths as positional CLI arguments.
- Read both files line-by-line (using in-memory text reads), stripping
  leading/trailing spaces and tabs from lines when the file has a known
  source-code extension.
- Compute set differences and, for very large files (both over 10,000
  lines), shard the first file's lines into chunks and process the
  filtering step concurrently.
- Use multiprocessing.Pool.imap_unordered with a fixed pool of 8 workers
  (no CLI flag controls parallelism).
- Log the "only in <file>" lines and a final summary using loguru.
- Include complete type hints, docstrings on every function, and this
  module-level docstring.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Sequence
from difflib import unified_diff
from multiprocessing import Pool
from pathlib import Path
from typing import Final

from loguru import logger

POOL_SIZE: Final[int] = 8
LARGE_FILE_THRESHOLD: Final[int] = 10_000
MIN_CHUNK_SIZE: Final[int] = 1_000
SHOW_LIMIT: Final[int] = 10
PREVIEW_COUNT: Final[int] = 3
DIFF_SHOW_LIMIT: Final[int] = 100
DIFF_PREVIEW_COUNT: Final[int] = 20
DIFF_LOG_PATH: Final[Path] = Path("difflines_full_diff.log")
USAGE: Final[str] = "usage: difflines.py [-d | --diff] <file1> <file2>"

CODE_EXT: Final[frozenset[str]] = frozenset(
    {
        ".py",
        ".js",
        ".ts",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".java",
        ".go",
        ".rs",
        ".rb",
        ".sh",
        ".lua",
    }
)

ReadResult = tuple[Path, list[str]]
ChunkTask = tuple[int, tuple[str, ...], frozenset[str]]
ChunkResult = tuple[int, tuple[str, ...]]


def read_file_task(path: Path) -> ReadResult:
    lines: list[str] = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if path.suffix.lower() in CODE_EXT:
        lines = [ln.strip(" \t") for ln in lines]
    return path, lines


def filter_chunk(task: ChunkTask) -> ChunkResult:
    idx, chunk, exclude = task
    return idx, tuple(ln for ln in chunk if ln not in exclude)


def load_files(path1: Path, path2: Path) -> tuple[list[str], list[str]]:
    loaded: dict[Path, list[str]] = {}
    with Pool(processes=POOL_SIZE) as pool:
        for path, lines in pool.imap_unordered(
            read_file_task, (path1, path2), chunksize=1
        ):
            loaded[path] = lines
    return loaded[path1], loaded[path2]


def unique_parallel(lines: list[str], exclude: frozenset[str], pool: Pool) -> list[str]:
    size: int = max(MIN_CHUNK_SIZE, len(lines) // (POOL_SIZE * 4))
    tasks: list[ChunkTask] = [
        (i, tuple(lines[s : s + size]), exclude)
        for i, s in enumerate(range(0, len(lines), size))
    ]
    parts: dict[int, tuple[str, ...]] = {}
    for idx, chunk in pool.imap_unordered(filter_chunk, tasks, chunksize=1):
        parts[idx] = chunk
    out: list[str] = []
    extend = out.extend
    for i in range(len(tasks)):
        extend(parts[i])
    return out


def unique_lines(lines: list[str], exclude: frozenset[str], pool: Pool) -> list[str]:
    if len(lines) <= LARGE_FILE_THRESHOLD:
        return [ln for ln in lines if ln not in exclude]
    return unique_parallel(lines, exclude, pool)


def common_preview(
    lines1: Sequence[str], set2: frozenset[str], total: int
) -> list[str]:
    limit: int = total if total <= SHOW_LIMIT else PREVIEW_COUNT
    out: list[str] = []
    seen: set[str] = set()
    for ln in lines1:
        if ln in set2 and ln not in seen:
            seen.add(ln)
            out.append(ln)
            if len(out) >= limit:
                break
    return out


def log_section(title: str, lines: Sequence[str], total: int, color: str) -> None:
    if total == 0:
        return
    print("{} ({}):", title, total)
    logc = logger.opt(colors=True)
    limit: int = total if total <= SHOW_LIMIT else PREVIEW_COUNT
    for ln in lines[:limit]:
        logc.info("<{}>  - {}</{}>", color, ln, color)
    if total > SHOW_LIMIT:
        print("  ... and {} more line(s)", total - limit)


def log_diff(path1: Path, path2: Path, lines1: list[str], lines2: list[str]) -> None:
    diff_lines: list[str] = list(
        unified_diff(
            lines1, lines2, fromfile=str(path1), tofile=str(path2), lineterm=""
        )
    )
    total: int = len(diff_lines)
    if total == 0:
        print("diff: files are identical")
        return
    print("diff ({} line(s)):", total)
    logc = logger.opt(colors=True)
    limit: int = total if total <= DIFF_SHOW_LIMIT else DIFF_PREVIEW_COUNT
    for ln in diff_lines[:limit]:
        if ln.startswith("+"):
            logc.info("<green>{}</green>", ln)
        elif ln.startswith("-"):
            logc.info("<red>{}</red>", ln)
        else:
            logc.info("<dim>{}</dim>", ln)
    if total > DIFF_SHOW_LIMIT:
        DIFF_LOG_PATH.write_text("\n".join(diff_lines) + "\n", encoding="utf-8")
        print(
            "  ... {} more line(s); full diff written to {}",
            total - limit,
            DIFF_LOG_PATH,
        )


def main(argv: Iterable[str] | None = None) -> int:
    args: list[str] = list(argv) if argv is not None else sys.argv[1:]
    show_diff: bool = False
    names: list[str] = []
    for arg in args:
        if arg in ("-d", "--diff"):
            show_diff = True
        elif arg in ("-h", "--help"):
            print(USAGE)
            return 0
        elif arg.startswith("-") and arg != "-":
            logger.error("unknown option: {}\n{}", arg, USAGE)
            return 1
        else:
            names.append(arg)
    if len(names) != 2:
        logger.error(USAGE)
        return 1
    path1: Path = Path(names[0])
    path2: Path = Path(names[1])
    for p in (path1, path2):
        if not p.is_file():
            logger.error("not a file: {}", p)
            return 1
    try:
        lines1, lines2 = load_files(path1, path2)
    except OSError as exc:
        logger.error("read failed: {}", exc)
        return 1

    set1: frozenset[str] = frozenset(lines1)
    set2: frozenset[str] = frozenset(lines2)
    common_count: int = len(set1 & set2)

    with Pool(processes=POOL_SIZE) as pool:
        only1: list[str] = unique_lines(lines1, set2, pool)
        only2: list[str] = unique_lines(lines2, set1, pool)

    if show_diff:
        try:
            log_diff(path1, path2, lines1, lines2)
        except OSError as exc:
            logger.error("diff log write failed: {}", exc)
            return 1

    log_section(f"only in {path1.name}", only1, len(only1), "green")
    log_section(f"only in {path2.name}", only2, len(only2), "yellow")
    log_section(
        "common", common_preview(lines1, set2, common_count), common_count, "blue"
    )

    logger.opt(colors=True).info(
        "<blue>summary: common: {} | only in {}: {} | only in {}: {}</blue>",
        common_count,
        path1.name,
        len(only1),
        path2.name,
        len(only2),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
