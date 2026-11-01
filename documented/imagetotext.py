#!/data/data/com.termux/files/usr/bin/env python
"""
Recursively extract English + Farsi + Russian text from images using Tesseract.
For each image, writes a sibling .txt file. Falls back to alternative PSM/OEM
configurations when the first OCR pass doesn't yield recognisable words.
"""

import re
from pathlib import Path
from multiprocessing import Pool

import pytesseract
from PIL import Image

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
TESSDATA = str(Path.home() / ".local" / "share" / "tessdata")
LANGS = "eng+fas+rus"
NUM_WORKERS = 4
OVERWRITE = False  # set True to re-OCR files that already have .txt

IMAGE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".gif",
    ".webp",
    ".pnm",
    ".ppm",
}

# (psm, oem) tried in order; stop at the first result that looks meaningful
CONFIGS = [
    (3, 3),  # fully automatic page segmentation, LSTM engine
    (1, 3),  # auto + orientation & script detection
    (4, 3),  # assume a single column of text
    (6, 3),  # assume a single uniform block of text
    (11, 3),  # sparse text
    (12, 3),  # sparse text + OSD
    (3, 1),  # legacy + LSTM fallback
    (6, 1),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
# Latin (a-z), Persian/Arabic (\u0600-\u06FF), Cyrillic (\u0400-\u04FF)
_LETTERS = r"A-Za-z\u0600-\u06FF\u0400-\u04FF"
_WORD_RE = re.compile(rf"[{_LETTERS}]{{2,}}")
_ALPHA_RE = re.compile(rf"[{_LETTERS}]")


def _is_meaningful(text: str) -> bool:
    """Heuristic: reject mostly-symbols/garbage output."""
    if not text:
        return False
    s = text.strip()
    if len(s) < 3:
        return False
    total = sum(1 for ch in s if not ch.isspace())
    if total < 3:
        return False
    alpha = len(_ALPHA_RE.findall(s))
    if alpha / total < 0.5:  # too many punctuation/digits → likely noise
        return False
    if not _WORD_RE.search(s):  # no real word of 2+ letters
        return False
    return True


def _ocr(img_path: Path, psm: int, oem: int) -> str:
    config = f'--oem {oem} --psm {psm} --tessdata-dir "{TESSDATA}"'
    with Image.open(img_path) as im:
        if im.mode not in ("L", "RGB"):
            im = im.convert("RGB")
        return pytesseract.image_to_string(im, lang=LANGS, config=config)


def process_image(img_path_str: str):
    img_path = Path(img_path_str)
    txt_path = img_path.with_suffix(".txt")

    if txt_path.exists() and not OVERWRITE:
        return str(img_path), "skipped"

    best, best_cfg = "", None
    for psm, oem in CONFIGS:
        try:
            text = _ocr(img_path, psm, oem)
            print(f"\npsm={psm} oem={oem}\n")
            print(f"\n{text}\n")
        except Exception:
            continue

        if _is_meaningful(text):
            best, best_cfg = text, (psm, oem)
            break
        if len(text) > len(best):
            best, best_cfg = text, (psm, oem)

    try:
        txt_path.write_text(best, encoding="utf-8")
    except Exception as e:
        return str(img_path), f"error writing txt: {e}"

    good = _is_meaningful(best)
    tag = "ok" if good else "fallback"
    if best_cfg:
        tag += f" (psm={best_cfg[0]},oem={best_cfg[1]})"
    return str(img_path), tag


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    root = Path(".")
    images = [str(p) for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS]

    print(f"Found {len(images)} image(s) under {root.resolve()}")
    if not images:
        return

    with Pool(processes=2) as pool:
        for img, status in pool.imap_unordered(process_image, images):
            print(f"[{status}] {img}")


if __name__ == "__main__":
    main()
