#!/data/data/com.termux/files/usr/bin/python
"""Read QR/barcodes from images (and optionally generate QR codes).

Analysis / deduplication
------------------------
``qrcode_reader.py`` and ``qrcoder.py`` are functionally identical:
both open an image with Pillow and decode it with pyzbar. The only
real differences - the reader prints type/position and every code,
``qrcoder`` keeps only ``QRCODE`` symbols - are now ``--verbose`` and
``--qr-only``. A ``make`` subcommand (via the optional ``qrcode``
package) was added since a read-only "qrcode_tools" folder begs for
its inverse; decoding prefers pyzbar and falls back to OpenCV's
``QRCodeDetector`` when pyzbar/zbar is unavailable.

Needs Pillow + (pyzbar or opencv-python); pyzbar needs the system
``zbar`` library (``apt install libzbar0``).

Examples
--------
  python3 qrcode_tool.py read code.png
  python3 qrcode_tool.py read photos/ --data-only
  python3 qrcode_tool.py make "https://example.com" -o code.png
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class DecodedCode:
    """One decoded symbol."""

    data: str
    kind: str
    position: str = ""


def decode_with_pyzbar(image: object, qr_only: bool) -> list[DecodedCode] | None:
    """Decode with pyzbar; None means "library unavailable"."""
    try:
        from pyzbar.pyzbar import decode
    except ImportError:
        return None
    results: list[DecodedCode] = []
    for symbol in decode(image):
        kind: str = str(symbol.type)
        if qr_only and kind != "QRCODE":
            continue
        rect = symbol.rect
        results.append(
            DecodedCode(
                data=symbol.data.decode("utf-8", errors="replace"),
                kind=kind,
                position=f"x={rect.left} y={rect.top} w={rect.width} h={rect.height}",
            )
        )
    return results


def decode_with_opencv(path: Path) -> list[DecodedCode] | None:
    """Decode a single QR code with OpenCV; None = unavailable."""
    try:
        import cv2
    except ImportError:
        return None
    image = cv2.imread(str(path))
    if image is None:
        return []
    detector = cv2.QRCodeDetector()
    data: str
    points: object
    data, points, _ = detector.detectAndDecode(image)
    if data:
        return [DecodedCode(data=data, kind="QRCODE", position=str(points))]
    multi_ok, infos = False, ()
    try:
        multi_ok, infos, _p, _s = detector.detectAndDecodeMulti(image)
    except Exception:
        pass
    if multi_ok:
        return [DecodedCode(data=str(d), kind="QRCODE") for d in infos if d]
    return []


def decode_image(path: Path, qr_only: bool) -> list[DecodedCode]:
    """Decode all codes in one image file."""
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Missing optional dependency: pip install Pillow pyzbar (+ apt libzbar0)") from None
    with Image.open(path) as img:
        rgb = img.convert("RGB")
        via_zbar: list[DecodedCode] | None = decode_with_pyzbar(rgb, qr_only)
    if via_zbar is not None:
        return via_zbar
    via_cv: list[DecodedCode] | None = decode_with_opencv(path)
    if via_cv is not None:
        return via_cv
    raise SystemExit("No decoder available: pip install pyzbar (+ libzbar0) or opencv-python")


def find_images(inputs: Sequence[Path]) -> list[Path]:
    """Collect image files from file/dir arguments."""
    suffixes: frozenset[str] = frozenset({".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"})
    found: list[Path] = []
    for root in inputs:
        if root.is_file():
            found.append(root)
        elif root.is_dir():
            found.extend(p for p in sorted(root.rglob("*")) if p.is_file() and p.suffix.lower() in suffixes)
    return found


def cmd_read(args: argparse.Namespace) -> int:
    """Decode QR/barcodes in image(s)."""
    images: list[Path] = find_images(args.images)
    if not images:
        print("No images found.", file=sys.stderr)
        return 1
    any_found: bool = False
    json_rows: list[dict[str, object]] = []
    for path in images:
        try:
            codes: list[DecodedCode] = decode_image(path, args.qr_only)
        except OSError as exc:
            print(f"Error: {path}: {exc}", file=sys.stderr)
            continue
        if codes:
            any_found = True
        if args.json:
            json_rows.append({"file": str(path), "codes": [asdict(c) for c in codes]})
            continue
        if args.data_only:
            for code in codes:
                print(code.data)
            continue
        if not codes:
            print(f"{path}: no code found")
            continue
        print(f"{path}: {len(codes)} code(s)")
        for index, code in enumerate(codes, start=1):
            print(f"  #{index} [{code.kind}] {code.data}")
            if args.verbose and code.position:
                print(f"      position: {code.position}")
    if args.json:
        print(json.dumps(json_rows, indent=2, ensure_ascii=False))
    return 0 if any_found else 1


def cmd_make(args: argparse.Namespace) -> int:
    """Generate a QR code PNG for the given data."""
    try:
        import qrcode
    except ImportError:
        print("Missing optional dependency: pip install qrcode", file=sys.stderr)
        return 1
    image: object = qrcode.make(args.data)
    if args.size is not None:
        image = image.resize((args.size, args.size))
    image.save(str(args.output))
    print(f"Wrote QR code to {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(description="Read (and make) QR codes.")
    sub = parser.add_subparsers(dest="command", required=True)
    rd = sub.add_parser("read", help="Decode codes in image file(s)/dir(s)")
    rd.add_argument("images", nargs="+", type=Path)
    rd.add_argument("--qr-only", action="store_true", help="Ignore non-QR barcodes (qrcoder)")
    rd.add_argument("--data-only", action="store_true", help="Print payloads only")
    rd.add_argument("--verbose", action="store_true", help="Also print symbol positions")
    rd.add_argument("--json", action="store_true", help="JSON output")
    rd.set_defaults(handler=cmd_read)
    mk = sub.add_parser("make", help="Generate a QR code image (needs qrcode pkg)")
    mk.add_argument("data")
    mk.add_argument("-o", "--output", type=Path, default=Path("qrcode.png"))
    mk.add_argument("--size", type=int, default=None, help="Force square pixel size")
    mk.set_defaults(handler=cmd_make)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args: argparse.Namespace = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    sys.exit(main())
