#!/data/data/com.termux/files/usr/bin/env python

import argparse
import heapq
import json
import mmap
import os
import shutil
import sys
import tempfile
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Iterator, TextIO

from dh import fsz  # format-size function, # TODO remove this import (implement it yourself)

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

#: Files smaller than this are sorted entirely in memory.
IN_MEMORY_THRESHOLD_BYTES = 8 * 1024 * 1024

#: Files larger than this are read through ``mmap``.
MMAP_THRESHOLD_BYTES = 1024 * 1024

#: Number of lines kept in memory per temporary chunk during external sorting.
DEFAULT_CHUNK_LINES = 100_000

#: Convenience alias for the statistics dictionary returned by ``FileSorter``.
Stats = dict[str, Any]


class _CountingIterator(Iterator[str]):
    """Wrap an iterator and expose how many items were consumed.

    Attributes:
        count: Number of items yielded so far.
    """

    __slots__ = ("count", "_iterator")

    def __init__(self, iterator: Iterator[str]) -> None:
        self._iterator = iterator
        self.count = 0

    def __iter__(self) -> "_CountingIterator":
        return self

    def __next__(self) -> str:
        value = next(self._iterator)
        self.count += 1
        return value


class LineProcessor:
    """Common functionality shared by the line-processing helpers."""

    def __init__(self, *, verbose: bool = False) -> None:
        self.verbose = verbose

    def log(self, message: str) -> None:
        """Print ``message`` when verbose mode is enabled."""
        if self.verbose:
            print(f"[INFO] {message}")

    @staticmethod
    def get_file_size(path: Path) -> int:
        """Return the size of *path* in bytes."""
        return Path(path).stat().st_size


class MmapReader(LineProcessor):
    """Read text files line by line without loading them entirely into memory."""

    def read_lines_mmap(
        self,
        path: Path,
        encoding: str = "utf-8",
        skip_empty: bool = False,
    ) -> Iterator[str]:
        """Yield lines from *path* using ``mmap`` for large files.

        Args:
            path: File to read.
            encoding: Text encoding used to decode the bytes.
            skip_empty: When ``True`` blank lines are discarded.

        Yields:
            Decoded lines with their line terminators removed.
        """
        size = self.get_file_size(path)
        if size == 0:
            self.log(f"Reading {path}: empty file")
            return
        self.log(f"Reading {path} ({fsz(size)}) via mmap")
        try:
            with Path(path).open("rb") as handle:
                with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as mapped:
                    offset = 0
                    length = len(mapped)
                    while offset < length:
                        newline = mapped.find(b"\n", offset)
                        end = length if newline < 0 else newline
                        raw = mapped[offset:end]
                        offset = length if newline < 0 else newline + 1
                        try:
                            line = raw.decode(encoding).rstrip("\r\n")
                        except UnicodeDecodeError as exc:
                            self.log(f"Warning: encoding error at offset {offset}: {exc!s}")
                            continue
                        if not skip_empty or line.strip():
                            yield line
        except OSError as exc:
            raise OSError(f"unable to read {path}") from exc

    def read_lines_regular(
        self,
        path: Path,
        encoding: str = "utf-8",
        skip_empty: bool = False,
    ) -> Iterator[str]:
        """Yield lines from *path* using a plain text stream.

        Args:
            path: File to read.
            encoding: Text encoding used to decode the file.
            skip_empty: When ``True`` blank lines are discarded.

        Yields:
            Lines with their line terminators removed.
        """
        self.log(f"Reading {path} (regular mode)")
        try:
            with Path(path).open("r", encoding=encoding) as handle:
                for raw_line in handle:
                    line = raw_line.rstrip("\r\n")
                    if not skip_empty or line.strip():
                        yield line
        except OSError as exc:
            raise OSError(f"unable to read {path}") from exc

    def read_lines(
        self,
        path: Path,
        encoding: str = "utf-8",
        skip_empty: bool = False,
        use_mmap: bool = True,
    ) -> Iterator[str]:
        """Yield lines from *path*, choosing the best strategy automatically.

        Args:
            path: File to read.
            encoding: Text encoding used to decode the file.
            skip_empty: When ``True`` blank lines are discarded.
            use_mmap: Allow ``mmap`` for files above ``MMAP_THRESHOLD_BYTES``.

        Yields:
            Lines with their line terminators removed.
        """
        if use_mmap and self.get_file_size(path) > MMAP_THRESHOLD_BYTES:
            yield from self.read_lines_mmap(path, encoding, skip_empty)
        else:
            yield from self.read_lines_regular(path, encoding, skip_empty)


