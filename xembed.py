#!/data/data/com.termux/files/usr/bin/python
import argparse
import base64
import binascii
import hashlib
import json
import mimetypes
import sys
from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import quote
import re

PATTERN: re.Pattern[str] = re.compile(
    r"(?<![A-Za-z0-9_-])data:(?P<mime>[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+)?"
    r"(?P<params>(?:;[A-Za-z0-9.+=_-]+)*?);base64,"
    r"(?P<data>[A-Za-z0-9+/_-]+={0,2})"
)

MIME_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/svg+xml": ".svg",
    "image/x-icon": ".ico",
    "image/vnd.microsoft.icon": ".ico",
    "text/plain": ".txt",
    "font/woff2": ".woff2",
    "font/woff": ".woff",
    "font/ttf": ".ttf",
    "font/otf": ".otf",
    "application/font-woff": ".woff",
    "application/font-woff2": ".woff2",
    "application/x-font-ttf": ".ttf",
    "application/x-font-woff": ".woff",
    "application/vnd.ms-fontobject": ".eot",
    "application/octet-stream": "",
}

SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
    (b"%PDF-", ".pdf"),
    (b"wOF2", ".woff2"),
    (b"wOFF", ".woff"),
    (b"OTTO", ".otf"),
    (b"\x00\x01\x00\x00", ".ttf"),
    (b"\x00\x00\x01\x00", ".ico"),
)

DEFAULT_EXCLUDES: tuple[str, ...] = (".git", "node_modules", "__pycache__", ".venv", "venv")


@dataclass(slots=True)
class Options:
    root: Path
    assets: Path
    suffixes: frozenset[str]
    exclude: frozenset[str]
    min_size: int
    replace: bool
    backup: bool
    dry_run: bool
    manifest: bool


@dataclass(slots=True)
class ManifestEntry:
    mime: str
    size: int
    sources: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Stats:
    files_scanned: int = 0
    files_changed: int = 0
    found: int = 0
    saved: int = 0
    duplicates: int = 0
    skipped: int = 0
    manifest: dict[str, ManifestEntry] = field(default_factory=dict)


def decode_payload(raw: str) -> bytes | None:
    cleaned = raw.replace("-", "+").replace("_", "/")
    cleaned += "=" * (-len(cleaned) % 4)
    try:
        return base64.b64decode(cleaned, validate=True)
    except (binascii.Error, ValueError):
        return None


def sniff_extension(payload: bytes) -> str | None:
    for signature, ext in SIGNATURES:
        if payload.startswith(signature):
            return ext
    if payload[:4] == b"RIFF" and payload[8:12] == b"WEBP":
        return ".webp"
    head = payload[:512].lstrip().lower()
    if head.startswith(b"<svg") or (head.startswith(b"<?xml") and b"<svg" in head):
        return ".svg"
    return None


def resolve_extension(mime: str | None, payload: bytes) -> str:
    if mime:
        key = mime.lower()
        ext = MIME_EXT.get(key)
        if ext is None:
            ext = mimetypes.guess_extension(key, strict=False)
        if ext:
            return ext
    return sniff_extension(payload) or ".bin"


def iter_sources(opts: Options) -> Iterator[Path]:
    assets_resolved = opts.assets.resolve()
    for dirpath, dirnames, filenames in opts.root.walk():
        dirnames[:] = sorted(
            d for d in dirnames if d not in opts.exclude and (dirpath / d).resolve() != assets_resolved
        )
        for name in sorted(filenames):
            path = dirpath / name
            if path.suffix.lower() in opts.suffixes:
                yield path


def write_atomic(path: Path, data: bytes) -> None:
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def build_link(asset: Path, source: Path) -> str:
    relative = asset.resolve().relative_to(source.parent.resolve(), walk_up=True)
    return quote(relative.as_posix())


