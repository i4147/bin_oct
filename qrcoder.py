#!/data/data/com.termux/files/usr/bin/python
"""
Unified QR Code Reader and Extractor.

Usage Examples:
    python merged.py read qrcode.png      # Original qrcode_reader.py behavior (metadata + first result)
    python merged.py extract qrcode.png   # Original qrcoder.py behavior (RGB conversion + list format)
"""

from __future__ import annotations
import argparse
import os
from pathlib import Path
import sys
from typing import Any, List

from PIL import Image
from pyzbar import pyzbar


def decode_image(image_path: str, convert_rgb: bool = False) -> list[Any]:
    with Image.open(image_path) as img:
        # Some barcodes/QR codes fail to read if not converted to standard RGB space
        if convert_rgb and img.mode != "RGB":
            img = img.convert("RGB")
        return pyzbar.decode(img)


def cmd_read(args: argparse.Namespace) -> None:
    print(f"Reading QR code from: {args.image_path}\n")

    try:
        decoded = decode_image(args.image_path, convert_rgb=False)
    except FileNotFoundError:
        print(f"Error: Image file '{args.image_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing image: {e}")
        sys.exit(1)

    if not decoded:
        print("No QR code found in the image.")
        return

    print(f"Found {len(decoded)} QR code(s):\n")
    results = []

    for i, item in enumerate(decoded, 1):
        data = item.data.decode("utf-8")
        rect = item.rect
        print(f"QR Code {i}:")
        print(f"  Data: {data}")
        print(f"  Type: {item.type}")
        print(f"  Position: (left={rect.left}, top={rect.top}, width={rect.width}, height={rect.height})\n")
        results.append(data)

    if results:
        print("First QR code data only:")
        print(results[0])


def cmd_extract(args: argparse.Namespace) -> None:
    if not os.path.exists(args.image_path):
        print(f"Error: File '{args.image_path}' not found.")
        sys.exit(1)

    try:
        decoded = decode_image(args.image_path, convert_rgb=True)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        decoded = []

    results = [item.data.decode("utf-8") for item in decoded if item.type == "QRCODE"]

    if results:
        print(f"\nFound {len(results)} QR code(s):")
        print("-" * 40)
        for i, data in enumerate(results, 1):
            print(f"QR #{i}: {data}")
        print("-" * 40)
    else:
        print("No QR codes found in the image.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified QR Code Reader and Extractor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_read = subparsers.add_parser("read", help="Read all barcodes with detailed metadata")
    parser_read.add_argument("image_path", help="Path to the image file")
    parser_read.set_defaults(func=cmd_read)

    parser_extract = subparsers.add_parser("extract", help="Extract strictly QR codes with dashed formatting")
    parser_extract.add_argument("image_path", help="Path to the image file")
    parser_extract.set_defaults(func=cmd_extract)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
