#!/data/data/com.termux/files/usr/bin/python
import sys
from pathlib import Path
import chardet
import charset_normalizer


def get_file_encoding() -> None:
    if len(sys.argv) < 2:
        print("Error: Please provide an input file path.", file=sys.stderr)
        print("Usage: python script.py <path_to_file>", file=sys.stderr)
        sys.exit(1)
    file_path = Path(sys.argv[1])
    if not file_path.is_file():
        print(f"Error: File '{file_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    try:
        raw_bytes = file_path.read_bytes()
        if not raw_bytes:
            print("utf-8")  # Default for empty files
            return
        # 1. Primary Backend: chardet
        chardet_result = chardet.detect(raw_bytes)
        encoding = chardet_result.get("encoding")
        confidence = chardet_result.get("confidence") or 0.0
        # Fallback if chardet returns nothing or has exceptionally low confidence
        if not encoding or confidence < 0.5:
            # 2. Fallback Backend: charset-normalizer
            normalizer_result = charset_normalizer.from_bytes(raw_bytes).best()
            if normalizer_result:
                encoding = normalizer_result.encoding
        # Final print out or ultimate safe fallback
        print(encoding if encoding else "utf-8")
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    get_file_encoding()
