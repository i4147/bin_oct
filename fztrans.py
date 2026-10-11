#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python command-line bilingual dictionary tool (Persian/Farsi ↔ English) for Termux on Android, backed by a JSON file at ~/dic.json. Cover the following:

**Purpose:** A terminal dictionary lookup tool that translates words in both directions between Farsi (fa) and English (en) using a user-supplied JSON dictionary file. It should support an interactive mode with tab completion and fuzzy-match suggestions, plus a one-shot mode for translating a word passed as a command-line argument.

**Environment and dependencies:**
- Target shebang: the Termux Python path `/data/data/com.termux/files/usr/bin/env python`.
- Standard library only, except for a third-party-style helper module named `faprint` that exposes a `faprint` function used for formatted output. Reproduce its import as-is and assume it is available.
- Use `from __future__ import annotations`. Use `readline` for tab completion (note it is available on Termux and most Unix-like systems), `shutil`, `subprocess` (for launching external output or clipboard/pager-style helpers if needed), `difflib.get_close_matches` for fuzzy suggestions, `pathlib.Path`, `typing.Final`, `argparse`, `json`, `logging`, and `sys`.
- Configure logging at INFO level with a bare message format (`%(message)s`) and use a module-level logger named after `__name__`.

**Dictionary file:**
- Path is a constant `DICT_FILE` equal to `~/dic.json` expanded to the user's home directory, typed as `Final[str]` (though it is a Path object; reproduce faithfully).
- The JSON is an object mapping Farsi words to English translations. Keys and values are coerced to strings and stripped of whitespace.
- Build two dictionaries: `fa_en` (Farsi→English) and `en_fa` (English→Farsi, the inverse). Note that if multiple Farsi words share an English value, the inverse keeps the last one encountered.
- Function `load_dictionary(path)` returns the tuple `(fa_en, en_fa)`. If the file is missing, log an error like "Error: Dictionary file <path> not found" and exit with status 1. If reading or JSON parsing fails for any reason, log "Error loading dictionary: <exception>" and exit with status 1. Read with UTF-8 encoding.

**Tab completion:**
- Function `setup_readline(words)` sorts the combined vocabulary, registers a completer that returns prefix matches by state index (returning None when exhausted), binds `tab: complete`, and sets completer delimiters to space, tab, and newline.

**Translation logic (`translate(word, fa_en, en_fa)` and related):**
- Determine the language direction by checking whether the input word appears in the Farsi or English dictionary; look up the translation in the opposite dictionary.
- If no exact match is found, use `difflib.get_close_matches` against the relevant keys to offer suggestions, and report them to the user.
- Handle empty input and whitespace gracefully (strip input before lookup).
- Output should be formatted via the `faprint` helper.

**Execution modes:**
- Use `argparse` for CLI arguments: an optional positional word to translate directly, with an interactive loop when no word is provided.
- Interactive mode: repeatedly prompt for input, allow an exit command (such as empty input, `exit`, or `quit`) and handle Ctrl-C and EOF cleanly by exiting without a traceback.
- Use `sys.exit` with appropriate status codes on fatal errors.
- The script runs as a main program guarded by `if __name__ == "__main__":`.

**Edge cases to honor:** missing dictionary file, malformed JSON, non-object JSON, non-string values (coerced via `str`), duplicate English values (inverse map collisions), words not found (suggest close matches or report absence), empty or whitespace-only input, and Persian Unicode text requiring UTF-8 throughout.

**Output requirements:** Produce a single, complete Python script with the shebang line, imports, constants, functions, and a `main` entry point. Keep type hints consistent with the original (including `tuple[dict[str, str], dict[str, str]]` and `str | None`). Match standard PEP 8 style and docstrings where helpful.
---"""

from __future__ import annotations

import argparse
import json
import logging
import readline
import shutil
import subprocess
import sys
from difflib import get_close_matches
from pathlib import Path
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
