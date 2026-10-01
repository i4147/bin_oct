#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that cleans a raw terminal transcript file passed as a single argument, reading it as UTF-8 text with error replacement.
It should strip ANSI escape sequences, normalize CRLF/CR line endings to LF, remove backspace-erased characters and other control characters, collapse three or more consecutive blank lines into a single blank line, and trim trailing whitespace from each line while ensuring the file ends with exactly one newline.
The cleaned content should overwrite the original file, and the script should print a confirmation message showing the cleaned file path.
If the script is run without exactly one argument, it should print a usage message and exit with status code 1."""

import regex as re
import sys


def clean1(text: str) -> str:
    ansi_escape = re.compile(r"\x1b(\[[0-9;]*[mABCDEFGHJKSTfhilmnprsu]|\][^\x07]*\x07|[()][AB012])")
    content = ansi_escape.sub("", text)
    content = content.replace("\r\n", "\n")
    content = content.replace("\r", "\n")
    while "\x08" in content:
        content = re.sub(r".\x08", "", content)
    content = content.replace("\x00", "")
    content = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", content)
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = "\n".join(line.rstrip() for line in content.splitlines())
    return content.rstrip("\n") + "\n"


def clean2(text: str) -> str:
    text = ANSI_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    m = re.search(r"^\s*Received\s*:", text, re.MULTILINE | re.IGNORECASE)
    if m:
        after = text[m.end() :]

        after = after.split("\n", 1)[1] if "\n" in after else ""
        after = re.sub(r"^\s*\n+", "", after)
        text = after

    text = re.sub(
        r"^\s*(?:SuperAgent|felo|feli)\b.*$",
        "",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    text = FENCE_RE.sub("", text)
    text = SHELL_PROMPT_RE.sub("", text)
    text = PREAMBLE_RE.sub("", text)
    text = text.strip()

    if not text:
        return ""

    if "\n" not in text:
        parts = re.split(r"(?<=[.!?])\s+", text)
        text = "\n".join(p.strip() for p in parts if p.strip())

    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def clean_terminal_transcript(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    res1 = clean1(content)
    res2 = clean2(content)
    f1 = Path("res1")
    f2 = Path("res2")

    if res1 != res2:
        print("\u2713 not same")
        input("press any key ...")
        f1.write_text(res1)
        f2.write_text(res2)

    final = res1.rstrip("\n") + "\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(final)
    print(f"Cleaned: {path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <transcript_file>")
        sys.exit(1)
    clean_terminal_transcript(sys.argv[1])
