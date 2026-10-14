#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that cleans up raw terminal or log text captured from a command-line session. The script should read text input (from a file path given as an argument, or from standard input when no argument is provided) and write the cleaned result to standard output or to an output file specified by the user.
The cleaning should remove terminal control artifacts so the result reads as plain, human-readable text. This includes stripping ANSI escape sequences used for colors, cursor movement, and screen control; resolving carriage returns and normalizing line endings; applying backspace characters so that overwritten characters are removed; and dropping null bytes and other non-printable control characters while preserving ordinary whitespace and newlines. Collapse runs of excessive blank lines into a single blank line, strip trailing whitespace from every line, and ensure the output ends with exactly one newline.
The script should also support a second, more specialized cleaning mode aimed at email-style or mail-transcript content. In this mode, after the same terminal artifact removal, it should locate a header line beginning with "Received:" (case-insensitive) and trim the text so that only the content following that header block remains, skipping the header's first line and any leading blank lines that follow. If no such header is found, the text should pass through unchanged apart from the general cleanup.
Allow the user to select the mode via a command-line option, default to the general cleaning mode, and print a brief usage message on invalid arguments. Handle missing input files with a clear error message and a non-zero exit code. The script should be robust to large inputs and to text containing mixed line endings or unusual control characters, and it should never crash on malformed escape sequences.
---"""

from __future__ import annotations
import sys
import regex as re


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
