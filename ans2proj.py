#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that parses a Markdown "digest" file containing multiple code sections, each introduced by a header line in the form "## `relative/path`" followed by a fenced code block, and reconstructs the original files on disk under a given root directory.
It should use a regex to locate headers and code fences, extract each file's relative path and body content between the opening and closing triple-backtick fences (gracefully handling missing closing fences by saving partial content and logging a warning via loguru), then write each extracted section to its corresponding file path under the root, creating parent directories as needed.
The script should be runnable from the command line, taking the digest file path and target root directory as inputs, and should report progress/errors through logging while producing the restored file tree as output."""

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
            if content.endswith("\n"):
                content = content[:-1]
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
