#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that tells an AI coding agent to reproduce a Python CLI tool that converts data between file formats. The prompt should cover the purpose, inputs/outputs, supported formats, detection logic, the target-name parsing, dependencies, error handling, and usage details. Since the code is truncated at the end, I'll describe the likely remaining behavior carefully as a reasonable assumption rather than stating it as fact.

Reproduce the following Python command-line tool from scratch.

**Purpose:** A cross-format data converter CLI that reads a tabular dataset from one file format and writes it to another. It is intended to run under Termux on Android (the shebang points to the Termux Python interpreter), so it should use a portable `#!/usr/bin/env python`-style shebang with the Termux path as the first line.

**Dependencies:** Python 3 standard library (`argparse`, `json`, `pickle`, `sqlite3`, `sys`, `pathlib`) plus `pandas`. Use `from __future__ import annotations` at the top.

**Supported formats and extension detection:**
- SQLite: `.db`, `.sqlite`, `.sqlite3`
- JSON Lines: `.jsonl`, `.ndjson`
- JSON: `.json`
- CSV: `.csv`
- TSV: `.tsv`
- Pickle: `.pkl`, `.pickle`
- Parquet: `.parquet`, `.pq`
- Excel: `.xlsx`, `.xls`

Extension matching must be case-insensitive. An unrecognized input extension must raise a `ValueError` whose message includes the offending extension in repr form.

**SQLite detection:** Provide a helper that checks whether a file is a real SQLite database by reading its first 16 bytes and comparing them to the standard header `SQLite format 3` followed by a NUL byte. Return False on any `OSError` rather than raising.

**Target format parsing:** Provide a helper that takes a user-supplied target name, strips a leading dot, lowercases it, and maps aliases to canonical format names (e.g., `db`/`sqlite`/`sqlite3` → sqlite, `jsonl`/`ndjson` → jsonl, `pkl`/`pickle` → pkl, `parquet`/`pq` → parquet, `xlsx`/`xls`/`excel` → excel, and `json`/`csv`/`tsv` map to themselves). Unrecognized names raise a `ValueError` with a clear "unsupported" message.

**CLI behavior:** Build the interface with `argparse`. It takes an input file path and a target format (or output path from which the target is derived via the extension). Use `Path` objects throughout. Convert the data by loading into a pandas DataFrame according to the detected input format, then write it out in the requested target format using pandas (or sqlite3 for SQLite output, and pickle for `pkl`). For SQLite input, read the first/specified table into a DataFrame via sqlite3. Exit with a non-zero status and a message to stderr on errors, using `sys.exit`.

**Error handling:** Validate that the input file exists before processing; surface unsupported extensions and targets as clear user-facing errors rather than tracebacks; handle unreadable or non-SQLite files gracefully.

**Edge cases to handle:** Files with uppercase extensions, targets specified with or without a leading dot, input files whose extension lies about their content (use the SQLite magic check to confirm), and empty datasets.

**Output:** Write the converted file to the target path and print a short confirmation to stdout (row count and output path are reasonable).

