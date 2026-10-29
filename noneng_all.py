#!/data/data/com.termux/files/usr/bin/env python
"""
Language detection scanner with pluggable backends.

Usage:
    python langscan.py -b pycld2 .
    python langscan.py --backend lingua /path/to/dir
    python langscan.py -b fast_langdetect --only-non-english .
    python langscan.py -b langdetect .

Available backends (install the one you need):
    pycld2           -> pip install pycld2
    gcld3            -> pip install gcld3
    cld3             -> pip install cld3
    langdetect       -> pip install langdetect
    pylangid         -> pip install py3langid
    fast_langdetect  -> pip install fast-langdetect
    lingua           -> pip install lingua-language-detector
"""

import os
import sys
import math
import argparse
from typing import Callable, Tuple

DetectionResult = Tuple[str, float]  # (lang_code, probability in [0,1])


# --- Backend implementations -------------------------------------------------
# Each function lazy-imports its library so a missing package only breaks
# that specific backend, not the whole program.


def _detect_pycld2(text: str) -> DetectionResult:
    import pycld2 as cld2

    _, _, details = cld2.detect(text)
    if not details:
        return "unknown", 0.0
    # details[i] = (name, code, percent_int, score)
    _name, code, percent, _score = details[0]
    return code, percent / 100.0


_gcld3_detector = None


def _detect_gcld3(text: str) -> DetectionResult:
    global _gcld3_detector
    if _gcld3_detector is None:
        import gcld3

        _gcld3_detector = gcld3.NNetLanguageIdentifier(min_num_bytes=0, max_num_bytes=1000)
    result = _gcld3_detector.FindLanguage(text=text)
    return result.language, float(result.probability)


def _detect_cld3(text: str) -> DetectionResult:
    import cld3

    result = cld3.get_language(text)
    if result is None:
        return "unknown", 0.0
    return result.language, float(result.probability)


def _detect_langdetect(text: str) -> DetectionResult:
    from langdetect import detect_langs, DetectorFactory

    DetectorFactory.seed = 0  # deterministic output
    results = detect_langs(text)
    if not results:
        return "unknown", 0.0
    top = results[0]
    return top.lang, float(top.prob)


def _detect_pylangid(text: str) -> DetectionResult:
    # `py3langid` installs the `langid` module name
    import langid

    rankings = langid.rank(text)  # [(lang, log_score), ...] sorted desc
    if not rankings:
        return "unknown", 0.0
    top_lang, top_score = rankings[0]
    # Softmax over the top-K candidates to turn log-scores into probabilities
    top_k = rankings[:10]
    max_s = top_k[0][1]
    total = sum(math.exp(s - max_s) for _, s in top_k)
    prob = math.exp(top_score - max_s) / total if total else 0.0
    return top_lang, float(prob)


def _detect_fast_langdetect(text: str) -> DetectionResult:
    from fast_langdetect import detect

    result = detect(text)
    # Different versions return either a dict or a list of dicts
    if isinstance(result, dict):
        return result.get("lang", "unknown").lower(), float(result.get("score", 0.0))
    if isinstance(result, list) and result:
        return result[0].get("lang", "unknown").lower(), float(result[0].get("score", 0.0))
    return "unknown", 0.0


_lingua_detector = None


def _detect_lingua(text: str) -> DetectionResult:
    global _lingua_detector
    if _lingua_detector is None:
        from lingua import LanguageDetectorBuilder

        # NOTE: from_all_languages() loads all models (~few seconds startup).
        # For speed, restrict with: .from_languages(Language.ENGLISH, Language.FRENCH, ...)
        _lingua_detector = LanguageDetectorBuilder.from_all_languages().build()
    confidences = _lingua_detector.compute_language_confidence_values(text)
    if not confidences:
        return "unknown", 0.0
    top_lang, top_conf = confidences[0]
    return top_lang.iso_code_639_1.name.lower(), float(top_conf)


BACKENDS: dict[str, Callable[[str], DetectionResult]] = {
    "pycld2": _detect_pycld2,
    "gcld3": _detect_gcld3,
    "cld3": _detect_cld3,
    "langdetect": _detect_langdetect,
    "pylangid": _detect_pylangid,
    "fast_langdetect": _detect_fast_langdetect,
    "lingua": _detect_lingua,
}

INSTALL_HINT = {
    "pycld2": "pycld2",
    "gcld3": "gcld3",
    "cld3": "cld3",
    "langdetect": "langdetect",
    "pylangid": "py3langid",
    "fast_langdetect": "fast-langdetect",
    "lingua": "lingua-language-detector",
}


def detect_language(text: str, backend: str) -> DetectionResult:
    try:
        return BACKENDS[backend](text)
    except Exception as e:
        return f"error", float("nan")


# --- Scanner ----------------------------------------------------------------


def scan_and_detect(root_dir: str, backend: str, only_non_english: bool) -> None:
    print(f"Backend : {backend}", flush=True)
    print(f"Scanning: {os.path.abspath(root_dir)}\n", flush=True)
    print(f"{'File Path':<50} | {'Lang':<10} | {'Conf':<6} | Snippet", flush=True)
    print("-" * 120, flush=True)

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for file in files:
            if file.startswith("."):
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
            except Exception:
                continue
            if not content:
                continue

            lang, prob = detect_language(content, backend)

            if only_non_english and lang == "en":
                continue

            snippet = content[:40].replace("\n", " ") + ("..." if len(content) > 40 else "")
            conf_str = "  n/a" if math.isnan(prob) else f"{prob:>5.0%}"
            print(f"{file_path:<50} | {lang:<10} | {conf_str:<6} | {snippet}", flush=True)


# --- Entry point ------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Scan a directory and detect the language of each file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("root", nargs="?", default=".", help="Root directory to scan (default: .)")
    parser.add_argument(
        "-b", "--backend", choices=list(BACKENDS), default="pycld2", help="Language detection backend (default: pycld2)"
    )
    parser.add_argument("--only-non-english", action="store_true", help="Only print files detected as non-English")
    args = parser.parse_args()

    # Pre-flight: verify the chosen backend is usable before walking the tree
    try:
        detect_language("hello world", args.backend)
    except ImportError as e:
        pkg = INSTALL_HINT.get(args.backend, args.backend)
        print(f"ERROR: backend '{args.backend}' is not available: {e}", file=sys.stderr)
        print(f"       Install with:  pip install {pkg}", file=sys.stderr)
        sys.exit(1)

    scan_and_detect(args.root, args.backend, args.only_non_english)


if __name__ == "__main__":
    main()
