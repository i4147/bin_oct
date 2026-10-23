#!/data/data/com.termux/files/usr/bin/python
import sys
import json
import tokenize
from pathlib import Path

# Safe package imports to ensure script execution even if some packages are missing
try:
    import chardet
except ImportError:
    chardet = None

try:
    import charset_normalizer
except ImportError:
    charset_normalizer = None

try:
    import cchardet
except ImportError:
    cchardet = None

try:
    from bs4 import UnicodeDammit
except ImportError:
    UnicodeDammit = None

try:
    import magic
except ImportError:
    magic = None

try:
    import ced
except ImportError:
    ced = None


def run_diagnostic() -> None:
    if len(sys.argv) < 2:
        print("Error: Please provide an input file path.", file=sys.stderr)
        print("Usage: python script.py <path_to_file>", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.is_file():
        print(f"Error: File '{file_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Prepare raw bytes for 3rd-party consumers
    try:
        raw_bytes = file_path.read_bytes()
    except Exception as e:
        print(f"Critical Error: Could not read file bytes: {e}", file=sys.stderr)
        sys.exit(1)

    report = {"target_file": str(file_path), "file_size_bytes": len(raw_bytes), "results": {}}

    # 1. Standard Library (tokenize)
    try:
        with open(file_path, "rb") as f:
            encoding, _ = tokenize.detect_encoding(f.readline)
        report["results"]["stdlib_tokenize"] = {"encoding": encoding, "confidence": 1.0}
    except Exception as e:
        report["results"]["stdlib_tokenize"] = {"error": str(e)}

    # 2. chardet
    if chardet:
        try:
            res = chardet.detect(raw_bytes)
            report["results"]["chardet"] = {"encoding": res.get("encoding"), "confidence": res.get("confidence")}
        except Exception as e:
            report["results"]["chardet"] = {"error": str(e)}
    else:
        report["results"]["chardet"] = {"status": "Not Installed"}

    # 3. charset_normalizer
    if charset_normalizer:
        try:
            match = charset_normalizer.from_bytes(raw_bytes).best()
            report["results"]["charset_normalizer"] = {
                "encoding": match.encoding if match else None,
                "confidence": match.chaos if match else 0.0,  # chaos metric represents consistency
            }
        except Exception as e:
            report["results"]["charset_normalizer"] = {"error": str(e)}
    else:
        report["results"]["charset_normalizer"] = {"status": "Not Installed"}

    # 4. cchardet (or faust-cchardet)
    if cchardet:
        try:
            res = cchardet.detect(raw_bytes)
            report["results"]["cchardet"] = {"encoding": res.get("encoding"), "confidence": res.get("confidence")}
        except Exception as e:
            report["results"]["cchardet"] = {"error": str(e)}
    else:
        report["results"]["cchardet"] = {"status": "Not Installed"}

    # 5. bs4 (BeautifulSoup UnicodeDammit)
    if UnicodeDammit:
        try:
            dammit = UnicodeDammit(raw_bytes)
            report["results"]["bs4_unicode_dammit"] = {"encoding": dammit.original_encoding, "confidence": None}
        except Exception as e:
            report["results"]["bs4_unicode_dammit"] = {"error": str(e)}
    else:
        report["results"]["bs4_unicode_dammit"] = {"status": "Not Installed"}

    # 6. unicodeit (Clarification Note)
    report["results"]["unicodeit"] = {
        "status": "Skipped - Tool converts LaTeX math strings, does not detect file encodings"
    }

    # 7. python_magic
    if magic:
        try:
            mime = magic.Magic(mime_encoding=True)
            encoding = mime.from_file(str(file_path))
            report["results"]["python_magic"] = {"encoding": encoding, "confidence": None}
        except Exception as e:
            report["results"]["python_magic"] = {"error": str(e)}
    else:
        report["results"]["python_magic"] = {"status": "Not Installed"}

    # 8. compact_enc_det (CED bindings via pip install compact_enc_det)
    if ced:
        try:
            # Basic wrapper usage returns string name or reliable status
            encoding = ced.default_detector.detect(raw_bytes)
            report["results"]["compact_enc_det"] = {"encoding": encoding, "confidence": None}
        except Exception as e:
            report["results"]["compact_enc_det"] = {"error": str(e)}
    else:
        report["results"]["compact_enc_det"] = {"status": "Not Installed"}

    # Print live visual terminal output
    print(json.dumps(report, indent=2))

    # Save to disk as clean JSON format
    output_report = Path("encoding_report.json")
    output_report.write_text(json.dumps(report, indent=4), encoding="utf-8")
    print(f"\n[+] Diagnostic report written to: {output_report.resolve()}")


if __name__ == "__main__":
    run_diagnostic()
