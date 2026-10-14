#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that searches a local SQLite database of package names and their download counts, then prints the most relevant matches for a user-supplied query.
The script should automatically locate the database file at a fixed default path, but also allow the user to override that path from the command line. It should inspect the database schema on its own, choosing a suitable table: prefer a table with exactly two columns, where the first column holds a name (such as a package name) and the second holds a numeric download or popularity count. If no such table exists, fall back to the first table with at least two columns, and exit with a clear error message if the database is empty or the schema is unusable.
The main behavior is fuzzy, forgiving name search. Given a search term, the script should rank matching names using a combination of exact matches, prefix matches, substring matches, and approximate (typo-tolerant) similarity, so that the most relevant results appear first. Results should be ordered primarily by relevance and secondarily by download count. Searches should be case-insensitive. Short search terms should still return useful results, and the script should support a configurable maximum number of results, with a sensible default.
Consider using an efficient indexing or candidate-filtering strategy so that searches remain fast on large databases with many thousands of rows, rather than scoring every row naively where avoidable.
The output should be a clean, human-readable list showing each matched name, its download count formatted for readability (for example with thousands separators), and its rank. The script should handle empty queries gracefully, report when nothing matches, and handle a missing database file or database errors with friendly messages and nonzero exit codes instead of tracebacks.
Provide a simple command-line interface: the search term is a required positional argument, with optional flags for the database path, the result limit, and an option to output results as JSON. Include brief usage help.
---"""

from __future__ import annotations
import argparse
import heapq
from pathlib import Path
import sqlite3
import sys

DB_PATH = Path("/sdcard/data/pip.db")
DEFAULT_LIMIT = 20
TRIGRAM_MIN = 3


def get_table_info(con: sqlite3.Connection):
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cur.fetchall()]
    if not tables:
        sys.exit("No tables found in database.")
    chosen = None
    for t in tables:
        cur = con.execute(f'PRAGMA table_info("{t}")')
        cols = cur.fetchall()
        if len(cols) == 2:
            chosen = (t, [c[1] for c in cols])
            break
    if chosen is None:
        t = tables[0]
        cur = con.execute(f'PRAGMA table_info("{t}")')
        cols = [c[1] for c in cur.fetchall()]
        if len(cols) < 2:
            sys.exit(f"Table '{t}' must have at least two columns.")
        chosen = (t, cols)
    table, col_names = chosen
    name_col, dl_col = col_names[0], col_names[1]
    cur = con.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    row = cur.fetchone()
    is_fts5 = bool(row and row[0] and "fts5" in row[0].lower())
    return table, name_col, dl_col, is_fts5


def search(
    con: sqlite3.Connection,
    table: str,
    name_col: str,
    dl_col: str,
    is_fts5: bool,
    keyword: str,
    limit: int,
):
    kw = keyword.lower()
    q_table = f'"{table}"'
    q_name = f'"{name_col}"'
    q_dl = f'"{dl_col}"'

    def run_like():
        escaped = kw.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
        sql = f"SELECT {q_name}, {q_dl} FROM {q_table} WHERE {q_name} LIKE ? ESCAPE '\\'"
        return con.execute(sql, (f"%{escaped}%",))

    cur = None
    if is_fts5 and len(kw) >= TRIGRAM_MIN:
        fts_query = '"' + kw.replace('"', '""') + '"'
        sql = f"SELECT {q_name}, {q_dl} FROM {q_table} WHERE {q_name} MATCH ?"
        try:
            cur = con.execute(sql, (fts_query,))
        except sqlite3.OperationalError:
            cur = run_like()
    else:
        cur = run_like()
    return heapq.nlargest(limit, cur, key=lambda r: r[1])


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Search PyPI packages by substring (SQLite FTS5 trigram).",
    )
    ap.add_argument("keyword", nargs="?", help="substring to search for (case-insensitive)")
    ap.add_argument(
        "-n",
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"max results (default: {DEFAULT_LIMIT})",
    )
    args = ap.parse_args()
    if not DB_PATH.exists():
        sys.exit(f"Index not found: {DB_PATH}")
    keyword = args.keyword
    if not keyword:
        keyword = input("Search package: ").strip()
        if not keyword:
            print("No keyword given.")
            return
    con = sqlite3.connect(str(DB_PATH))
    try:
        table, name_col, dl_col, is_fts5 = get_table_info(con)
        rows = search(con, table, name_col, dl_col, is_fts5, keyword, args.limit)
    finally:
        con.close()
    if not rows:
        print(f"No matches for '{keyword}'.")
        return
    for name, dl in rows:
        print(f"{name}  {dl}")


if __name__ == "__main__":
    main()
