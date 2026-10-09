#!/data/data/com.termux/files/usr/bin/python

from __future__ import annotations
import argparse
import json
from pathlib import Path
import pickle
import sys
from typing import Any


def sanitize_for_json(obj: Any) -> Any:
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, set):
        return [sanitize_for_json(item) for item in obj]
    return str(obj)


def load_pickle(path: Path) -> Any:
    with open(path, "rb") as f:
        return pickle.load(f)


def cmd_json(args: argparse.Namespace) -> None:
    input_path = Path(args.path)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    if input_path.suffix != ".pkl" and args.verbose:
        print(f"Warning: Expected .pkl file, got {input_path.suffix}")

    try:
        data = load_pickle(input_path)
    except Exception as e:
        print(f"Error loading pickle: {e}")
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".json")

    if args.verbose:
        print(f"✓ Loaded: {input_path}")
        print(f"  Type: {type(data).__name__}")
        print(f"  Size: {len(str(data))} chars\n")
        print("Content:")
        print("-" * 40)
        print(json.dumps(data, indent=args.indent, default=str))
        print("-" * 40)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=args.ensure_ascii, indent=args.indent)
        if args.verbose:
            print(f"\n✓ Saved to: {output_path}")
    except (TypeError, ValueError) as e:
        # Attempt fallback serialization if explicitly allowed or when sanitization flag is passed
        if args.sanitize:
            try:
                sanitized_data = sanitize_for_json(data)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(sanitized_data, f, ensure_ascii=args.ensure_ascii, indent=args.indent)
                if args.verbose:
                    print(f"\n⚠ Converted non-serializable objects → {output_path}")
            except Exception as err:
                print(f"\n✗ Cannot convert to JSON: {err}")
                sys.exit(1)
        else:
            print(f"Error converting to JSON: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Failed to save JSON: {e}")
        sys.exit(1)


def cmd_raw(args: argparse.Namespace) -> None:
    input_path = Path(args.path)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    try:
        data = load_pickle(input_path)
    except Exception as e:
        print(f"Error loading pickle: {e}")
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".raw")

    if isinstance(data, bytes):
        output_path.write_bytes(data)
    else:
        output_path.write_bytes(bytes(data))

    print(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified Pickle File Processor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    json_parser = subparsers.add_parser("json", help="Convert pickle file to JSON format")
    json_parser.add_argument("path", help="Path to input pickle file")
    json_parser.add_argument("-o", "--output", help="Custom output JSON path")
    json_parser.add_argument("-v", "--verbose", action="store_true", help="Print detailed metadata and preview")
    json_parser.add_argument("--sanitize", action="store_true", help="Sanitize non-serializable objects")
    json_parser.add_argument(
        "--no-ensure-ascii",
        dest="ensure_ascii",
        action="store_false",
        default=True,
        help="Allow non-ASCII characters in JSON output",
    )
    json_parser.add_argument("--indent", type=int, default=2, help="JSON indentation level")
    json_parser.set_defaults(func=cmd_json)

    raw_parser = subparsers.add_parser("raw", help="Unpack raw bytes from pickle file")
    raw_parser.add_argument("path", help="Path to input pickle file")
    raw_parser.add_argument("-o", "--output", help="Custom output raw file path")
    raw_parser.set_defaults(func=cmd_raw)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
