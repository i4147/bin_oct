#!/data/data/com.termux/files/usr/bin/python3.12
# transliterate_names.py: rename non-ASCII file/dir names to ASCII, in place, recursively.
#
# Install : pip install pypinyin pykakasi unidecode   (unidecode is only a fallback)
# Usage   : python transliterate_names.py              (current dir, renames for real)
#           python transliterate_names.py -n           (dry run: print the plan only)
#           python transliterate_names.py some/dir     (a different root)
#
# Languages / methods
#   Russian  : built-in table (BGN/PCGN-style, e.g. ж->zh, щ->shch). Ukrainian/Belarusian letters included.
#   Persian  : built-in table; short vowels are not written in Persian, so output is a
#              consonant skeleton (e.g. فایل -> fayl). Diacritics removed; Persian/Arabic digits -> 0-9.
#   Chinese  : pypinyin, toneless, syllables joined with "_" (文件 -> wen_jian).
#   Japanese : pykakasi, Hepburn (ファイル -> fairu). Any name containing kana is treated as
#              Japanese so kanji get Japanese readings; Han-only names are treated as Chinese.
#   Anything else non-ASCII (accents, Greek, emoji...): unidecode if installed, else accents are
#   stripped and the remaining characters become "_".
import argparse
import re
import sys
import unicodedata
from pathlib import Path

try:
    from pypinyin import lazy_pinyin
except ImportError:
    lazy_pinyin = None
try:
    import pykakasi

    _KAKASI = pykakasi.kakasi()
except ImportError:
    _KAKASI = None
try:
    from unidecode import unidecode
except ImportError:
    unidecode = None
# VCS metadata is never touched: renaming inside it can corrupt a repository.
SKIP_DIRS = frozenset({".git", ".hg", ".svn"})
MAX_NAME = 255  # most filesystems cap a single name at 255 bytes (output is ASCII, so chars == bytes)
# Script detectors (run after NFKC, so half-width kana are already full-width).
KANA = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff]")
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002ebef]+")
FA_MARKS = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")  # harakat / Quranic marks
_RU = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    "і": "i",
    "ї": "yi",
    "є": "ye",
    "ґ": "g",
    "ў": "u",
}
# Both cases in one table; capitals become "Zh", "Shch", ... so "Жуков" -> "Zhukov".
RU_TABLE = {}
for _k, _v in _RU.items():
    RU_TABLE[ord(_k)] = _v
    RU_TABLE[ord(_k.upper())] = _v.capitalize()
_FA = {
    "ا": "a",
    "آ": "a",
    "أ": "a",
    "إ": "e",
    "ء": "",
    "ئ": "",
    "ؤ": "",
    "ب": "b",
    "پ": "p",
    "ت": "t",
    "ث": "s",
    "ج": "j",
    "چ": "ch",
    "ح": "h",
    "خ": "kh",
    "د": "d",
    "ذ": "z",
    "ر": "r",
    "ز": "z",
    "ژ": "zh",
    "س": "s",
    "ش": "sh",
    "ص": "s",
    "ض": "z",
    "ط": "t",
    "ظ": "z",
    "ع": "",
    "غ": "gh",
    "ف": "f",
    "ق": "gh",
    "ک": "k",
    "ك": "k",
    "گ": "g",
    "ل": "l",
    "م": "m",
    "ن": "n",
    "و": "v",
    "ه": "h",
    "ة": "h",
    "ی": "y",
    "ي": "y",
    "ى": "y",
    "\u200c": "_",  # ZWNJ is a word-internal separator in Persian ("می‌خواهم")
    "\u200d": "",
    "\u0640": "",  # ZWJ, tatweel
    "،": ",",
    "؛": ";",
    "؟": "",
}
for _i in range(10):
    _FA[chr(0x06F0 + _i)] = str(_i)  # Persian digits
    _FA[chr(0x0660 + _i)] = str(_i)  # Arabic-Indic digits
FA_TABLE = {ord(k): v for k, v in _FA.items()}
# Characters illegal on at least one major filesystem, plus control characters.
BAD_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
# Windows device names are invalid as file names (with or without extension).
RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def _japanese(text: str) -> str:
    # Whole-string conversion keeps kanji readings context-aware; ASCII tokens pass through as-is.
    parts = []
    for item in _KAKASI.convert(text):
        orig = item["orig"]
        parts.append(orig if orig.isascii() else item["hepburn"] + "_")
    return "".join(parts)