def process_file(path: Path, opts: Options, stats: Stats) -> None:
    original = path.read_bytes()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError:
        print(f"skip (not utf-8): {path}", file=sys.stderr)
        return
    stats.files_scanned += 1
    source_label = path.relative_to(opts.root).as_posix()

    def substitute(match: re.Match[str]) -> str:
        stats.found += 1
        payload = decode_payload(match["data"])
        if payload is None or len(payload) < opts.min_size:
            stats.skipped += 1
            return match.group(0)
        ext = resolve_extension(match["mime"], payload)
        name = f"{hashlib.sha256(payload).hexdigest()[:16]}{ext}"
        target = opts.assets / name
        entry = stats.manifest.get(name)
        if entry is None:
            entry = ManifestEntry(mime=match["mime"] or "", size=len(payload))
            stats.manifest[name] = entry
            if target.exists():
                stats.duplicates += 1
            else:
                stats.saved += 1
                if not opts.dry_run:
                    opts.assets.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(payload)
        else:
            stats.duplicates += 1
        if source_label not in entry.sources:
            entry.sources.append(source_label)
        if not opts.replace:
            return match.group(0)
        return build_link(target, path)

    updated = PATTERN.sub(substitute, text)
    if not opts.replace or updated == text:
        return
    stats.files_changed += 1
    if opts.dry_run:
        return
    if opts.backup:
        path.with_name(f"{path.name}.bak").write_bytes(original)
    write_atomic(path, updated.encode("utf-8"))


def write_manifest(opts: Options, stats: Stats) -> None:
    if not opts.manifest or opts.dry_run or not stats.manifest:
        return
    opts.assets.mkdir(parents=True, exist_ok=True)
    target = opts.assets / "manifest.json"
    merged: dict[str, dict[str, object]] = {}
    if target.exists():
        try:
            merged = json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            merged = {}
    for name, entry in stats.manifest.items():
        current = asdict(entry)
        previous = merged.get(name)
        if isinstance(previous, dict):
            known = previous.get("sources", [])
            current["sources"] = sorted({*known, *entry.sources})
        merged[name] = current
    target.write_text(json.dumps(merged, indent=2, sort_keys=True), encoding="utf-8")


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract embedded base64 data URIs from .html/.css files into an assets folder."
    )
    parser.add_argument(
        "-x",
        dest="replace",
        action="store_true",
        help="replace base64 strings in source files with links to extracted assets",
    )
    parser.add_argument("--root", type=Path, default=Path("."), help="directory to scan recursively")
    parser.add_argument(
        "--assets", type=Path, default=Path("assets"), help="output folder (relative paths are resolved against --root)"
    )
    parser.add_argument("--suffixes", nargs="+", default=[".html", ".css"], help="file suffixes to scan")
    parser.add_argument("--exclude", nargs="*", default=list(DEFAULT_EXCLUDES), help="directory names to skip")
    parser.add_argument("--min-size", type=int, default=0, help="ignore decoded objects smaller than this many bytes")
    parser.add_argument("--backup", action="store_true", help="write a .bak copy before modifying a file")
    parser.add_argument("--dry-run", action="store_true", help="report what would happen without writing anything")
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="write assets/manifest.json mapping files to mime type, size and sources",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root: Path = args.root.resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    assets: Path = args.assets if args.assets.is_absolute() else root / args.assets
    opts = Options(
        root=root,
        assets=assets,
        suffixes=frozenset(s if s.startswith(".") else f".{s}" for s in (x.lower() for x in args.suffixes)),
        exclude=frozenset(args.exclude),
        min_size=args.min_size,
        replace=args.replace,
        backup=args.backup,
        dry_run=args.dry_run,
        manifest=args.manifest,
    )
    stats = Stats()
    for path in iter_sources(opts):
        process_file(path, opts, stats)
    write_manifest(opts, stats)
    prefix = "[dry-run] " if opts.dry_run else ""
    print(f"{prefix}files scanned : {stats.files_scanned}")
    print(f"{prefix}base64 found  : {stats.found}")
    print(f"{prefix}assets saved  : {stats.saved}")
    print(f"{prefix}duplicates    : {stats.duplicates}")
    print(f"{prefix}skipped       : {stats.skipped}")
    if opts.replace:
        print(f"{prefix}files rewritten: {stats.files_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
