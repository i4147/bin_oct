#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory tree (defaulting to the current working directory) for executable script files and rewrites their shebang lines so they point to a specific Python 3.14 interpreter located under a configurable installation prefix (defaulting to a Termux-style Android environment path, overridable via an environment variable). The script should:
- Recursively walk the target directory, considering only regular files that are plain-text scripts with a shebang on the first line.
- Parse each shebang, handling both direct interpreter paths and `env`-style invocations (where the actual interpreter name is the argument following `env`).
- Identify shebangs that reference a Python interpreter (any executable whose name contains "python") and skip those already pointing to the target Python 3.14 path.
- Rewrite qualifying shebang lines to the new interpreter path while preserving the rest of the exactly, including line endings and any encoding considerations.
- Preserve the original file permissions and ensure the rewritten files remain executable.
- Optionally support a dry-run mode that reports which files would change without modifying them, and a verbose mode that logs each file processed, skipped, or rewritten.
- Handle errors gracefully (unreadable files, binary files, permission issues, empty files, malformed shebangs) by skipping them and reporting a summary at the end.
- Print a final summary of how many files were scanned, rewritten, skipped, and failed.
- Be runnable from the command line, accepting an optional target directory argument.
---"""

from __future__ import annotations
import os
from pathlib import Path
import stat

HOME = Path.home()
cwd = Path.cwd()
PREFIX = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))
NEW_SHEBANG = f"#!{PREFIX}/bin/python3.14"
OLD_PREFIXES = (
    str(HOME / ".local/bin"),
    str(PREFIX / "bin"),
    "/usr/bin",
    "/usr/local/bin",
    "/usr/bin/env",
    "/opt/homebrew/bin",
    "/usr/local/opt",
)


def looks_like_python_interpreter(interp: str) -> bool:
    name = Path(interp).name
    return "python" in name


def should_rewrite(interp: str) -> bool:
    if not looks_like_python_interpreter(interp):
        return False
    return interp.strip() != str(PREFIX / "bin/python3.14")


def parse_shebang(first_line: str):
    if not first_line.startswith("#!"):
        return None
    body = first_line[2:].strip()
    if not body:
        return None
    parts = body.split()
    if not parts:
        return None
    exe = parts[0]
    if Path(exe).name == "env" and len(parts) >= 2:
        return parts[1]
    return exe


def rewrite_file(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except (OSError, PermissionError) as e:
        print(f"  ! cannot read {path}: {e}")
        return False
    if b"\x00" in data[:1024]:
        return False
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    first_newline = text.find("\n")
    if first_newline == -1:
        first_line, rest = text, ""
    else:
        first_line, rest = text[:first_newline], text[first_newline:]
    interp = parse_shebang(first_line)
    if interp is None:
        return False
    if not should_rewrite(interp):
        return False
    new_content = NEW_SHEBANG + rest
    try:
        mode = path.stat().st_mode
        tmp = path.with_suffix(path.suffix + ".shebang.tmp")
        tmp.write_text(new_content, encoding="utf-8")
        os.chmod(tmp, stat.S_IMODE(mode))
        tmp.replace(path)
    except OSError as e:
        print(f"  ! cannot write {path}: {e}")
        return False
    print(f"  ✓ {path.name}:  {interp}  →  {PREFIX}/bin/python3.14")
    return True


def main():
    if not cwd.is_dir():
        print(f"Directory not found: {cwd}")
        return
    print(f"Scanning {cwd} …")
    changed = 0
    scanned = 0
    for path in sorted(cwd.iterdir()):
        if not path.is_file():
            continue
        if not os.access(path, os.X_OK):
            continue
        scanned += 1
        if rewrite_file(path):
            changed += 1
    print()
    print(f"Scanned {scanned} executable file(s); rewrote {changed} shebang(s).")


if __name__ == "__main__":
    main()
