#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that parses a Markdown document containing multiple file sections and recreates those files on disk. The script should accept a path to a Markdown input file and an output directory as inputs, and treat each level-two heading whose text is a relative file path wrapped in backticks as the start of a new section. Within each section, the script should locate the first fenced code block and extract its contents as the file body, handling both properly closed fences and cases where the closing fence is missing (in which case it should take everything remaining in that section and log a warning). Content that appears outside of fenced blocks under a heading should be ignored, and sections without any code fence should be skipped with a logged warning.
The script should create any necessary subdirectories under the output directory so that each file lands at its specified relative path, overwrite existing files safely, and avoid writing outside the output directory (guard against absolute paths or path traversal such as "..").
It should log progress and warnings clearly, print a summary at the end listing how many files were written and how many sections were skipped, and exit with a non-zero status code with a helpful error message if the input file is missing or unreadable. The script should be runnable from the command line with the input and output locations supplied as arguments, and it should preserve the file contents exactly, including indentation, trailing newlines, and line endings where reasonable.
---"""

from __future__ import annotations
from pathlib import Path
import re
import sys
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
