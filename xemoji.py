#!/data/data/com.termux/files/usr/bin/python3.12
"""Create a Python 3 script (intended to run under Termux on Android, using the shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that scans the current working directory recursively for emoji characters used in text files and exports all unique emojis found to a JSON file.

Requirements and behavior:

1. **Purpose**: Recursively walk through every file and subdirectory starting from the current working directory, read each file's text content, detect all emoji characters (including multi-codepoint emoji sequences such as ZWJ sequences, skin-tone modifiers, variation selectors, and regional-indicator flag pairs), and collect the unique set of emojis encountered across all files.

2. **Emoji detection**:
   - Build a regex pattern using Unicode ranges covering common emoji blocks (e.g., U+1F300–U+1F5FF, U+1F600–U+1F64F, U+1F680–U+1F6FF, U+1F700–U+1F7FF, U+1F780–U+1F8FF, U+1F900–U+1FAFF, U+2600–U+26FF, U+2700–U+27BF, U+1F000–U+1F0FF, U+2B00–U+2BFF, U+2190–U+21FF, U+2300–U+23FF, U+25A0–U+25FF, U+2500–U+257F).
   - Support variation selectors (U+FE0E, U+FE0F), skin-tone modifiers (U+1F3FB–U+1F3FF), zero-width joiner (U+200D) sequences for combined emoji, and pairs of regional-indicator symbols (U+1F1E6–U+1F1FF) for flag emojis.
   - Use a single compiled regular expression that matches either a base emoji (optionally followed by a variation selector and/or skin-tone modifier, optionally repeated via ZWJ joins) or exactly two regional-indicator characters.

3. **File scanning**:
   - Use `pathlib.Path.cwd()` as the root directory and recursively iterate all entries (`rglob("*")`).
   - Skip anything that is not a regular file.
   - Skip the script's own output file (compare resolved paths).
   - Skip files larger than 20 MB.
   - Attempt to read each file as UTF-8 text; silently skip files that raise `OSError` or `UnicodeDecodeError` (e.g., binary files or unreadable files).

4. **Collection logic**:
   - For every emoji match found in a file's text, build a dictionary key composed of the space-separated Unicode code points of each character in the matched emoji, formatted as `U+XXXX` (uppercase hex, zero-padded to 4 digits), e.g., `"U+1F600"` or `"U+1F468 U+200D U+1F469"`.
   - Store the key mapped to the actual emoji string in a dictionary, naturally deduplicating identical emojis across all files.

5. **Output**:
   - Write the resulting dictionary to a file named `emojis.json` in the current working directory.
   - Serialize as JSON with `ensure_ascii=False`, `indent=2`, and `sort_keys=True`.
   - Use UTF-8 encoding when writing.

6. **Console output**:
   - After writing the file, print a summary message in the form: `Found {count} unique emojis. Wrote to {out_path}`ji entries and `out_path` is the full path to the generated JSON file.

The script should have no command-line arguments or external dependencies beyond the Python standard library (`json`, `re`, `pathlib`).
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/en3ZY6GWmN2BKmF3mCnXkH"""

import json
import re
from pathlib import Path

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