class LineSorter(LineProcessor):
    """Sort lines either fully in memory or through an external merge sort."""

    @staticmethod
    def _sort_key(case_insensitive: bool) -> Any:
        """Return the sort key used for every sorting stage.

        A tuple ``(lowercased, original)`` is used so that case-insensitive
        sorting remains stable and deterministic.
        """
        if case_insensitive:
            return lambda value: (value.lower(), value)
        return None

    def sort_in_memory(
        self,
        lines: list[str],
        *,
        reverse: bool = False,
        case_insensitive: bool = False,
    ) -> list[str]:
        """Return *lines* sorted in place-safe fashion.

        Args:
            lines: Lines to sort (not modified).
            reverse: Sort in descending order.
            case_insensitive: Ignore case when comparing lines.

        Returns:
            A new sorted list of lines.
        """
        self.log(f"Sorting {len(lines):,} lines in memory")
        return sorted(
            lines,
            key=self._sort_key(case_insensitive),
            reverse=reverse,
        )

    def _write_chunk(
        self,
        chunk: list[str],
        temp_dir: Path,
        index: int,
        *,
        reverse: bool,
        key: Any,
        encoding: str,
    ) -> Path:
        """Sort *chunk* and persist it to a temporary file."""
        chunk.sort(key=key, reverse=reverse)
        temp_file = temp_dir / f".sort_chunk_{os.getpid()}_{index}.tmp"
        with temp_file.open("w", encoding=encoding, newline="\n") as handle:
            for line in chunk:
                handle.write(line)
                handle.write("\n")
        return temp_file

    def create_sorted_chunks(
        self,
        path: Path,
        *,
        chunk_size: int = DEFAULT_CHUNK_LINES,
        reverse: bool = False,
        encoding: str = "utf-8",
        case_insensitive: bool = False,
        skip_empty: bool = False,
    ) -> tuple[list[Path], int]:
        """Split *path* into sorted temporary chunks for external sorting.

        Args:
            path: Input file.
            chunk_size: Maximum number of lines per chunk.
            reverse: Sort in descending order.
            encoding: Text encoding of the input file.
            case_insensitive: Ignore case when comparing lines.
            skip_empty: Skip blank lines while reading.

        Returns:
            A tuple of ``(temp_files, total_lines_read)``.
        """
        self.log(f"External sort enabled (chunk size: {chunk_size:,} lines)")
        reader = MmapReader(verbose=self.verbose)
        temp_dir = Path(tempfile.gettempdir())
        key = self._sort_key(case_insensitive)
        temp_files: list[Path] = []
        total = 0
        chunk: list[str] = []
        try:
            for line in reader.read_lines(path, encoding, skip_empty):
                chunk.append(line)
                total += 1
                if len(chunk) >= chunk_size:
                    temp_files.append(
                        self._write_chunk(
                            chunk,
                            temp_dir,
                            len(temp_files),
                            reverse=reverse,
                            key=key,
                            encoding=encoding,
                        )
                    )
                    chunk = []
            if chunk:
                temp_files.append(
                    self._write_chunk(
                        chunk,
                        temp_dir,
                        len(temp_files),
                        reverse=reverse,
                        key=key,
                        encoding=encoding,
                    )
                )
        except BaseException:
            self.cleanup_temp_files(temp_files)
            raise
        self.log(f"Wrote {len(temp_files)} sorted chunk(s)")
        return temp_files, total

    @staticmethod
    def _strip_lines(handle: TextIO) -> Iterator[str]:
        """Yield lines from an open file without trailing newlines."""
        for raw in handle:
            yield raw.rstrip("\n")

    def merge_sorted_files(
        self,
        temp_files: list[Path],
        *,
        reverse: bool = False,
        case_insensitive: bool = False,
        encoding: str = "utf-8",
        unique: bool = False,
    ) -> Iterator[str]:
        """Merge sorted chunk files into a single sorted stream.

        Because every chunk is already sorted, duplicates (if any) are
        adjacent, which allows de-duplication in O(1) memory.

        Args:
            temp_files: Sorted chunk files produced by ``create_sorted_chunks``.
            reverse: Merge in descending order.
            case_insensitive: Ignore case while merging.
            encoding: Encoding used to read the chunk files.
            unique: Drop duplicate lines while merging.

        Yields:
            Lines in sorted order.
        """
        key = self._sort_key(case_insensitive)
        handles: list[TextIO] = []
        try:
            for temp_file in temp_files:
                handles.append(temp_file.open("r", encoding=encoding))
            streams = [self._strip_lines(handle) for handle in handles]
            merged: Iterable[str]
            if streams:
                merged = heapq.merge(*streams, key=key, reverse=reverse)
            else:
                merged = iter(())
            previous: str | None = None
            has_previous = False
            for line in merged:
                if unique and has_previous and line == previous:
                    continue
                yield line
                previous = line
                has_previous = True
        finally:
            for handle in handles:
                handle.close()

    @staticmethod
    def cleanup_temp_files(temp_files: Iterable[Path]) -> None:
        """Remove temporary chunk files, ignoring missing paths."""
        for temp_file in temp_files:
            try:
                temp_file.unlink(missing_ok=True)
            except OSError:
                pass