def _chinese(text: str) -> str:
    # Only Han runs are converted; padding "_" is tidied up later.
    return HAN.sub(lambda m: "_" + "_".join(lazy_pinyin(m.group())) + "_", text)


def _ascii_fallback(text: str) -> str:
    if unidecode:
        return unidecode(text)
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c if c.isascii() else "_" for c in decomposed if not unicodedata.combining(c))


def _clean(name: str, original: str) -> str:
    name = BAD_CHARS.sub("_", name)
    name = re.sub(r"_{2,}", "_", name)  # collapse separator runs
    name = re.sub(r"\s{2,}", " ", name)
    name = re.sub(r"_+(?=\.)", "", name)  # "wen_jian_.txt" -> "wen_jian.txt"
    # Strip edge underscores only if the transliteration introduced them.
    if not original.startswith("_"):
        name = name.lstrip("_")
    if not original.endswith("_"):
        name = name.rstrip("_")
    name = name.rstrip(" .")  # trailing space/dot is invalid on Windows
    if not name:
        name = "unnamed"
    if name.split(".")[0].upper() in RESERVED:
        name = "_" + name
    if len(name) > MAX_NAME:  # transliteration can expand names a lot (1 Han -> ~7 chars)
        suffix = Path(name).suffix[:20]
        name = name[: MAX_NAME - len(suffix)] + suffix
    return name


def transliterate(name: str) -> str:
    # NFKC: composes macOS NFD names, folds full-width forms and Arabic presentation forms.
    text = unicodedata.normalize("NFKC", name)
    text = FA_MARKS.sub("", text)
    if KANA.search(text) and _KAKASI:
        text = _japanese(text)
    elif HAN.search(text) and lazy_pinyin:
        text = _chinese(text)
    text = text.translate(RU_TABLE).translate(FA_TABLE)
    text = _ascii_fallback(text)  # whatever is still non-ASCII
    return _clean(text, name)


def _key(path: Path) -> str:
    return str(path).casefold()  # case-insensitive filesystems (Windows/macOS)


def unique_target(path: Path, claimed: set) -> Path:
    # is_symlink() catches broken links, which exists() reports as missing.
    def free(p: Path) -> bool:
        return _key(p) not in claimed and not p.exists() and not p.is_symlink()

    if free(path):
        return path
    n = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{n}{path.suffix}")
        if free(candidate):
            return candidate
        n += 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Transliterate non-ASCII file/dir names in place.")
    parser.add_argument("root", nargs="?", default=".", type=Path)
    parser.add_argument("-n", "--dry-run", action="store_true", help="show renames without doing them")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):  # non-UTF-8 consoles must not crash on printing old names
        sys.stdout.reconfigure(errors="backslashreplace")
        sys.stderr.reconfigure(errors="backslashreplace")
    for lib, label in ((lazy_pinyin, "pypinyin (Chinese)"), (_KAKASI, "pykakasi (Japanese)")):
        if lib is None:
            print(f"warning: {label} not installed; falling back to a rougher conversion", file=sys.stderr)
    root = args.root.resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 1
    entries = [p for p in root.rglob("*") if not SKIP_DIRS.intersection(p.relative_to(root).parts)]
    # Deepest first: children are renamed before their parents, so every collected path stays valid.
    entries.sort(key=lambda p: len(p.parts), reverse=True)
    claimed: set = set()  # targets already taken (matters for dry runs and collisions)
    renamed = failed = 0
    for old in entries:
        if old.name.isascii():
            continue
        new_name = transliterate(old.name)
        if new_name == old.name:
            continue
        new = unique_target(old.with_name(new_name), claimed)
        claimed.add(_key(new))
        print(f"{old.relative_to(root)}  ->  {new.name}")
        if args.dry_run:
            renamed += 1
            continue
        try:
            old.rename(new)
            renamed += 1
        except OSError as exc:  # permissions, in-use files, etc.: report and continue
            failed += 1
            print(f"  error: {exc}", file=sys.stderr)
    verb = "would rename" if args.dry_run else "renamed"
    print(f"\n{verb} {renamed} item(s), {failed} error(s).")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
