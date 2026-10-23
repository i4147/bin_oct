#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
from pathlib import Path
import re
import sys
CODE_BLOCK_RE = re.compile(
    r"^```(?:python|py)\b\s*\n(.*?)^```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)
def extract_blocks(text: str) -> list[str]:
    return [match.group(1) for match in CODE_BLOCK_RE.finditer(text)]
def markdown_files(argv: list[str]) -> list[Path]:
    if len(argv) > 1:
        return [Path(arg) for arg in argv[1:]]
    return sorted(Path.cwd().glob("*.md"))
def main() -> None:
    out_dir = Path.cwd()
    counter = 0
    for md_path in markdown_files(sys.argv):
        if not md_path.is_file():
            print(f"skip (not a file): {md_path}")
            continue
        text = md_path.read_text(encoding="utf-8")
        for code in extract_blocks(text):
            counter += 1
            out_path = out_dir / f"ex{counter:02d}.py"
            out_path.write_text(code, encoding="utf-8")
            print(f"{md_path.name}  ->  {out_path.name}")
    print(f"\nDone. Extracted {counter} Python code block(s).")
if __name__ == "__main__":
    main()
