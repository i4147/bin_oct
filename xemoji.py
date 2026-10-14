#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that recursively scans the current working directory and all of its subdirectories for text files, identifies every emoji (including multi-codepoint sequences such as skin-tone modifiers, variation selectors, zjoiner sequences, and flag pairs) appearing in their contents, and writes a consolidated JSON report to an output file in the working directory. The report should map each distinct emoji to a key describing its Unicode code points, so that each unique emoji is recorded exactly once.
Key behaviors and requirements:
- Process the directory tree concurrently using multiple worker processes to speed up scanning of large projects.
- Skip the it is scanned or included in its own results.
- Ignore files that are unonably large (anned independently; the results from all files are merged into a single collection of unique emojis.
- Write the final output as a well-formatted, human-readable JSON file, with keys sffs.
- Handle the where no emojis are found by still producing a valid (empty) JSON output.
- Run the scanning logic only when the script is executed directly, with a clean entry point.
- Avoid printing noisy output; the only expected user-facing result is the generated JSON file, optionally with a brief summary of how many unique emojis were found.
---"""

from __future__ import annotations
import json
from multiprocessing import Pool
from pathlib import Path
import re

_BASE = (
    "\U0001f300-\U0001f5ff"
    "\U0001f600-\U0001f64f"
    "\U0001f680-\U0001f6ff"
    "\U0001f700-\U0001f77f"
    "\U0001f780-\U0001f7ff"
    "\U0001f800-\U0001f8ff"
    "\U0001f900-\U0001f9ff"
    "\U0001fa00-\U0001faff"
    "\U00002600-\U000026ff"
    "\U00002700-\U000027bf"
    "\U0001f000-\U0001f0ff"
    "\U00002b00-\U00002bff"
    "\U00002190-\U000021ff"
    "\U00002300-\U000023ff"
    "\U000025a0-\U000025ff"
    "\U00002500-\U0000257f"
)
_VS = "\ufe0e\ufe0f"
_SKIN = "\U0001f3fb-\U0001f3ff"
_ZWJ = "\u200d"
_RI = "\U0001f1e6-\U0001f1ff"
EMOJI_RE = re.compile(
    f"(?:[{_BASE}][{_VS}]?[{_SKIN}]?(?:{_ZWJ}[{_BASE}][{_VS}]?[{_SKIN}]?)*|[{_RI}]{{2}})",
    flags=re.UNICODE,
)


def scan_file(path: Path) -> dict[str, str]:
    try:
        if path.stat().st_size > 20 * 1024 * 1024:
            return {}
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    result: dict[str, str] = {}
    for match in EMOJI_RE.finditer(text):
        emoji = match.group(0)
        key = " ".join(f"U+{ord(ch):04X}" for ch in emoji)
        result[key] = emoji
    return result


def main() -> None:
    here = Path.cwd()
    out_path = here / "emojis.json"
    out_resolved = out_path.resolve()
    paths = [p for p in here.rglob("*") if p.is_file() and p.resolve() != out_resolved]
    found: dict[str, str] = {}
    with Pool() as pool:
        for partial in pool.imap_unordered(scan_file, paths):
            found.update(partial)
    out_path.write_text(
        json.dumps(found, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"Found {len(found)} unique emojis. Wrote to {out_path}")


if __name__ == "__main__":
    main()