class LineDeduplicator(LineProcessor):
    """Remove duplicate lines with predictable memory usage."""

    def deduplicate_list(
        self,
        lines: list[str],
        *,
        preserve_order: bool = False,
    ) -> list[str]:
        """Return a de-duplicated copy of *lines*.

        Args:
            lines: Input lines.
            preserve_order: Keep first-seen order instead of dict order.

        Returns:
            A list containing each distinct line exactly once.
        """
        if preserve_order:
            self.log(f"Deduplicating {len(lines):,} lines (preserving order)")
            seen: set[str] = set()
            unique: list[str] = []
            for line in lines:
                if line not in seen:
                    seen.add(line)
                    unique.append(line)
            return unique
        self.log(f"Deduplicating {len(lines):,} lines")
        return list(dict.fromkeys(lines))

    def deduplicate_stream(self, lines: Iterable[str]) -> Iterator[str]:
        """Yield unique lines from an arbitrary stream.

        The full set of already-seen lines is retained, which is unavoidable
        for unsorted input.

        Args:
            lines: Input line stream.

        Yields:
            Unique lines in first-seen order.
        """
        seen: set[str] = set()
        count = 0
        for line in lines:
            if line not in seen:
                seen.add(line)
                yield line
                count += 1
        self.log(f"Found {count:,} unique lines")

    def deduplicate_sorted(self, lines: Iterable[str]) -> Iterator[str]:
        """Yield unique lines from an already sorted stream in O(1) memory.

        Args:
            lines: Sorted input line stream.

        Yields:
            Unique lines in sorted order.
        """
        previous: str | None = None
        for line in lines:
            if line != previous:
                yield line
                previous = line


