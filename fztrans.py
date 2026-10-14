#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as an interactive bilingual (Persian/English) command-line dictionary lookup tool. The tool should load a word-pair dictionary from a JSON file in the user's home directory, where each entry maps a Persian term to its English equivalent. If the dictionary file is missing or cannot be parsed, the tool should log a clear error message and exit with a non-zero status.
The script should support two modes of use:
1 mode**: The user passes a word or phrase as a command-line argument. The tool looks it up in either direction (Persian-to-English or English-to-Persian), prints the translation if found, and exits. If no exact match exists, it should suggest close matches using fuzzy string matching.
2. **Interactive mode**: When no argument is given, the tool starts a continuous prompt loop where the user can type words repeatedly. The prompt should offer tab-completion over all known words in both languages, retain command history across inputs, and exit cleanly on an exit command or end-of-input (Ctrl+D) or interrupt (Ctrl+C), printing a friendly farewell.
Additional behaviors to include:
- Automatically detect whether the entered text is Persian or English so the correct direction is used, while still allowing lookups to succeed when the text matches either side.
- Handle right-to-left Persian text correctly in terminal output.
- Provide a helpful usage/help message describing both modes and any flags.
- Use a consistent, readable output format for results, including the "not found" case with suggestions.
- Keep the code robust against empty input, whitespace, and unexpected characters.
- Log informational and error messages through a standard logging setup rather than bare prints where appropriate.
The script should rely on a small external formatting helper for displaying styled or RTL-aligned text, and should be organized so that loading, lookup, completion setup, and the interactive loop are clearly separated concerns.
---"""

from __future__ import annotations
import argparse
from difflib import get_close_matches
import json
import logging
from pathlib import Path
import readline
import shutil
import subprocess
import sys
from typing import Final
from faprint import faprint

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
DICT_FILE: Final[str] = Path("~/dic.json").expanduser()


def load_dictionary(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    if not path.exists():
        logger.error("Error: Dictionary file %s not found", path)
        sys.exit(1)
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        fa_en = {str(k).strip(): str(v).strip() for k, v in data.items()}
        en_fa = {v: k for k, v in fa_en.items()}
        return (fa_en, en_fa)
    except Exception as e:
        logger.error("Error loading dictionary: %s", e)
        sys.exit(1)


def setup_readline(words: Iterable[str]) -> None:
    sorted_words = sorted(words)

    def completer(text: str, state: int) -> str | None:
        matches = [w for w in sorted_words if w.startswith(text)]
        return matches[state] if state < len(matches) else None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" \t\n")


def translate(word: str, fa_en: dict[str, str], en_fa: dict[str, str]) -> str | None:
    return fa_en.get(word) or en_fa.get(word)


def fuzzy_search(word: str, all_words: set[str], limit: int = 5, cutoff: float = 0.6) -> list[str]:
    return get_close_matches(word, all_words, n=limit, cutoff=cutoff)


def fzf_select(all_words: set[str]) -> str | None:
    if not shutil.which("fzf"):
        logger.warning("fzf not found in PATH. Falling back to normal mode.")
        return None
    try:
        proc = subprocess.run(
            [
                "fzf",
                "--prompt=Select word: ",
                "--height=40%",
                "--layout=reverse",
                "--border",
            ],
            input="\n".join(sorted(all_words)),
            text=True,
            capture_output=True,
            check=False,
        )
        selection = proc.stdout.strip()
        return selection or None
    except Exception as e:
        logger.error("fzf execution error: %s", e)
        return None


def interactive_mode(fa_en: dict[str, str], en_fa: dict[str, str]) -> None:
    all_words = set(fa_en) | set(en_fa)
    setup_readline(all_words)
    print("\n🌐 Offline Persian ↔ English Translator")
    print("⌨  TAB for suggestions, Ctrl+C to exit\n")
    while True:
        try:
            word = input("> ").strip()
            if not word:
                continue
            result = translate(word, fa_en, en_fa)
            if result:
                print(f"✅ {result}")
            else:
                matches = fuzzy_search(word, all_words)
                if matches:
                    print(f"❓ Not found. Did you mean: {', '.join(matches)}?")
                else:
                    print("❌ Not found")
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Bye.")
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline Persian ↔ English translator")
    parser.add_argument("word", nargs="*", help="Word to translate")
    parser.add_argument("--prefix", help="List words starting with prefix")
    parser.add_argument("--fuzzy", help="Fuzzy search (typo tolerant)")
    parser.add_argument("--no-fzf", action="store_true", help="Disable interactive fzf selector")
    args = parser.parse_args()
    fa_en, en_fa = load_dictionary(Path(DICT_FILE))
    all_words = set(fa_en) | set(en_fa)
    if not args.no_fzf and (not args.word) and (not args.prefix) and (not args.fuzzy):
        selected = fzf_select(all_words)
        if selected:
            result = translate(selected, fa_en, en_fa)
            print(f"{selected} → {result}")
            sys.exit(0)
        elif shutil.which("fzf"):
            sys.exit(0)
    if args.prefix:
        matches = sorted(w for w in all_words if w.startswith(args.prefix))
        if matches:
            print("\n".join(matches))
            sys.exit(0)
        print("No matches found for prefix: %s", args.prefix)
        sys.exit(1)
    if args.fuzzy:
        matches = fuzzy_search(args.fuzzy, all_words)
        if matches:
            print("\n".join(matches))
            sys.exit(0)
        print("No close matches found for: %s", args.fuzzy)
        sys.exit(1)
    if args.word:
        word = " ".join(args.word).strip()
        result = translate(word, fa_en, en_fa)
        if result:
            faprint(result)
            sys.exit(0)
        else:
            matches = fuzzy_search(word, all_words)
            if matches:
                faprint(f"Not found. Did you mean: {', '.join(matches)}?", file=sys.stderr)
            else:
                print("Not found", file=sys.stderr)
            sys.exit(1)
    interactive_mode(fa_en, en_fa)


if __name__ == "__main__":
    raise SystemExit(main())
