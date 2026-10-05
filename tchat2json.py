#!/data/data/com.termux/files/usr/bin/python3.12
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
