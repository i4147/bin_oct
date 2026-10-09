#!/data/data/com.termux/files/usr/bin/python
"""
Unified Comment Out CLI

Consolidates functionality for commenting out ranges of lines in files.
Supports in-memory processing for small files and chunked processing for large files.

Usage Examples:
    python merged.py comment script.py 10 20 --in-memory --add-space
    python merged.py comment large_script.sql 500 --chunk-size 5000
"""

from __future__ import annotations
import argparse
from multiprocessing import Pool
from pathlib import Path
import sys
import tempfile


# Union of extensions from both scripts
COMMENT_MAP = {
    ".py": "#",
    ".sh": "#",
    ".yaml": "#",
    ".yml": "#",
    ".rb": "#",
    ".js": "//",
    ".ts": "//",
    ".cpp": "//",
    ".c": "//",
    ".java": "//",
    ".go": "//",
    ".html": "<!--",
    ".css": "/*",
    ".vim": '"',
    ".lua": "--",
    ".toml": "#",
    ".cs": "//",
    ".sql": "--",
}


def process_chunk(lines: list, comment_char: str, add_space: bool) -> list:
    """Processes a chunk of lines (behavior inherited from commentout.py)."""
    result = []
    prefix = f"{comment_char} " if add_space else comment_char
    for line in lines:
        stripped = line.lstrip()
        # commentout.py explicitly skips empty lines
        if not stripped or stripped.startswith(comment_char):
            result.append(line)
        else:
            result.append(f"{prefix}{line}")
    return result


def process_in_memory(filename: Path, start_line: int, end_line: int, comment_char: str, add_space: bool) -> None:
    """Processes the file entirely in memory (behavior inherited from comment_out.py)."""
    with filename.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    total_lines = len(lines)
    if start_line > total_lines:
        print(f"Error: Start line ({start_line}) exceeds file length ({total_lines} lines).", file=sys.stderr)
        sys.exit(1)

    p_end = end_line if end_line is not None else total_lines
    end_idx = min(p_end, total_lines)

    # 1-indexed to 0-indexed translation
    for i in range(start_line - 1, end_idx):
        stripped = lines[i].strip()
        # comment_out.py comments out empty lines because strip() makes them "" which doesn't start with '#'
        if not stripped.startswith(comment_char):
            prefix = f"{comment_char} " if add_space else comment_char
            lines[i] = f"{prefix}{lines[i]}"

    with filename.open("w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Success: Commented out lines {start_line} to {end_idx} in '{filename}' using '{comment_char}'.")


def process_chunked(
    filename: Path, start_line: int, end_line: int, comment_char: str, add_space: bool, workers: int, chunk_size: int
) -> None:
    """Processes the file using chunks and optional multiprocessing (behavior inherited from commentout.py)."""
    p_end = end_line if end_line is not None else sys.maxsize

    with (
        filename.open("r", encoding="utf-8", errors="ignore") as f_in,
        tempfile.NamedTemporaryFile("w", delete=False, dir=filename.parent, encoding="utf-8") as f_out,
    ):
        temp_path = Path(f_out.name)
        current_line = 1

        # Original code used pool trivially blocking on `.get()`. We preserve the Pool availability.
        pool = Pool(processes=workers) if workers > 1 else None

        try:
            while True:
                chunk = [f_in.readline() for _ in range(chunk_size)]
                chunk = [line for line in chunk if line]
                if not chunk:
                    break

                chunk_start = current_line
                chunk_end = current_line + len(chunk) - 1

                # Check if the current chunk overlaps with the target line range
                if chunk_start <= p_end and chunk_end >= start_line:
                    rel_start = max(0, start_line - chunk_start)
                    rel_end = max(0, p_end - chunk_start + 1) if end_line is not None else len(chunk)

                    pre_lines = chunk[:rel_start]
                    target_lines = chunk[rel_start:rel_end]
                    post_lines = chunk[rel_end:]

                    if pool:
                        async_res = pool.apply_async(process_chunk, (target_lines, comment_char, add_space))
                        processed_target = async_res.get()
                    else:
                        processed_target = process_chunk(target_lines, comment_char, add_space)

                    f_out.writelines(pre_lines)
                    f_out.writelines(processed_target)
                    f_out.writelines(post_lines)
                else:
                    f_out.writelines(chunk)

                current_line += len(chunk)
        finally:
            if pool:
                pool.close()
                pool.join()

    temp_path.replace(filename)
    print(f"Successfully processed '{filename}' using '{comment_char}'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified Comment Out CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_comment = subparsers.add_parser("comment", help="Comment out a range of lines in a file")
    p_comment.add_argument("filename", type=Path, help="File to modify")
    p_comment.add_argument("start_line", type=int, help="Starting line number (1-indexed)")
    p_comment.add_argument("end_line", type=int, nargs="?", default=None, help="Ending line number (optional)")

    # Original behavior flags
    p_comment.add_argument("--add-space", action="store_true", help="Add a space after the comment character")
    p_comment.add_argument("--in-memory", action="store_true", help="Process the file entirely in memory")
    p_comment.add_argument(
        "-w", "--workers", type=int, default=8, help="Number of workers for chunked processing (default: 8)"
    )
    p_comment.add_argument(
        "-c", "--chunk-size", type=int, default=10000, help="Number of lines per chunk (default: 10000)"
    )

    args = parser.parse_args()

    if args.command == "comment":
        if args.start_line < 1:
            print("Error: Line numbers must start from 1.", file=sys.stderr)
            sys.exit(1)

        if args.end_line is not None and args.end_line < args.start_line:
            print("Error: End line must be >= start line.", file=sys.stderr)
            sys.exit(1)

        if not args.filename.exists():
            print(f"Error: The file '{args.filename}' does not exist.", file=sys.stderr)
            sys.exit(1)

        comment_char = COMMENT_MAP.get(args.filename.suffix.lower())
        if comment_char is None:
            print(f"Warning: Unknown extension '{args.filename.suffix.lower()}'. Using default '#' as comment char.")
            comment_char = "#"

        if args.in_memory:
            if args.end_line is None:
                print("Error: --in-memory mode requires both start_line and end_line.", file=sys.stderr)
                sys.exit(1)
            process_in_memory(args.filename, args.start_line, args.end_line, comment_char, args.add_space)
        else:
            process_chunked(
                args.filename,
                args.start_line,
                args.end_line,
                comment_char,
                args.add_space,
                args.workers,
                args.chunk_size,
            )


if __name__ == "__main__":
    main()
