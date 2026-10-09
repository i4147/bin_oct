#!/data/data/com.termux/files/usr/bin/env python
"""Design a Python 3 command-line utility (intended to run under Termux on Android, using the `/data/data/com.termux/files/usr/bin/python3.12` interpreter) that exports the contents of a SQLite database into JSON. script's purpose is to open a given SQLite database file in read-only mode, enumerate all user tables (and optionally other object types), and dump each table's rows into one or more JSON files, handling large tables efficiently and encoding binary (BLOB) data in a JSON-safe way.

Key requirements and behavior:

1. **CLI interface (via `argparse`)**:
   - Positional argument: path to the source SQLite database file.
   - Option to specify an output directory (default could be current directory or a derived name),.
   - Option to select which tables to export (default: all tables), e.g. an include/exclude list or pattern.
   - Option to control BLOB encoding, supporting at least four modes: `base64`, `hex`, `base64-plain`, `hex-plain` — where the non-"plain" variants wrap the encoded string in a small object with a marker key (`__blob_base64` or `__blob_hex`) so consumers can distinguish encoded blobs from plain strings, while the "-plain" variants just emit the raw encoded string.
   - Option to control parallelism (number of worker processes) for exporting multiple tables concurrently.
   - Option to control batch size / rows per fetch (default 5000) to keep memory usage flat regardless of table size, using `cursor.fetchmany()`-style batched reads.
   - Option for pretty-printing vs. compact JSON output, and/or indentation level.
   - Option to overwrite existing output files or skip/skip-existing behavior.

2. **Database handling**:
   - Open the SQLite file strictly read-only (e.g. via a `file:` URI with `mode=ro`), failing gracefully with a clear error message if the file doesn't exist or isn't a valid SQLite database.
   - Query `sqlite_master` (or `sqlite_schema`) to list tables (excluding internal `sqlite_*` tables unless explicitly requested). identifiers (table double-`quidentifier` style) to safely handle names

3. **Value/version for `str` pass through unchanged.
   - `float` values are pass they are N in which case they are stringified (since stand support them).
   - `bytes`/`bytearray`/`memoryview` (SQLite BLOBs) are converted using the selected blob encoder function.
   - Any other/unexpected type is converted via `str()` as a fallback.

4. **Export process**:
   - For each table, stream rows in batches (using the configurable batch size) rather than loading the entire table into memory at once.
   - Convert each row into a JSON-serializable structure (e.g., list of dicts keyed by column name, or list of row arrays plus a column-name list) using the value-conversion logic above.
   - Write each table's data to its own JSON output file named after the table (sanitized for filesystem safety), inside the specified output directory.
   - Use parallel processing (`ProcessPoolExecutor` with `as_completed`) to export multiple tables concurrently when more than one worker is requested, reporting progress/ table as they complete.
   - Use temporary files (`tempfile`) and atomic rar safe-write technaving partiallySON files ifrupted.

5. **Error handling and output**:
   - Handle missing files, corrupt databases, permission errors, and invalid CLI arguments gracefully, printing clear error messages to stderr and exiting with non-zero status codes.
   - Print a summary to stdout/stderr indicating which tables were exported, how many rows each contained, and where the output files were written, including any tables that failed and why.

6. **Code structure**:
   - Use type hints throughout (`from __future__ import annotations`, `Any`, `Callable`, etc.).
   - Keep helper functions small and composable (e.g., `quote_identifier`, `make_blob_encoder`, `encode_value`, a read-only DB opener, a per-table export function suitable for use as a worker in a process pool).
   - Use `contextlib.closing` to ensure database connections/cursors are properly closed.
   - Use `pathlib.Path` for filesystem path handling and `shutil` for any file operations (like moving temp files into place).
   - The script should be self-contained, relying only on the Python standard library (`argparse`, `base64`, `json`, `math`, `os`, `shutil`, `sqlite3`, `sys`, `tempfile`, `concurrent.futures`, `contextlib`, `pathlib`, `typing`).
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/NLfg7xEcezESTtnxdzoitQ"""

