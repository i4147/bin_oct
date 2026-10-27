#!/data/data/com.termux/files/usr/bin/python
from pathlib import Path
import sys
from PIL import Image
from pyzbar import pyzbar


def process_qrcode(path):
    try:
        with Image.open(path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            decoded = pyzbar.decode(img)
            results = []
            for i, obj in enumerate(decoded_objects, 1):
                data = obj.data.decode("utf-8")
                rect = obj.rect
                print(f"QR Code {i}:")
                print(f"  Data: {data}")
                print(f"  Type: {obj.type}")
                print(f"  Position: (left={rect.left}, top={rect.top}, width={rect.width}, height={rect.height})")
                print()
                results.append(data)
            return results
    except FileNotFoundError:
        sys.exit(1)
    except Exception as e:
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python qr_extractor.py <path_to_qrcode_image>")
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: File '{path}' not found.")
        sys.exit(1)
    results = process_qrcode(path)
    if results:
        for i, data in enumerate(results, 1):
            print(f"QR #{i}: {data}")
        print("-" * 40)
    else:
        print("No QR codes found.")


if __name__ == "__main__":
    raise SystemExit(main())
