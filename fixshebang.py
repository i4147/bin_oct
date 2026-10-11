#!/data/data/com.termux/files/usr/bin/env python
"""I'm going to write the prompt directly from the code you pasted; no tools are needed.

Write a self-contained Python 3 script that reproduces the following behavior. Use only the standard library. Include a Termux-style shebang on line 1 (`#!/data/data/com.termux/files/usr/bin/env python`) and `from __future__ import annotations` at the top, and use `typing.Final` for module-level constants.

**Purpose:** The script scans a directory tree for Python source files that lack a proper Python shebang line (or are otherwise identifiable as Python), and normalizes their first line so they start with a fixed Termux-specific interpreter shebang. It processes files in parallel.

**Constants to define:**
- A compiled regex `SHEBANG_PATTERN` (multiline mode) that matches a first-line shebang referencing `python`, optionally with a version suffix such as `python2`, `python3`, or `python3.x`, and optional trailing arguments.
- `PY_SHEBANG`, the replacement shebang string `#!/data/data/com.termux/files/usr/bin/python3.14`.
- A set `COMMON_PYTHON_NAMES` of extensionless and `.py`-suffixed names commonly used for Python entry points (e.g., setup, manage, app, wsgi, asgi, test, conftest, requirements, main, cli, run, each with and without `.py`).

**Function `is_likely_python_file(path: Path) -> bool`:**
- Open the file in binary mode and read only the first 512 bytes. Wrap everything in a try/except that returns False on any error (e.g., permissions, missing file, directory).
- If the sample starts with `#!` and the first line (up to the first newline, or the whole sample if there is no newline) contains `python` (case-insensitive), return True.
- Otherwise decode the sample as UTF-8 with errors ignored and test it against a list of regex patterns anchored at line starts with multiline matching: import/from statements, `def name(`, `class Name:` or `class Name(`, `if __name__ == '__main__'` (either quote style), and a `#!` line containing `python`. Return True if any match.

**Expected remaining behavior (infer and complete sensibly):**
- A function that takes a file path, checks whether it is a candidate (e.g., name in COMMON_PYTHON_NAMES, `.py` suffix, or `is_likely_python_file` returns True), reads the full text, and if the first line does not already match SHEBANG_PATTERN, replaces or prepends the first line with `PY_SHEBANG` while preserving the rest of the content and line endings. Handle `UnicodeDecodeError` and `OSError` gracefully by skipping the file and returning a status or message rather than crashing.
- A main entry point that accepts a root directory (default to the current directory, or take it from `sys.argv[1]`), recursively walks it with `Path.rglob`, skips hidden directories and common vendor/cache directories such as `.git`, `__pycache__`, `venv`, `.venv`, `node_modules`, and skips non-regular files and symlinks.
- Use `multiprocessing.Pool` to process the collected files in parallel (use `if __name__ == "__main__":` guard), and collect results via `imap_unordered` or `map`.
- Print a concise summary: number of files scanned, number modified, and a list of modified paths and any errors encountered. Use a non-zero exit code if any errors occurred.
- Preserve file encoding (UTF-8) and do not modify files that already have a matching Python shebang.
- Be idempotent: running it twice should produce no further changes.
- Use type hints throughout, PEP 8 style, and short docstrings for each function.

**Output requirements for the generated script:** Print nothing except the summary and per-file messages for modified or failed files. Do not follow symlinks. Do not crash on empty files (an empty file should get the shebang only if it is a candidate, or be skipped; document the choice in a comment).
---"""

from __future__ import annotations

import re
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Final

SHEBANG_PATTERN: Final[re.Pattern[str]] = re.compile(r"^#!.*python[23]?(?:\.\d+)?(?:[ \t]+.*)?$", re.MULTILINE)
PY_SHEBANG: Final[str] = "#!/data/data/com.termux/files/usr/bin/python3.14"
COMMON_PYTHON_NAMES: Final[set[str]] = {
    "setup",
    "setup.py",
    "manage",
    "manage.py",
    "app",
    "app.py",
    "wsgi",
    "wsgi.py",
    "asgi",
    "asgi.py",
    "test",
    "test.py",
    "conftest",
    "conftest.py",
    "requirements",
    "main",
    "main.py",
    "cli",
    "cli.py",
    "run",
    "run.py",
}


