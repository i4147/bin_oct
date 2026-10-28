#!/data/data/com.termux/files/usr/bin/env python
"""Streaming hex-color extractor for text files.

Scans files and directories for CSS-style hex colors (#RGB, #RGBA, #RRGGBB,
#RRGGBBAA), normalizes them to lowercase, and reports per-file occurrences
using a fixed pool of eight worker processes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from multiprocessing import get_context
from pathlib import Path
from typing import Final

from loguru import logger

WORKERS: Final[int] = 8
CHUNKSIZE: Final[int] = 16
READ_SIZE: Final[int] = 1 << 20
MAX_HEX_DIGITS: Final[int] = 8
CARRY_SIZE: Final[int] = MAX_HEX_DIGITS + 1

COLOR_RE: Final[re.Pattern[str]] = re.compile(
    r"#(?:[0-9A-Fa-f]{8}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{4}|[0-9A-Fa-f]{3})(?![0-9A-Fa-f])"
)


@dataclass(frozen=True, slots=True)
class FileResult:
    path: Path
    counts: dict[str, int] | None
    error: str | None


def _extract(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    carry = ""
    with path.open("rb") as handle:
        raw = handle.read(READ_SIZE)
        while raw:
            following = handle.read(READ_SIZE)
            is_final = not following
            text = carry + raw.decode("utf-8", "ignore")
            carry_len = len(carry)
            limit = len(text)
            for match in COLOR_RE.finditer(text):
                end = match.end()
                if end < carry_len:
                    continue
                if not is_final and end == limit:
                    continue
                key = match.group(0).lower()
                counts[key] = counts.get(key, 0) + 1
            carry = text[-CARRY_SIZE:]
            raw = following
    return counts


def process_file(path: Path) -> FileResult:
    try:
        return FileResult(path=path, counts=_extract(path), error=None)
    except Exception as exc:
        return FileResult(path=path, counts=None, error=f"{type(exc).__name__}: {exc}")


def resolve_sources(inputs: list[str]) -> tuple[list[Path], int]:
    sources = inputs if inputs else ["."]
    resolved: list[Path] = []
    missing = 0
    for source in sources:
        path = Path(source)
        if path.is_dir() or path.is_file():
            resolved.append(path)
        else:
            logger.error("Not a file or directory: {}", path)
            missing += 1
    return resolved, missing


def collect_files(sources: list[Path]) -> list[Path]:
    files: list[Path] = []
    for source in sources:
        if source.is_dir():
            files.extend(child for child in source.rglob("*") if child.is_file())
        else:
            files.append(source)
    return files


def format_colors(counts: dict[str, int], show_counts: bool) -> str:
    if show_counts:
        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return " ".join(f"{color}:{count}" for color, count in ordered)
    return " ".join(sorted(counts))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="extract_colors",
        description="Extract CSS hex colors (#RGB, #RGBA, #RRGGBB, #RRGGBBAA) from files.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to scan; defaults to the current directory",
    )
    parser.add_argument(
        "--counts",
        action="store_true",
        help="Append occurrence counts as color:count",
    )
    parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Emit one JSON object per line",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include files that contain no colors",
    )
    args = parser.parse_args(argv)

    sources, missing = resolve_sources(args.paths)
    if missing:
        logger.error("{} input path(s) could not be resolved", missing)
    if not sources:
        logger.warning("No files to scan")
        return 0 if missing == 0 else 1

    try:
        files = collect_files(sources)
    except OSError as exc:
        logger.error("Failed to enumerate files: {}", exc)
        return 1

    if not files:
        logger.warning("No files to scan")
        return 0 if missing == 0 else 1

    logger.info("Scanning {} file(s) with {} workers", len(files), WORKERS)
    chunksize = max(1, min(64, len(files) // (WORKERS * 8)))

    context = get_context("fork")
    out = sys.stdout
    scanned = 0
    with_colors = 0
    total_colors = 0
    failures = 0

    try:
        with context.Pool(processes=WORKERS) as pool:
            for result in pool.imap_unordered(process_file, files, chunksize=chunksize):
                scanned += 1
                if result.error is not None:
                    logger.error("Failed to process {}: {}", result.path, result.error)
                    failures += 1
                    continue
                counts = result.counts if result.counts is not None else {}
                if counts:
                    with_colors += 1
                    total_colors += sum(counts.values())
                elif not args.all:
                    continue
                if args.jsonl:
                    payload = {
                        "path": str(result.path),
                        "colors": dict(sorted(counts.items())),
                    }
                    out.write(json.dumps(payload, ensure_ascii=False))
                    out.write("\n")
                else:
                    rendered = format_colors(counts, args.counts)
                    if rendered:
                        out.write(f"{result.path}\t{rendered}\n")
                    else:
                        out.write(f"{result.path}\n")
    except BrokenPipeError:
        logger.debug("Output pipe closed")
        return 0
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    except Exception as exc:
        logger.error("Scanning aborted: {}", exc)
        return 1

    out.flush()
    logger.info(
        "Done: scanned {} file(s), {} with colors, {} occurrence(s), {} failure(s)",
        scanned,
        with_colors,
        total_colors,
        failures,
    )
    return 0 if failures == 0 and missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