from __future__ import annotations
import argparse
import base64
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import closing
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from typing import Any, Callable


BLOB_BASE64 = "__blob_base64"
BLOB_HEX = "__blob_hex"

BATCH_SIZE = 5000


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def make_blob_encoder(blob_encoding: str) -> Callable[[bytes], Any]:

    encoders: dict[str, Callable[[bytes], Any]] = {
        "base64": lambda d: {BLOB_BASE64: base64.b64encode(d).decode("ascii")},
        "hex": lambda d: {BLOB_HEX: d.hex()},
        "base64-plain": lambda d: base64.b64encode(d).decode("ascii"),
        "hex-plain": lambda d: d.hex(),
    }
    try:
        return encoders[blob_encoding]
    except KeyError:
        msg = f"Unsupported blob encoding: {blob_encoding}"
        raise ValueError(msg) from None


def encode_value(value: Any, blob_fn: Callable[[bytes], Any]) -> Any:
    if value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return blob_fn(bytes(value))
    return str(value)


def open_readonly(db_path: str, text_errors: str) -> sqlite3.Connection:

    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)

    conn.text_factory = lambda b: b.decode("utf-8", errors=text_errors)
    return conn


def get_tables(conn: sqlite3.Connection, include_internal: bool = False) -> list[str]:
    sql = "SELECT name FROM sqlite_master WHERE type = 'table'"
    if not include_internal:
        sql += r" AND name NOT LIKE 'sqlite\_%' ESCAPE '\'"
    sql += " ORDER BY name"
    return [row[0] for row in conn.execute(sql)]


def write_table_array(
    conn: sqlite3.Connection,
    table: str,
    fp,
    blob_fn: Callable[[bytes], Any],
    indent: int,
    ensure_ascii: bool,
) -> None:

    nl = "\n" if indent else ""
    pad1 = " " * indent
    pad2 = pad1 * 2
    separators = None if indent else (",", ":")

    cur = conn.execute(f"SELECT * FROM {quote_identifier(table)}")

    cols = [d[0] for d in cur.description]

    first = True
    while True:
        batch = cur.fetchmany(BATCH_SIZE)
        if not batch:
            break
        for row in batch:
            obj = {c: encode_value(v, blob_fn) for c, v in zip(cols, row)}
            text = json.dumps(
                obj,
                ensure_ascii=ensure_ascii,
                indent=indent or None,
                separators=separators,
            )
            if indent:
                text = text.replace("\n", "\n" + pad2)
            fp.write(("[" if first else ",") + nl + pad2 + text)
            first = False

    fp.write("[]" if first else nl + pad1 + "]")


def export_table(args: tuple) -> tuple[str, str | None]:

    db_path, table, frag_path, blob_encoding, text_errors, indent, ensure_ascii = args
    try:
        blob_fn = make_blob_encoder(blob_encoding)
        with (
            closing(open_readonly(db_path, text_errors)) as conn,
            open(frag_path, "w", encoding="utf-8", errors="replace", newline="\n") as fp,
        ):
            write_table_array(conn, table, fp, blob_fn, indent, ensure_ascii)
        return table, None
    except Exception as exc:
        with open(frag_path, "w", encoding="utf-8", newline="\n") as fp:
            fp.write("[]")
        return table, f"Error processing table {table!r}: {exc}"


