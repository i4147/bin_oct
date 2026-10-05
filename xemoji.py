#!/data/data/com.termux/files/usr/bin/python3.12
import json
import re
from pathlib import Path

_BASE = (
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "\U0001F000-\U0001F0FF"
    "\U00002B00-\U00002BFF"
    "\U00002190-\U000021FF"
    "\U00002300-\U000023FF"
    "\U000025A0-\U000025FF"
    "\U00002500-\U0000257F"
)
_VS   = "\uFE0E\uFE0F"
_SKIN = "\U0001F3FB-\U0001F3FF"
_ZWJ  = "\u200D"
_RI   = "\U0001F1E6-\U0001F1FF"

EMOJI_RE = re.compile(
    "(?:"
    f"[{_BASE}][{_VS}]?[{_SKIN}]?"
    f"(?:{_ZWJ}[{_BASE}][{_VS}]?[{_SKIN}]?)*"
    "|"
    f"[{_RI}]{{2}}"
    ")",
    flags=re.UNICODE,
)

here = Path.cwd()
out_path = here / "emojis.json"

found = {}

for path in here.rglob("*"):
    if not path.is_file() or path.resolve() == out_path.resolve():
        continue
    try:
        if path.stat().st_size > 20 * 1024 * 1024:
            continue
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        continue

    for match in EMOJI_RE.finditer(text):
        emoji = match.group(0)
        key = " ".join(f"U+{ord(ch):04X}" for ch in emoji)
        found[key] = emoji

out_path.write_text(
    json.dumps(found, ensure_ascii=False, indent=2, sort_keys=True),
    encoding="utf-8",
)
print(f"Found {len(found)} unique emojis. Wrote to {out_path}")