class FileSorter(LineProcessor):
    """High-level orchestrator that sorts and de-duplicates a file."""

    def __init__(self, *, verbose: bool = False, dry_run: bool = False) -> None:
        super().__init__(verbose=verbose)
        self.dry_run = dry_run
        self.reader = MmapReader(verbose=verbose)
        self.sorter = LineSorter(verbose=verbose)
        self.deduplicator = LineDeduplicator(verbose=verbose)

    def _write_lines(
        self,
        lines: Iterable[str],
        output: Path,
        encoding: str,
    ) -> tuple[int, int]:
        """Consume *lines* and write them to *output*.

        Output is written to a temporary file in the destination directory and
        atomically moved into place.  In dry-run mode nothing is written and
        the resulting size is only estimated.

        Args:
            lines: Processed lines to write.
            output: Destination path.
            encoding: Encoding used for output.

        Returns:
            A tuple of ``(line_count, size_in_bytes)``.
        """
        if self.dry_run:
            count = 0
            estimated_size = 0
            for line in lines:
                count += 1
                estimated_size += len(line.encode(encoding)) + 1
            self.log(f"DRY RUN: would write {count:,} lines ({fsz(estimated_size)})")
            return count, estimated_size

        output.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=str(output.parent),
        )
        tmp_path = Path(tmp_name)
        count = 0
        try:
            with os.fdopen(fd, "w", encoding=encoding, newline="\n") as handle:
                for line in lines:
                    handle.write(line)
                    handle.write("\n")
                    count += 1
            os.replace(tmp_path, output)
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise

        size = self.get_file_size(output)
        self.log(f"Output written: {output} ({count:,} lines, {fsz(size)})")
        return count, size

    def _streaming_pipeline(
        self,
        input_path: Path,
        output: Path,
        *,
        unique: bool,
        skip_empty: bool,
        encoding: str,
    ) -> tuple[int, int, int]:
        """Process a file without sorting it.

        Returns:
            A tuple of ``(original_lines, final_lines, final_size)``.
        """
        counted = _CountingIterator(self.reader.read_lines(input_path, encoding, skip_empty))
        stream: Iterable[str] = counted
        if unique:
            stream = self.deduplicator.deduplicate_stream(counted)
        final_lines, final_size = self._write_lines(stream, output, encoding)
        self.log(f"Original file: {counted.count:,} lines")
        return counted.count, final_lines, final_size

    def _sorted_pipeline(
        self,
        input_path: Path,
        output: Path,
        *,
        unique: bool,
        reverse: bool,
        case_insensitive: bool,
        skip_empty: bool,
        encoding: str,
        chunk_lines: int,
    ) -> tuple[int, int, int]:
        """Sort a file in memory or via external merge sort.

        Returns:
            A tuple of ``(original_lines, final_lines, final_size)``.
        """
        if self.get_file_size(input_path) <= IN_MEMORY_THRESHOLD_BYTES:
            lines = list(self.reader.read_lines(input_path, encoding, skip_empty))
            original_lines = len(lines)
            self.log(f"Original file: {original_lines:,} lines (in-memory sort)")
            lines = self.sorter.sort_in_memory(
                lines,
                reverse=reverse,
                case_insensitive=case_insensitive,
            )
            stream: Iterable[str] = lines
            if unique:
                stream = self.deduplicator.deduplicate_sorted(stream)
            final_lines, final_size = self._write_lines(stream, output, encoding)
            return original_lines, final_lines, final_size

        temp_files, original_lines = self.sorter.create_sorted_chunks(
            input_path,
            chunk_size=chunk_lines,
            reverse=reverse,
            encoding=encoding,
            case_insensitive=case_insensitive,
            skip_empty=skip_empty,
        )
        self.log(f"Original file: {original_lines:,} lines (external sort)")
        try:
            merged = self.sorter.merge_sorted_files(
                temp_files,
                reverse=reverse,
                case_insensitive=case_insensitive,
                encoding=encoding,
                unique=unique,
            )
            final_lines, final_size = self._write_lines(merged, output, encoding)
        finally:
            LineSorter.cleanup_temp_files(temp_files)
        return original_lines, final_lines, final_size

    def process_file(
        self,
        path: str,
        output_path: str | None = None,
        *,
        sort: bool = True,
        unique: bool = True,
        reverse: bool = False,
        case_insensitive: bool = False,
        skip_empty: bool = False,
        backup: bool = False,
        encoding: str = "utf-8",
        chunk_lines: int = DEFAULT_CHUNK_LINES,
    ) -> Stats:
        """Sort and de-duplicate *path*.

        Args:
            path: Input file.
            output_path: Destination path; defaults to in-place editing.
            sort: Sort the lines.
            unique: Remove duplicate lines.
            reverse: Sort in descending order.
            case_insensitive: Ignore case while sorting.
            skip_empty: Discard blank lines.
            backup: Write ``<input>.bak`` before overwriting the input.
            encoding: Text encoding used for reading and writing.
            chunk_lines: Lines per chunk for external sorting.

        Returns:
            A dictionary with statistics about the operation.

        Raises:
            FileNotFoundError: If the input file does not exist.
            OSError: If reading, writing or the backup fails.
        """
        input_path = Path(path)
        if not input_path.exists():
            raise FileNotFoundError(f"input file not found: {input_path}")

        output = Path(output_path) if output_path else input_path
        original_size = self.get_file_size(input_path)
        start_time = time.monotonic()

        if backup and not self.dry_run and output.resolve() == input_path.resolve():
            backup_path = input_path.with_name(input_path.name + ".bak")
            shutil.copy2(input_path, backup_path)
            self.log(f"Backup written: {backup_path}")

        if sort:
            original_lines, final_lines, after_size = self._sorted_pipeline(
                input_path,
                output,
                unique=unique,
                reverse=reverse,
                case_insensitive=case_insensitive,
                skip_empty=skip_empty,
                encoding=encoding,
                chunk_lines=chunk_lines,
            )
        else:
            original_lines, final_lines, after_size = self._streaming_pipeline(
                input_path,
                output,
                unique=unique,
                skip_empty=skip_empty,
                encoding=encoding,
            )

        duplicate_count = original_lines - final_lines if unique else 0
        elapsed_time = time.monotonic() - start_time

        return {
            "input_file": str(input_path),
            "output_file": str(output),
            "original_lines": original_lines,
            "original_size_bytes": original_size,
            "original_size": fsz(original_size),
            "final_lines": final_lines,
            "after_bytes": after_size,
            "after": fsz(after_size),
            "duplicate_lines": duplicate_count,
            "size_reduction": original_size - after_size,
            "size_reduction_pct": ((original_size - after_size) / original_size * 100 if original_size > 0 else 0.0),
            "processing_time": elapsed_time,
            "lines_per_second": (original_lines / elapsed_time if elapsed_time > 0 else 0.0),
        }

    def print_stats(self, stats: Stats) -> None:
        """Print a short human readable summary of *stats*."""
        duplicate_count = stats["duplicate_lines"]
        if duplicate_count > 0:
            prefix = "would remove" if self.dry_run else "removed"
            print(f"{prefix} {duplicate_count} duplicate lines")
        else:
            print("no duplicate line")

    def save_report(self, stats: Stats, report_file: str | None = None) -> None:
        """Persist *stats* as a JSON report.

        Args:
            stats: Statistics returned by :meth:`process_file`.
            report_file: Destination path; defaults to ``sort_report.json``.
        """
        if report_file is None:
            report_file = "sort_report.json"
        report = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "statistics": stats,
        }
        try:
            with Path(report_file).open("w", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2)
            print(f"Report saved: {report_file}")
        except OSError as exc:
            print(f"Error saving report: {exc!s}")


