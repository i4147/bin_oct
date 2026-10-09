#!/data/data/com.termux/files/usr/bin/env python
"""Write a prompt for an AI coding agent to generate a Python 3 command-line script named `transliterate_names.py` Termux (Android) with the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`, that recursively renames non-ASCII file and directory names to ASCII-safe equivalents in place.

The script must behave as follows:

**Purpose**: Walk a directory tree recursively and rename every file/directory whose name contains non-ASCII characters to an ASCII transliteration, so that the names become safe for filesystems/tools that don't handle Unicode well.

**Dependencies**: Optionally use `pypinyin`, `pykakasi`, and `unidecode` (installside a `try/except ImportError` block are missing. `unidecode` is only a fallback transliterator.

**CLI usage**:
- `python transliterate_names.py` — operate on the current directory, actually performing renames.
- `python transliterate_names.py -n` — dching the filesystem.
- `python transliterate_/dified root directory instead of these` to parse an optional positional root directory argument ( dir) and a `-nry-run flag.

**/language**:
- **Russian (arusian a built-in hardcoded character mapping table followingN/PCGN-like romanization (e.g. ж→zh, щ→shch).
- **Persian/Arabic**: use a built-in hardcoded mapping table. Since Persian doesn't write short vowels, output is a consonant skeleton (e.g. ف → fay). Strip diacritics,Arabic digits to : detect Han characters andinyin syscores (e.g. 文件 → wen_jian).
- **Japanese**: detect kana characters (hiragana/katakana) in the name — if present, treat the whole name (including any kanji) as Japanese and use `pykakasi` to produce Hepburn romanization (e.g. ファイル → fairu). If a name contains only Han characters with no kana, treat it as Chinese instead (use the pinyin path).
- **Any other non-ASCII text** (accented Latin, Greek, emoji, symbols, etc.): if `unidecode` is available, use it; otherwise fall back to stripping accents via `unicodedata` normalization and replacing any remaining non-ASCII characters with underscores.

**Other required behavior**:
- Process directory entries recursively, renaming deeper paths before their parents where necessary (so renaming a paralidate child paths), orle path-resolution order correctly during the control metadata directories (e.g. `.git`), since renaming filesry-run mode, print each planned old-name → new-name mapping without performing any filesystem changes.
- In normal mode, actually perform the renames on disk, printing progress/results.
- Handle name collisions sensibly (e.g. if the transliterated name already exists, avoid overwriting by appending a disambiguating suffix).
- Use `re` and `unicodedata` as needed for character classification/normalization, and `pathlib.Path` for filesystem operations.
- Include module-level comments documenting install instructions, usage examples, and the language/method mapping as shown above.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/aFmDxy8i93dEDrCKDbFUd9"""

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

SKIP_DIRS = frozenset({".git", ".hg", ".svn"})
MAX_NAME = 255

KANA = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff]")
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002ebef]+")
FA_MARKS = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
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
    "\u200c": "_",
    "\u200d": "",
    "\u0640": "",
    "،": ",",
    "؛": ";",
    "؟": "",
}
for _i in range(10):
    _FA[chr(0x06F0 + _i)] = str(_i)
    _FA[chr(0x0660 + _i)] = str(_i)
FA_TABLE = {ord(k): v for k, v in _FA.items()}

BAD_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def _japanese(text: str) -> str:

    parts = []
    for item in _KAKASI.convert(text):
        orig = item["orig"]
        parts.append(orig if orig.isascii() else item["hepburn"] + "_")
    return "".join(parts)


def _chinese(text: str) -> str:

    return HAN.sub(lambda m: "_" + "_".join(lazy_pinyin(m.group())) + "_", text)


def _ascii_fallback(text: str) -> str:
    if unidecode:
        return unidecode(text)
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c if c.isascii() else "_" for c in decomposed if not unicodedata.combining(c))


def _clean(name: str, original: str) -> str:
    name = BAD_CHARS.sub("_", name)
    name = re.sub(r"_{2,}", "_", name)
    name = re.sub(r"\s{2,}", " ", name)
    name = re.sub(r"_+(?=\.)", "", name)

    if not original.startswith("_"):
        name = name.lstrip("_")
    if not original.endswith("_"):
        name = name.rstrip("_")
    name = name.rstrip(" .")
    if not name:
        name = "unnamed"
    if name.split(".")[0].upper() in RESERVED:
        name = "_" + name
    if len(name) > MAX_NAME:
        suffix = Path(name).suffix[:20]
        name = name[: MAX_NAME - len(suffix)] + suffix
    return name


def transliterate(name: str) -> str:

    text = unicodedata.normalize("NFKC", name)
    text = FA_MARKS.sub("", text)
    if KANA.search(text) and _KAKASI:
        text = _japanese(text)
    elif HAN.search(text) and lazy_pinyin:
        text = _chinese(text)
    text = text.translate(RU_TABLE).translate(FA_TABLE)
    text = _ascii_fallback(text)
    return _clean(text, name)


def _key(path: Path) -> str:
    return str(path).casefold()


def unique_target(path: Path, claimed: set) -> Path:

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
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
        sys.stderr.reconfigure(errors="backslashreplace")
    for lib, label in (
        (lazy_pinyin, "pypinyin (Chinese)"),
        (_KAKASI, "pykakasi (Japanese)"),
    ):
        if lib is None:
            print(
                f"warning: {label} not installed; falling back to a rougher conversion",
                file=sys.stderr,
            )
    root = args.root.resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 1
    entries = [p for p in root.rglob("*") if not SKIP_DIRS.intersection(p.relative_to(root).parts)]

    entries.sort(key=lambda p: len(p.parts), reverse=True)
    claimed: set = set()
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
        except OSError as exc:
            failed += 1
            print(f"  error: {exc}", file=sys.stderr)
    verb = "would rename" if args.dry_run else "renamed"
    print(f"\n{verb} {renamed} item(s), {failed} error(s).")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