**Style:** Keep the script a single file, use type hints, small focused helper functions, and a `main()` guarded by `if __name__ == "__main__":` that returns an exit code.
---"""

from __future__ import annotations

import argparse
import json
import pickle
import sqlite3
import sys
from pathlib import Path

import pandas as pd

SQLITE_MAGIC = b"SQLite format 3\x00"


def is_sqlite_file(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(16) == SQLITE_MAGIC
    except OSError:
        return False


def detect_format(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".db", ".sqlite", ".sqlite3"):
        return "sqlite"
    if ext in (".jsonl", ".ndjson"):
        return "jsonl"
    if ext == ".json":
        return "json"
    if ext == ".csv":
        return "csv"
    if ext == ".tsv":
        return "tsv"
    if ext in (".pkl", ".pickle"):
        return "pkl"
    if ext in (".parquet", ".pq"):
        return "parquet"
    if ext in (".xlsx", ".xls"):
        return "excel"
    msg = f"Unsupported input extension: {ext!r}"
    raise ValueError(msg)


def parse_target(name: str) -> str:
    n = name.lower().lstrip(".")
    if n in ("db", "sqlite", "sqlite3"):
        return "sqlite"
    if n in ("jsonl", "ndjson"):
        return "jsonl"
    if n in ("pkl", "pickle"):
        return "pkl"
    if n in ("parquet", "pq"):
        return "parquet"
    if n in ("xlsx", "xls", "excel"):
        return "excel"
    if n in ("json", "csv", "tsv"):
        return n
    msg = f"Unsupported target format: {name!r}"
    raise ValueError(msg)


def _coerce_to_tables(obj) -> dict[str, pd.DataFrame]:
    if isinstance(obj, pd.DataFrame):
        return {"data": obj}
    if isinstance(obj, dict):
        if obj and all(isinstance(v, pd.DataFrame) for v in obj.values()):
            return dict(obj)
        if obj and all(isinstance(v, list) for v in obj.values()):
            return {k: pd.DataFrame(v) for k, v in obj.items()}
        return {"data": pd.DataFrame([obj])}
    if isinstance(obj, list):
        return {"data": pd.DataFrame(obj)}
    return {"data": pd.DataFrame([{"value": obj}])}


def read_json(path: Path) -> dict[str, pd.DataFrame]:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if isinstance(obj, list):
        return {"data": pd.DataFrame(obj)}
    if isinstance(obj, dict):
        if obj and all(isinstance(v, list) for v in obj.values()):
            return {k: pd.DataFrame(v) for k, v in obj.items()}
        return {"data": pd.DataFrame([obj])}
    msg = f"Unsupported JSON root type: {type(obj).__name__}"
    raise ValueError(msg)


def read_jsonl(path: Path) -> dict[str, pd.DataFrame]:
    return {"data": pd.read_json(path, orient="records", lines=True)}


def read_csv(path: Path) -> dict[str, pd.DataFrame]:
    return {"data": pd.read_csv(path)}


def read_tsv(path: Path) -> dict[str, pd.DataFrame]:
    return {"data": pd.read_csv(path, sep="\t")}


def read_pkl(path: Path) -> dict[str, pd.DataFrame]:
    with open(path, "rb") as f:
        return _coerce_to_tables(pickle.load(f))


def read_sqlite(path: Path) -> dict[str, pd.DataFrame]:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        names = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
            con,
        )["name"].tolist()
        return {n: pd.read_sql_query(f'SELECT * FROM "{n}"', con) for n in names}
    finally:
        con.close()


def read_parquet(path: Path) -> dict[str, pd.DataFrame]:
    return {"data": pd.read_parquet(path)}


def read_excel(path: Path) -> dict[str, pd.DataFrame]:
    return dict(pd.read_excel(path, sheet_name=None))


def _single(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if len(tables) != 1:
        msg = f"this output format supports a single table, got {len(tables)}: {list(tables)}"
        raise ValueError(msg)
    return next(iter(tables.values()))


def write_json(tables: dict[str, pd.DataFrame], path: Path) -> None:
    if len(tables) == 1:
        payload = _single(tables).to_dict(orient="records")
    else:
        payload = {k: df.to_dict(orient="records") for k, df in tables.items()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str, ensure_ascii=False)


def write_jsonl(tables: dict[str, pd.DataFrame], path: Path) -> None:
    df = _single(tables)
    df.to_json(
        path,
        orient="records",
        lines=True,
        force_ascii=False,
        default_handler=str,
    )


def write_csv(tables: dict[str, pd.DataFrame], path: Path) -> None:
    _single(tables).to_csv(path, index=False)


def write_tsv(tables: dict[str, pd.DataFrame], path: Path) -> None:
    _single(tables).to_csv(path, index=False, sep="\t")


def write_pkl(tables: dict[str, pd.DataFrame], path: Path) -> None:
    obj = next(iter(tables.values())) if len(tables) == 1 else tables
    with open(path, "wb") as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)


def write_sqlite(tables: dict[str, pd.DataFrame], path: Path) -> None:
    con = sqlite3.connect(path)
    try:
        for name, df in tables.items():
            df.to_sql(name, con, if_exists="replace", index=False)
    finally:
        con.close()


def write_parquet(tables: dict[str, pd.DataFrame], path: Path) -> None:
    _single(tables).to_parquet(path, index=False)


def write_excel(tables: dict[str, pd.DataFrame], path: Path) -> None:
    with pd.ExcelWriter(path) as xw:
        for name, df in tables.items():
            df.to_excel(xw, sheet_name=name[:31], index=False)


READERS = {
    "json": read_json,
    "jsonl": read_jsonl,
    "csv": read_csv,
    "tsv": read_tsv,
    "pkl": read_pkl,
    "sqlite": read_sqlite,
    "parquet": read_parquet,
    "excel": read_excel,
}
WRITERS = {
    "json": write_json,
    "jsonl": write_jsonl,
    "csv": write_csv,
    "tsv": write_tsv,
    "pkl": write_pkl,
    "sqlite": write_sqlite,
    "parquet": write_parquet,
    "excel": write_excel,
}
EXT_FOR = {
    "json": ".json",
    "jsonl": ".jsonl",
    "csv": ".csv",
    "tsv": ".tsv",
    "pkl": ".pkl",
    "sqlite": ".sqlite",
    "parquet": ".parquet",
    "excel": ".xlsx",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert between data container file formats.",
    )
    parser.add_argument("input", help="input file path")
    parser.add_argument(
        "-d",
        "--dest",
        required=True,
        help="target extension, e.g. csv, .json, sqlite, pkl",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="output path (default: input path with new extension)",
    )
    args = parser.parse_args(argv)
    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"input file not found: {input_path}")
    try:
        src_fmt = detect_format(input_path)
        dst_fmt = parse_target(args.dest)
    except ValueError as e:
        parser.error(str(e))
    output_path = Path(args.output) if args.output else input_path.with_suffix(EXT_FOR[dst_fmt])
    tables = READERS[src_fmt](input_path)
    WRITERS[dst_fmt](tables, output_path)
    n = len(tables)
    print(f"{input_path}  [{src_fmt}]  ->  {output_path}  [{dst_fmt}]   ({n} table{'s' if n != 1 else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