class FileAnalyzer(LineProcessor):
    """Collect statistics about a text file without storing all its lines."""

    def __init__(self, *, verbose: bool = False) -> None:
        super().__init__(verbose=verbose)
        self.reader = MmapReader(verbose=verbose)

    def analyze_file(self, path: Path, encoding: str = "utf-8") -> dict[str, Any]:
        """Compute statistics for *path*.

        Args:
            path: File to analyze.
            encoding: Text encoding used to decode the file.

        Returns:
            A dictionary describing the file contents.
        """
        size = self.get_file_size(path)
        line_counts: Counter[str] = Counter()
        total_lines = 0
        total_length = 0
        max_length = 0

        for line in self.reader.read_lines(path, encoding):
            line_counts[line] += 1
            total_lines += 1
            length = len(line)
            total_length += length
            if length > max_length:
                max_length = length

        duplicate_count = total_lines - len(line_counts)
        average_length = total_length / total_lines if total_lines else 0.0

        return {
            "file": str(path),
            "size_bytes": size,
            "size": fsz(size),
            "total_lines": total_lines,
            "unique_lines": len(line_counts),
            "duplicate_lines": duplicate_count,
            "duplicate_percentage": (duplicate_count / total_lines * 100 if total_lines else 0.0),
            "max_line_length": max_length,
            "avg_line_length": average_length,
            "most_common_lines": line_counts.most_common(10),
        }

    def print_analysis(self, path: Path, encoding: str = "utf-8") -> None:
        """Print a formatted analysis report for *path*."""
        analysis = self.analyze_file(path, encoding)
        print(f"\n{'=' * 40}")
        print(f"File Analysis: {path.name}")
        print(f"{'=' * 40}")
        print("\nBasic Statistics:")
        print(f"  Size: {analysis['size']}")
        print(f"  Total lines: {analysis['total_lines']:,}")
        print(f"  Unique lines: {analysis['unique_lines']:,}")
        print(f"  Duplicate lines: {analysis['duplicate_lines']:,} ({analysis['duplicate_percentage']:.1f}%)")
        print("\nLine Length Statistics:")
        print(f"  Maximum: {analysis['max_line_length']} characters")
        print(f"  Average: {analysis['avg_line_length']:.1f} characters")
        if analysis["most_common_lines"]:
            print("\nMost Common Lines (Top 10):")
            for line, count in analysis["most_common_lines"]:
                display_line = line[:47] + "..." if len(line) > 50 else line
                print(f"  ({count}x) {display_line}")
        print(f"{'=' * 40}\n")


