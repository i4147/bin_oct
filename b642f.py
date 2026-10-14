#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a text or markdown file for embedded base64-encoded image data (such as data URIs of the form "data:image/...;base64,..."), decodes each embedded payload, and saves the recovered files into an output folder inside the current working directory. The script should accept a path to the source file as input and produce decoded image files as output, naming them in a clear, sequential or content-based way so they can be easily identified. It should handle common variations in how base64 data is embedded, such as payloads terminated by quotes, spaces, or closing parentheses, and tolerate malformed or truncated base64 strings by attempting a best-effort recovery (for example, by trimming a trailing character) rather than crashing. The script should skip entries that cannot be decoded, report a summary of how many files were successfully extracted and how many failed, and optionally clean up or leave intermediate artifacts depending on a configuration setting. Ensure the output directory is created automatically if it does not exist, and make the tool robust enough to process large files line by line without loading everything into memory at once.
---"""

from __future__ import annotations
import base64
from pathlib import Path
import sys
from dh import cprint


def content_hash(data: bytes) -> str:
    from hashlib import sha256

    if not isinstance(data, bytes):
        data = data.encode("utf8")
    return sha256(data).hexdigest()


cleanup = True
cwd = Path.cwd()
out_dir = Path("output")
if not out_dir.exists():
    out_dir.mkdir(exist_ok=True)


def try_again(txt, fout) -> None:
    try:
        txt = txt[:-1]
        dbz = base64.b64decode(txt)
        fout.write_text(dbz)
    except:
        return


def clean_line(txt):
    cleaned: str = ""
    indx = txt.index("base64,") + 7
    cleaned = txt[indx:]
    if '"' in cleaned:
        end_indx = cleaned.index('"')
        cleaned = cleaned[:end_indx]
    elif " " in cleaned:
        end_indx = cleaned.index(" ")
        cleaned = cleaned[:end_indx]
    elif ")" in cleaned:
        end_indx = cleaned.index(")")
        cleaned = cleaned[:end_indx]
    return cleaned


def decode_base64_lines(path: Path) -> None:
    success_count = 0
    error_count = 0
    failed = []
    remained = []
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            output_path = Path(f"{content_hash(line)}.bin")
            if "base64," in line:
                line = clean_line(line)
            try:
                decoded_bytes = base64.b64decode(line.strip())
                output_path.write_bytes(decoded_bytes)
                success_count += 1
            except Exception as e:
                print(f"✗ Line {i:4d} failed: {e}")
                error_count += 1
                failed.append(i)
                remained.append(line)
    print(failed)
    cprint(f"✓ {success_count}\n✘ {error_count}", "cyan")
    if cleanup:
        new_content = "\n".join(remained)
        path.write_text(new_content)


if __name__ == "__main__":
    INPUT_FILE = Path(sys.argv[1])
    decode_base64_lines(INPUT_FILE)
