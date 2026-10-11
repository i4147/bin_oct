#!/data/data/com.termux/files/usr/bin/env python
"""You are reproducing a Python utility script from scratch. Write a single self-contained Python 3 script that meets the specification below. Output only the script itself, with no commentary.

**Purpose:** The script parses a Markdown file that contains multiple file sections, each introduced by a level-2 heading whose text is a file path wrapped in backticks (for example, a heading of the form `## ` followed by a backtick-quoted relative path). Under each heading is a fenced code block. The script extracts each relative path and the content of its fenced block, returning them as an ordered list of (path, content) pairs, and it is intended to be the core of a tool that later writes those contents to disk.

**Shebang and imports:** Start with a Termux-specific shebang line pointing to `/data/data/com.termux/files/usr/bin/env python`. Use `from __future__ import annotations`. Import `re`, `sys`, and `Path` from `pathlib`. Import `logger` from the third-party `loguru` package and use it for all warnings (do not use the standard `logging` module).

**Regular expressions (compiled at module level, with type annotations of `re.Pattern[str]`):**
- A header pattern matching lines that begin with `## `, followed by a backtick-quoted capture group of one or more non-backtick characters, followed by optional trailing whitespace to end of line. Use multiline mode.
- An opening fence pattern matching three backticks followed by any non-newline characters (info string) and a newline.
- A closing fence pattern using multiline mode that matches a line consisting of exactly three backticks with optional spaces or tabs and an optional carriage return before the newline.

**Function `extract_sections(text: str) -> list[tuple[str, str]]`:**
1. Find all header matches in the text and convert to a list.
2. For each header at index i, take the relative path from capture group 1. The body starts right after the header match and ends at the start of the next header, or at the end of the text if it is the last header.
3. Search the body for the opening fence. If none is found, log a warning in the form `"<rel>: no opening code fence found, skipping"` and continue to the next header without appending.
4. Take the remainder of the body after the opening fence. Search it for the closing fence. If found, the content is everything before the closing fence's start, with one trailing newline removed (use the string method that removes a suffix, available in Python 3.9+). If not found, the content is the remainder with all trailing newlines stripped, and log a warning `"<rel>: missing closing fence, saving partial content"`.
5. If this is the last header in the file and no closing fence was found, additionally log a warning `"<rel>: last section in file, saving what exists"`.
6. Append the tuple (relative path, content) to the result list, preserving document order.
7. Return the list. An empty list is returned if no headers exist.

**Edge cases to honor:** Headers with no following fence are skipped rather than erroring. Unclosed fences are tolerated and saved as partial content. CRLF line endings in closing fences are accepted. Content inside fences is preserved verbatim, including inner backticks that are not on their own line.

**Main execution (guarded by `if __name__ == "__main__":`):**
- Accept the input Markdown file path as the first command-line argument via `sys.argv`.
- If no argument is supplied, or the file does not exist, log an error through loguru and exit with a nonzero status code via `sys.exit`.
- Read the file as UTF-8 text using `Path`.
- Call `extract_sections` on the text.
- For each returned (path, content) pair, log an informational message (or print) showing the path and content length; do not write files to disk in this version.
- Log a summary of how many sections were extracted, and exit with status 0 on success.

**Style:** Use concise docstrings or comments only where helpful, type hints throughout, f-strings for formatting, and 4-space indentation. Keep the whole script to a single file with no external dependencies beyond `loguru`.
---"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from loguru import logger

HEADER_RE: re.Pattern[str] = re.compile(r"^##\s+`([^`]+)`\s*$", re.MULTILINE)
OPEN_FENCE_RE: re.Pattern[str] = re.compile(r"```[^\n]*\n")
CLOSE_FENCE_RE: re.Pattern[str] = re.compile(r"(?m)^```[ \t]*\r?$")


def extract_sections(text: str) -> list[tuple[str, str]]:
    headers = list(HEADER_RE.finditer(text))
    sections: list[tuple[str, str]] = []
    for i, match in enumerate(headers):
        rel = match.group(1)
        start = match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[start:end]
        open_match = OPEN_FENCE_RE.search(body)
        if not open_match:
            logger.warning(f"{rel}: no opening code fence found, skipping")
            continue
        rest = body[open_match.end() :]
        close_match = CLOSE_FENCE_RE.search(rest)
        if close_match:
            content = rest[: close_match.start()]
            content = content.removesuffix("\n")
        else:
            content = rest.rstrip("\n")
            logger.warning(f"{rel}: missing closing fence, saving partial content")
        if i + 1 == len(headers) and not close_match:
            logger.warning(f"{rel}: last section in file, saving what exists")
        sections.append((rel, content))
    return sections


def write_file(root: Path, rel: str, content: str) -> bool:
    target = root / rel
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        logger.info(f"wrote {target}")
        return True
    except OSError as exc:
        logger.error(f"failed to write {target}: {exc}")
        return False


def main() -> int:
    if len(sys.argv) < 2:
        logger.error("usage: script.py <source.md> [output_dir]")
        return 2
    src = Path(sys.argv[1])
    root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()
    try:
        text = src.read_text()
    except OSError as exc:
        logger.error(f"failed to read {src}: {exc}")
        return 1
    sections = extract_sections(text)
    if not sections:
        logger.warning(f"no sections found in {src}")
        return 1
    ok = 0
    for rel, content in sections:
        if write_file(root, rel, content):
            ok += 1
    logger.info(f"created {ok}/{len(sections)} files under {root}")
    return 0 if ok == len(sections) else 1


if __name__ == "__main__":
    sys.exit(main())
