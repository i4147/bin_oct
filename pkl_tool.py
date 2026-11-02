#!/data/data/com.termux/files/usr/bin/env python
"""Convert/inspect pickle files (to JSON, repr, or raw bytes).

Analysis / deduplication
------------------------
- ``pkl2json.py`` (bare ``json.dump``, dies on sets/bytes/dates) and
  ``pkltojson.py`` (recursive serializer with type tagging) are one
  ``to-json`` command; the smarter serializer is the only engine now
  (previously unhandled objects degrade to ``{"__type__", "repr"}``
  instead of crashing the conversion).
- ``upkl.py`` loaded a pickle and wrote it as ``.raw`` bytes; it
  called ``pkl.load`` although only ``pickle`` was imported, so it
  crashed on every run. It is now ``inspect`` (type/size/repr) and
  ``to-raw`` (bytes payloads written verbatim).

SECURITY: unpickling executes code. Only run this on pickles you
trust - every subcommand prints a reminder on stderr.

Examples
--------
  python3 pickle_tool.py to-json data.pkl
  python3 pickle_tool.py inspect data.pkl --max-repr 2000
  python3 pickle_tool.py to-raw blob.pkl -o blob.bin
"""

import argparse
import base64
import datetime
import json
import pickle
import sys
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

JSON_NATIVE: tuple[type, ...] = (str, int, float, bool, type(None))


def warn_unpickle(path: Path) -> None:
    """Remind the user that unpickling is code execution."""
    print(f"warning: unpickling {path} executes embedded code - trusted files only!", file=sys.stderr)


def load_pickle(path: Path) -> object:
    """Unpickle one file (first object)."""
    warn_unpickle(path)
    with path.open("rb") as handle:
        return pickle.load(handle)


def serialize(obj: object) -> object:
    """Recursively convert *obj* into JSON-compatible data."""
    if isinstance(obj, JSON_NATIVE):
        return obj
    if isinstance(obj, dict):
        return {stringify_key(k): serialize(v) for k, v in obj.items()}  # type: ignore[arg-type]
    if isinstance(obj, (list, tuple)):
        return [serialize(item) for item in obj]  # type: ignore[arg-type]
    if isinstance(obj, (set, frozenset)):
        return {"__type__": type(obj).__name__, "items": [serialize(i) for i in obj]}  # type: ignore[arg-type]
    if isinstance(obj, (bytes, bytearray)):
        return {
            "__type__": "bytes",
            "base64": base64.b64encode(bytes(obj)).decode(),  # type: ignore[arg-type]
            "length": len(obj),
        }  # type: ignore[arg-type]
    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return {"__type__": type(obj).__name__, "iso": obj.isoformat()}  # type: ignore[attr-defined]
    if isinstance(obj, Path):
        return {"__type__": "Path", "value": str(obj)}
    if isinstance(obj, Decimal):
        return {"__type__": "Decimal", "value": str(obj)}
    if hasattr(obj, "__dict__"):
        return {"__type__": type(obj).__name__, "attrs": {str(k): serialize(v) for k, v in vars(obj).items()}}
    return {"__type__": type(obj).__name__, "repr": repr(obj)}


def stringify_key(key: object) -> str:
    """JSON object keys must be strings; tag exotic keys as ``type:value``."""
    if isinstance(key, str):
        return key
    if isinstance(key, (int, float, bool)) or key is None:
        return json.dumps(key)
    return f"{type(key).__name__}:{key!r}"


def cmd_to_json(args: argparse.Namespace) -> int:
    """Convert pickle file(s) to JSON."""
    for path in args.files:
        try:
            data: object = load_pickle(path)
        except Exception as exc:
            print(f"failed: {path}: {exc}", file=sys.stderr)
            return 1
        payload: object = serialize(data)
        text: str = json.dumps(payload, indent=args.indent, ensure_ascii=False) + "\n"
        if args.stdout:
            print(text, end="")
        else:
            dest: Path = args.output if args.output and len(args.files) == 1 else path.with_suffix(".json")
            dest.write_text(text, encoding="utf-8")
            print(f"{path} -> {dest}")
    return 0


def describe(obj: object, depth: int = 0, max_depth: int = 2) -> str:
    """Short structural summary of an unpickled object."""
    if isinstance(obj, dict):
        keys: list[object] = list(obj.keys())[:5]  # type: ignore[attr-defined]
        return f"dict(len={len(obj)}, keys={keys!r})"  # type: ignore[arg-type]
    if isinstance(obj, (list, tuple, set, frozenset)):
        return f"{type(obj).__name__}(len={len(obj)})"  # type: ignore[arg-type]
    if isinstance(obj, (bytes, bytearray)):
        return f"bytes(len={len(obj)})"  # type: ignore[arg-type]
    if isinstance(obj, str):
        return f"str(len={len(obj)})"
    return type(obj).__name__


def cmd_inspect(args: argparse.Namespace) -> int:
    """Print type/structure/repr of a pickle's payload."""
    obj: object = load_pickle(args.file)
    print(f"file:   {args.file} ({args.file.stat().st_size} bytes on disk)")
    print(f"type:   {type(obj).__module__}.{type(obj).__qualname__}")
    print(f"shape:  {describe(obj)}")
    text: str = repr(obj)
    if len(text) > args.max_repr:
        text = text[: args.max_repr] + f"... [truncated, {len(text)} chars total]"
    print(f"repr:   {text}")
    return 0


def cmd_to_raw(args: argparse.Namespace) -> int:
    """Write a bytes payload verbatim (or repr-encode anything else)."""
    obj: object = load_pickle(args.file)
    dest: Path = args.output or args.file.with_suffix(".raw")
    if isinstance(obj, (bytes, bytearray)):
        dest.write_bytes(bytes(obj))
        print(f"Wrote {len(obj)} raw byte(s) to {dest}")  # type: ignore[arg-type]
    elif args.force_repr:
        dest.write_text(repr(obj), encoding="utf-8")
        print(f"Wrote repr to {dest}")
    else:
        print(f"Payload is {describe(obj)}, not bytes. Use inspect/to-json, or --force-repr.", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(description="Pickle -> JSON / inspect / raw (trusted files only!).")
    sub = parser.add_subparsers(dest="command", required=True)
    tj = sub.add_parser("to-json", help="Convert .pkl to .json")
    tj.add_argument("files", nargs="+", type=Path)
    tj.add_argument("-o", "--output", type=Path, default=None, help="Single-file output")
    tj.add_argument("--indent", type=int, default=2)
    tj.add_argument("--stdout", action="store_true")
    tj.set_defaults(handler=cmd_to_json)
    ins = sub.add_parser("inspect", help="Describe a pickle's payload")
    ins.add_argument("file", type=Path)
    ins.add_argument("--max-repr", type=int, default=500)
    ins.set_defaults(handler=cmd_inspect)
    raw = sub.add_parser("to-raw", help="Write a bytes payload verbatim")
    raw.add_argument("file", type=Path)
    raw.add_argument("-o", "--output", type=Path, default=None, help="Default: <name>.raw")
    raw.add_argument("--force-repr", action="store_true", help="Non-bytes: write repr() as text")
    raw.set_defaults(handler=cmd_to_raw)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    args: argparse.Namespace = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    sys.exit(main())