def convert_sqlite_to_json(
    db_path: Path,
    output_path: Path,
    *,
    blob_encoding: str = "base64",
    indent: int = 2,
    ensure_ascii: bool = False,
    text_errors: str = "replace",
    include_internal: bool = False,
    jobs: int = 1,
    fail_fast: bool = False,
) -> list[str]:
    make_blob_encoder(blob_encoding)
    indent = max(0, indent)
    warnings: dict[str, str] = {}

    with closing(open_readonly(str(db_path), text_errors)) as conn:
        tables = get_tables(conn, include_internal)

    output_path = output_path.resolve()
    out_dir = output_path.parent

    with tempfile.TemporaryDirectory(dir=out_dir, prefix=".sqlite2json_") as tmp:
        tmp_dir = Path(tmp)
        frags = {t: tmp_dir / f"{i}.part" for i, t in enumerate(tables)}
        tasks = [(str(db_path), t, str(frags[t]), blob_encoding, text_errors, indent, ensure_ascii) for t in tables]

        workers = min(jobs, len(tasks))
        if workers > 1:
            pool = ProcessPoolExecutor(max_workers=workers)
            try:
                futures = [pool.submit(export_table, t) for t in tasks]
                for future in as_completed(futures):
                    table, warning = future.result()
                    if warning:
                        warnings[table] = warning
                        if fail_fast:
                            raise RuntimeError(warning)
            except BaseException:
                pool.shutdown(wait=False, cancel_futures=True)
                raise
            else:
                pool.shutdown()
        else:
            for task in tasks:
                table, warning = export_table(task)
                if warning:
                    warnings[table] = warning
                    if fail_fast:
                        raise RuntimeError(warning)

        nl = "\n" if indent else ""
        pad1 = " " * indent
        colon = ": " if indent else ":"
        final_tmp = tmp_dir / "final.json"
        with open(final_tmp, "w", encoding="utf-8", errors="replace", newline="\n") as out:
            if not tables:
                out.write("{}")
            else:
                out.write("{" + nl)
                for i, table in enumerate(tables):
                    if i:
                        out.write("," + nl)
                    out.write(pad1 + json.dumps(table, ensure_ascii=ensure_ascii) + colon)
                    with open(frags[table], "r", encoding="utf-8", newline="\n") as frag:
                        shutil.copyfileobj(frag, out, 1 << 20)
                out.write(nl + "}")
            out.write("\n")

        os.replace(final_tmp, output_path)

    return [warnings[t] for t in tables if t in warnings]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert a SQLite database to JSON.")
    parser.add_argument("database", type=Path, help="SQLite database file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output JSON file (default: <database>.json)",
    )
    parser.add_argument(
        "--blob-encoding",
        choices=("base64", "hex", "base64-plain", "hex-plain"),
        default="base64",
        help="How to encode BLOB values (default: base64)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation, 0 for compact output (default: 2)",
    )
    parser.add_argument(
        "--ensure-ascii",
        action="store_true",
        help="Escape non-ASCII characters in JSON",
    )
    parser.add_argument(
        "--text-errors",
        choices=("replace", "ignore", "strict", "surrogateescape"),
        default="replace",
        help="How to handle invalid UTF-8 text (default: replace)",
    )
    parser.add_argument(
        "--include-internal",
        action="store_true",
        help="Include sqlite_% internal tables",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Number of parallel processes (default: 1)",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop at first table error",
    )
    args = parser.parse_args(argv)

    if not args.database.is_file():
        print(f"Error: database file not found: {args.database}", file=sys.stderr)
        return 1

    output_path = args.output or args.database.with_name(args.database.name + ".json")

    if output_path.resolve() == args.database.resolve():
        print("Error: output path must differ from the database path", file=sys.stderr)
        return 1

    try:
        warnings = convert_sqlite_to_json(
            args.database,
            output_path,
            blob_encoding=args.blob_encoding,
            indent=args.indent,
            ensure_ascii=args.ensure_ascii,
            text_errors=args.text_errors,
            include_internal=args.include_internal,
            jobs=max(1, args.jobs),
            fail_fast=args.fail_fast,
        )
    except sqlite3.Error as exc:
        print(f"SQLite error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Converted {args.database} to {output_path}")
    if warnings:
        print("Warnings:", file=sys.stderr)
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