def is_likely_python_file(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            content = f.read(512)
            if content.startswith(b"#!"):
                first_line = content.split(b"\n")[0] if b"\n" in content else content
                if b"python" in first_line.lower():
                    return True
            text_sample = content.decode("utf-8", errors="ignore")
            python_patterns = [
                r"^(from|import)\s+",
                r"^def\s+\w+\s*\(",
                r"^class\s+\w+[:\(]",
                r"^if\s+__name__\s*==\s*['\"]__main__['\"]",
                r"^#!.*python",
            ]
            return any(re.search(pattern, text_sample, re.MULTILINE) for pattern in python_patterns)
    except (OSError, UnicodeDecodeError, PermissionError):
        return False


def find_python_files(directory: Path) -> list[Path]:
    python_files: list[Path] = []
    for path in directory.rglob("*"):
        if any(part.startswith(".") and part != "." for part in path.parts) and ".git" in path.parts:
            continue
        if path.is_symlink():
            continue
        if not path.is_file():
            continue
        if path.suffix == ".py":
            python_files.append(path)
            continue
        skip_patterns = [
            r"\.(md|txt|rst|json|yaml|yml|toml|ini|cfg|conf|log|lock|gitignore|dockerignore)$",
            r"\.(css|html|js|ts|jsx|tsx|vue|svelte)$",
            r"\.(jpg|jpeg|png|gif|svg|ico|webp)$",
            r"\.(mp4|mp3|avi|mkv|mov)$",
            r"\.(pdf|doc|docx|xls|xlsx|ppt|pptx)$",
            r"\.(zip|tar|gz|rar|7z)$",
            r"\.(so|dll|dylib|exe|o|a|lib)$",
            r"\.(pyc|pyo|pyd)$",
        ]
        if any(re.search(pattern, str(path), re.IGNORECASE) for pattern in skip_patterns):
            continue
        if path.stem in COMMON_PYTHON_NAMES:
            if is_likely_python_file(path):
                python_files.append(path)
            continue
        if "." not in path.name and is_likely_python_file(path):
            python_files.append(path)
    return python_files


def process_file(path: Path, root_dir: Path) -> tuple[Path, bool, str | None, str, str]:
    rel_path = str(path.relative_to(root_dir))
    if path.is_symlink():
        return (path, False, "Symlink skipped", rel_path, "skipped")
    try:
        content = path.read_text(encoding="utf-8")
        new_shebang = PY_SHEBANG
        has_shebang = content.startswith("#!")
        if not has_shebang:
            path.write_text(f"{new_shebang}\n{content}", encoding="utf-8")
            return (path, True, None, rel_path, "added")
        first_line = content.split("\n", 1)[0]
        if "python" not in first_line.lower():
            return (path, False, "Not a Python shebang", rel_path, "skipped")
        if first_line.strip() == new_shebang:
            return (path, False, "Already correct", rel_path, "unchanged")
        lines = content.split("\n")
        lines[0] = new_shebang
        path.write_text("\n".join(lines), encoding="utf-8")
        return (path, True, None, rel_path, "updated")
    except Exception as e:
        return (path, False, str(e), rel_path, "error")


def _process_file_star(
    args: tuple[Path, Path],
) -> tuple[Path, bool, str | None, str, str]:
    return process_file(*args)


def main() -> int:
    current_dir = Path.cwd()
    print(f"📁 Scanning directory: {current_dir}")
    print("-" * 40)
    python_files = find_python_files(current_dir)
    if not python_files:
        print("No Python files found.")
        return 0
    print(f"Found {len(python_files)} Python files to check.")
    print("-" * 40)
    updated_files: list[tuple[Path, str]] = []
    added_shebang_files: list[tuple[Path, str]] = []
    errors: list[tuple[str, str]] = []
    skipped_count = 0
    already_correct_count = 0
    not_python_count = 0
    with Pool(processes=8) as pool:
        async_results: list[Any] = []
        for path in python_files:
            async_results.append(pool.apply_async(_process_file_star, ((path, current_dir),)))
        for async_result in async_results:
            path, was_changed, error, rel_path, action_type = async_result.get()
            if error:
                if "Symlink" in error:
                    skipped_count += 1
                elif "Not a Python shebang" in error:
                    not_python_count += 1
                elif "Already correct" in error:
                    already_correct_count += 1
                else:
                    errors.append((rel_path, error))
            elif was_changed and action_type == "updated":
                updated_files.append((path, rel_path))
            elif was_changed and action_type == "added":
                added_shebang_files.append((path, rel_path))
            else:
                skipped_count += 1
    if updated_files:
        print(f"\n✅ Updated existing shebangs in {len(updated_files)} files:")
        print("-" * 40)
        for path, rel_path in updated_files:
            file_info = rel_path
            if "." not in Path(rel_path).name:
                file_info += " (no extension)"
            print(f"  ✏️  {file_info}")
    if added_shebang_files:
        print(f"\n➕ Added new shebang to {len(added_shebang_files)} files:")
        print("-" * 40)
        for path, rel_path in added_shebang_files:
            file_info = rel_path
            if "." not in Path(rel_path).name:
                file_info += " (no extension)"
            print(f"  ➕ {file_info}")
    if not updated_files and not added_shebang_files:
        print("\n✅ No files needed updating.")
    print("\n" + "=" * 40)
    print("📊 Summary:")
    print(f"  ✏️  Updated existing shebangs: {len(updated_files)} files")
    print(f"  ➕ Added new shebangs: {len(added_shebang_files)} files")
    print(f"  ⏭️  Skipped (symlinks): {skipped_count} files")
    print(f"  ⏭️  Not Python shebang: {not_python_count} files")
    print(f"  ⏭️  Already correct: {already_correct_count} files")
    print(f"  📝 Total processed: {len(python_files)} files")
    if errors:
        print(f"  ❌ Errors: {len(errors)} files")
    if errors:
        print("\n❌ Errors:")
        for rel_path, error in errors:
            print(f"  - {rel_path}: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
