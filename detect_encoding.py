#!/data/data/com.termux/files/usr/bin/python
import sys
import json
import tokenize
from collections import Counter
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


def format_row(backend: str, encoding: str, confidence: str) -> str:
    """Formats a single row to fit standard terminal spacing parameters."""
    return f"║ {backend:<24} ║ {encoding:<18} ║ {confidence:<12} ║"


def normalize_encoding_name(name: str | None) -> str | None:
    """Normalizes variation in backend strings (e.g., 'UTF8', 'utf-8', 'UTF-8-SIG' -> 'utf-8')"""
    if not name:
        return None
    cleaned = name.strip().lower().replace("_", "-")
    if cleaned.startswith("utf-8"):
        return "utf-8"
    if cleaned == "utf8":
        return "utf-8"
    return cleaned


def run_diagnostic() -> None:
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
                "confidence": round(1.0 - match.chaos, 4) if match else 0.0,
            }
        except Exception as e:
            report["results"]["charset_normalizer"] = {"error": str(e)}
    else:
        report["results"]["charset_normalizer"] = {"status": "Not Installed"}

    # 4. cchardet
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
    report["results"]["unicodeit"] = {"status": "Skipped (LaTeX tool)"}

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

    # 8. compact_enc_det
    if ced:
        try:
            encoding = ced.default_detector.detect(raw_bytes)
            report["results"]["compact_enc_det"] = {"encoding": encoding, "confidence": None}
        except Exception as e:
            report["results"]["compact_enc_det"] = {"error": str(e)}
    else:
        report["results"]["compact_enc_det"] = {"status": "Not Installed"}

    # --- Consensus & Conflict Analysis Line ---
    valid_predictions = []
    unique_normalized_encodings = set()

    for data in report["results"].values():
        if "encoding" in data and data["encoding"]:
            norm_name = normalize_encoding_name(data["encoding"])
            if norm_name:
                valid_predictions.append(norm_name)
                unique_normalized_encodings.add(norm_name)

    # Calculate Consensus Parameters
    if valid_predictions:
        counts = Counter(valid_predictions)
        consensus_encoding, vote_count = counts.most_common(1)[0]
        consensus_percentage = (vote_count / len(valid_predictions)) * 100
        has_mismatch = len(unique_normalized_encodings) > 1
    else:
        consensus_encoding = "unknown"
        consensus_percentage = 0.0
        has_mismatch = False

    report["consensus"] = {
        "calculated_majority": consensus_encoding,
        "agreement_percentage": round(consensus_percentage, 2),
        "has_mismatch_conflict": has_mismatch,
    }

    # Save complete structural data payload to disk first
    output_report = Path("encoding_report.json")
    output_report.write_text(json.dumps(report, indent=4), encoding="utf-8")

    # Render clean terminal UI
    print(f"\nTarget File: {file_path.name} ({len(raw_bytes)} bytes)")
    print("╔" + "═" * 26 + "╦" + "═" * 20 + "╦" + "═" * 14 + "╗")
    print(format_row("Detection Backend", "Detected Encoding", "Confidence"))
    print("╠" + "═" * 26 + "╬" + "═" * 20 + "╬" + "═" * 14 + "╣")

    for backend_key, data in report["results"].items():
        if "error" in data:
            enc, conf = f"ERROR: {data['error'][:10]}", "N/A"
        elif "status" in data:
            enc, conf = data["status"], "N/A"
        else:
            enc = str(data.get("encoding") or "None")
            c_val = data.get("confidence")
            conf = f"{c_val:.4f}" if isinstance(c_val, (int, float)) else "N/A"

        print(format_row(backend_key, enc, conf))

    print("╚" + "═" * 26 + "╩" + "═" * 20 + "╩" + "═" * 14 + "╝")

    # Print the Consensus Status Block
    print(f"║ CONSENSUS MAJORITY : {consensus_encoding.upper()} ({consensus_percentage:.1f}% agreement)")
    if has_mismatch:
        print("║ WARNING            : ⚠️ Mismatch detected! Backends disagree on exact format configuration.")
    else:
        print("║ INTEGRITY STATUS   : ✅ Clean consensus match. All active backends agree.")
    print("╚" + "═" * 64)
    print(f"[+] Complete structural report logged to: {output_report.resolve()}")


if __name__ == "__main__":
    run_diagnostic()