def _build_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(
        description=("Sort lines in a file and remove duplicates (uses mmap / external sorting for large files)"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "\nExamples:\n"
            "  python sort_unique_lines.py input.txt\n"
            "  python sort_unique_lines.py input.txt -s -u\n"
            "  python sort_unique_lines.py input.txt --output sorted.txt\n"
            "  python sort_unique_lines.py input.txt --reverse -i\n"
            "  python sort_unique_lines.py input.txt --skip-empty --dry-run -v\n"
            "  python sort_unique_lines.py input.txt --analyze\n"
            "  python sort_unique_lines.py input.txt -R stats.json\n"
        ),
    )
    parser.add_argument("filename", help="Input filename")
    parser.add_argument(
        "--output",
        "-o",
        help="Output filename (default: overwrite input)",
    )
    parser.add_argument(
        "-s",
        "--sort",
        action="store_true",
        default=True,
        help="Sort lines (default: enabled)",
    )
    parser.add_argument(
        "-u",
        "--unique",
        action="store_true",
        default=True,
        help="Remove duplicate lines (default: enabled)",
    )
    parser.add_argument(
        "--reverse",
        "-r",
        action="store_true",
        help="Sort in reverse order",
    )
    parser.add_argument(
        "--case-insensitive",
        "-i",
        action="store_true",
        help="Case-insensitive sorting",
    )
    parser.add_argument(
        "--skip-empty",
        action="store_true",
        help="Skip empty lines",
    )
    parser.add_argument(
        "-k",
        "--no-backup",
        action="store_true",
        default=False,
        help="Do not create a .bak file when overwriting the input",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview without modifying files",
    )
    parser.add_argument(
        "--analyze",
        "-a",
        action="store_true",
        help="Analyze file before processing",
    )
    parser.add_argument(
        "--report",
        "-R",
        metavar="FILE",
        help="Save report to JSON file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Verbose output",
    )
    parser.add_argument(
        "--encoding",
        "-e",
        default="utf-8",
        help="File encoding (default: utf-8)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the command line interface.

    Args:
        argv: Argument list, defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        input_path = Path(args.filename)
        if not input_path.exists():
            print(f"Error: File not found: {args.filename}", file=sys.stderr)
            return 1

        if args.analyze:
            analyzer = FileAnalyzer(verbose=args.verbose)
            analyzer.print_analysis(input_path, args.encoding)
            return 0

        sorter = FileSorter(verbose=args.verbose, dry_run=args.dry_run)
        stats = sorter.process_file(
            args.filename,
            output_path=args.output,
            sort=args.sort,
            unique=args.unique,
            reverse=args.reverse,
            case_insensitive=args.case_insensitive,
            skip_empty=args.skip_empty,
            backup=not args.no_backup,
            encoding=args.encoding,
        )
        sorter.print_stats(stats)
        if args.report:
            sorter.save_report(stats, args.report)
    except (OSError, RuntimeError, UnicodeError) as exc:
        print(f"Error: {exc!s}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
