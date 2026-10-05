#!/data/data/com.termux/files/usr/bin/python3.12
"""Build a Termux-compatible Python 3.12 command-line script (shebang targeting `/data/data/com.termux/files/usr/bin/python3.12`) that parses plain-text chat log exports and converts them into structured data in JSON, CSV, or SQLite format.

Core requirements:

1. **Input parsing**: The script must read a chat log text file where each message line follows the format `[YYYY-MM-DD HH:MM:SS] username: message text`. Use a regular expression to match this pattern and extract the timestamp, username, and message content. Lines that do not match this pattern (continuation lines, e.g. multi-line messages) should be appended to the previous message's text (joined with a newline), but only if there is a prior message and the line is not blank/whitespace-only.

2. **Parsing function**: Implement a function that takes the raw chat text and returns a list of dictionaries, each containing `time`, `user` (stripped of whitespace), and `msg` (right-stripped) keys, preserving chronological order as they appear in the file.

3. **Grouping function**: Implement a function that groups parsed messages by user, producing a list of records (e.g., `{"user": ..., "msg": [...]}`). It must:
   - Preserve the order in which users first appear in the log.
   - Deduplicate messages per user (only keep unique message texts, preserving first-occurrence order within each user's list).

4. **Output writers**: Implement separate functions to export the grouped/aggregated records to:
   - **JSON**: pretty-printed (indent=2), UTF-8 encoded, with non-ASCII characters preserved (`ensure_ascii=False`).
   - **CSV**: using Python's `csv` module, writing to a file with UTF-8 encoding, accepting a configurable list of field names/columns.
   - **SQLite**: writing records into a database file (implementation should create/populate a table from the records).

5. **CLI interface**: Use `argparse` to accept command-line arguments, including at minimum: input chat log file path, output file path, and desired output format (json/csv/sqlite). Use `pathlib.Path` for file path handling and `sys` for exit/error handling as needed.

6. **Robustness**: Handle file reading/writing with proper encoding (UTF-8), and ensure the script can be run directly as an executable in a Termux Android environment.

The purpose of the script is to help users convert raw/plain-text chat export logs (such as from messaging apps) into clean, structured, de-duplicated, per-user message datasets in a format (JSON/CSV/SQLite) suitable for further analysis, archiving, or import into other tools.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/HFdxVZksciQREb8QZayNa3"""

import argparse
import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

# Regex matching a single chat line: "[timestamp] user: message"
LINE_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+(.*?):\s?(.*)$")


def parse_chat(text: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for line in text.splitlines():
        match = LINE_RE.match(line)
        if match:
            # Extract timestamp, user, and first line of the message
            time, user, msg = match.groups()
            messages.append({"time": time, "user": user.strip(), "msg": msg.rstrip()})
        elif messages and line.strip():
            # Continuation line: append to the previous message
            messages[-1]["msg"] += "\n" + line
    return messages


def group_by_user(messages: list[dict[str, str]]) -> list[dict[str, object]]:
    users: dict[str, list[str]] = {}
    order: list[str] = []
    for m in messages:
        u = m["user"]
        # Preserve first-seen ordering of users
        if u not in users:
            users[u] = []
            order.append(u)
        # Deduplicate messages per user
        if m["msg"] not in users[u]:
            users[u].append(m["msg"])
    return [{"user": u, "msg": users[u]} for u in order]


def write_json(records: list[dict[str, object]], dst: Path) -> None:
    dst.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(records: list[dict[str, object]], dst: Path, fields: list[str]) -> None:
    with dst.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            row = dict(r)
            # Serialize list-valued cells as JSON strings
            if isinstance(row.get("msg"), list):
                row["msg"] = json.dumps(row["msg"], ensure_ascii=False)
            writer.writerow(row)


def write_db(records: list[dict[str, object]], dst: Path, fields: list[str]) -> None:
    conn = sqlite3.connect(dst)
    cur = conn.cursor()
    # Create a messages table with all columns as TEXT
    cols = ", ".join(f"{f} TEXT" for f in fields)
    cur.execute(f"CREATE TABLE messages ({cols})")
    placeholders = ", ".join(f":{f}" for f in fields)
    rows = []
    for r in records:
        row = dict(r)
        # Serialize list-valued cells as JSON strings
        if isinstance(row.get("msg"), list):
            row["msg"] = json.dumps(row["msg"], ensure_ascii=False)
        rows.append(row)
    cur.executemany(f"INSERT INTO messages ({', '.join(fields)}) VALUES ({placeholders})", rows)
    conn.commit()
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    # Accept zero or more input files
    parser.add_argument("input", nargs="*", type=Path)
    parser.add_argument("-t", "--time", action="store_true")
    parser.add_argument("-o", "--output", choices=["json", "csv", "db"], default="json")
    # Merge is enabled by default; no flag needed to turn it on
    parser.add_argument("-m", "--merge", action="store_true", default=True)
    # Remove the original input file after a successful conversion
    parser.add_argument("-r", "--remove", action="store_true")
    args = parser.parse_args()
    # Determine input files: explicit args or all .txt in current directory
    if args.input:
        srcs = list(args.input)
    else:
        srcs = sorted(Path.cwd().glob("*.txt"))
        if not srcs:
            sys.exit("error: no .txt files found in current directory")
    # Validate all inputs before processing
    for src in srcs:
        if not src.is_file():
            sys.exit(f"error: file not found: {src}")
    # Process each input file
    for src in srcs:
        messages = parse_chat(src.read_text(encoding="utf-8"))
        # Drop placeholder messages with no real content
        messages = [m for m in messages if m["msg"].strip() != "[No Text/Media]"]
        if args.merge:
            # Group all messages per user (default behavior)
            records: list[dict[str, object]] = group_by_user(messages)
            fields = ["user", "msg"]
        else:
            # Flat mode: optionally keep timestamps
            if not args.time:
                for m in messages:
                    m.pop("time", None)
            records = messages
            fields = ["time", "user", "msg"] if args.time else ["user", "msg"]
        ext = {"json": ".json", "csv": ".csv", "db": ".db"}[args.output]
        dst: Path = src.with_suffix(ext)
        if args.output == "json":
            write_json(records, dst)
        elif args.output == "csv":
            write_csv(records, dst, fields)
        else:
            write_db(records, dst, fields)
        print(f"Parsed {len(records)} records -> {dst}")
        # Delete the original input text file if requested
        if args.remove:
            src.unlink()
            print(f"Removed original file: {src}")


if __name__ == "__main__":
    main()
