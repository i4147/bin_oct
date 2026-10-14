#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that parses an exported group chat log file and converts it into a structured output file, grouping each participant's messages together. The tool should accept a path to a plain-text chat export as input, along with a desired output format (such as JSON, CSV, or a local SQLite database) and an output destination path provided via command-line arguments.
The script should read each line of the chat export, recognize timestamped entries in the form of a bracketed date and time followed by a username and message, and treat any subsequent non-empty lines without a timestamp as continuations of the previous message (preserving line breaks). Blank lines and malformed content before the first valid entry should be handled gracefully without crashing.
Once parsed, the messages should be organized by user, with each user's messages collected in the order they first appeared in the chat. Duplicate messages from the same user should be removed so each unique message appears only once per user. The final result should be a list of records, each containing a username and that user's list of unique messages.
The script should write this grouped data to the chosen output format: a formatted, human-readable JSON file preserving non-ASCII characters, a CSV file with one row per user and messages suitably joined or serialized, or a SQLite database table holding the same information. It should validate that the input file exists, report clear error messages for missing files or unsupported formats, and print a concise summary (such as the number of users and messages processed) upon successful completion. Ensure the script can be run directly from the command line and handles file encoding issues robustly.
---"""

from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import re
import sqlite3
import sys

LINE_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+(.*?):\s?(.*)$")


def parse_chat(text: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for line in text.splitlines():
        match = LINE_RE.match(line)
        if match:
            time, user, msg = match.groups()
            messages.append({"time": time, "user": user.strip(), "msg": msg.rstrip()})
        elif messages and line.strip():
            messages[-1]["msg"] += "\n" + line
    return messages


def group_by_user(messages: list[dict[str, str]]) -> list[dict[str, object]]:
    users: dict[str, list[str]] = {}
    order: list[str] = []
    for m in messages:
        u = m["user"]
        if u not in users:
            users[u] = []
            order.append(u)
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
            if isinstance(row.get("msg"), list):
                row["msg"] = json.dumps(row["msg"], ensure_ascii=False)
            writer.writerow(row)


def write_db(records: list[dict[str, object]], dst: Path, fields: list[str]) -> None:
    conn = sqlite3.connect(dst)
    cur = conn.cursor()
    cols = ", ".join(f"{f} TEXT" for f in fields)
    cur.execute(f"CREATE TABLE messages ({cols})")
    placeholders = ", ".join(f":{f}" for f in fields)
    rows = []
    for r in records:
        row = dict(r)
        if isinstance(row.get("msg"), list):
            row["msg"] = json.dumps(row["msg"], ensure_ascii=False)
        rows.append(row)
    cur.executemany(f"INSERT INTO messages ({', '.join(fields)}) VALUES ({placeholders})", rows)
    conn.commit()
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="*", type=Path)
    parser.add_argument("-t", "--time", action="store_true")
    parser.add_argument("-o", "--output", choices=["json", "csv", "db"], default="json")
    parser.add_argument("-m", "--merge", action="store_true", default=True)
    parser.add_argument("-r", "--remove", action="store_true")
    args = parser.parse_args()
    if args.input:
        srcs = list(args.input)
    else:
        srcs = sorted(Path.cwd().glob("*.txt"))
        if not srcs:
            sys.exit("error: no .txt files found in current directory")
    for src in srcs:
        if not src.is_file():
            sys.exit(f"error: file not found: {src}")
    for src in srcs:
        messages = parse_chat(src.read_text(encoding="utf-8"))
        messages = [m for m in messages if m["msg"].strip() != "[No Text/Media]"]
        if args.merge:
            records: list[dict[str, object]] = group_by_user(messages)
            fields = ["user", "msg"]
        else:
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
        if args.remove:
            src.unlink()
            print(f"Removed original file: {src}")


if __name__ == "__main__":
    main()
