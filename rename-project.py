#!/data/data/com.termux/files/usr/bin/python


import os
import re
import sys
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    ".eggs",
    ".idea",
    ".vscode",
}

TEXT_EXTS = {
    ".py",
    ".pyi",
    ".pyx",
    ".pxd",
    ".c",
    ".h",
    ".txt",
    ".md",
    ".rst",
    ".toml",
    ".cfg",
    ".ini",
    ".json",
    ".yaml",
    ".yml",
    ".in",
    ".jinja",
    ".jinja2",
    ".tmpl",
    ".tpl",
    ".sh",
    ".bash",
    ".zsh",
    ".bat",
    ".ps1",
    ".html",
    ".css",
    ".js",
    ".ts",
}

TEXT_PREFIXES = (
    "readme",
    "license",
    "copying",
    "changelog",
    "authors",
    "notice",
    "requirements",
    "makefile",
    "dockerfile",
)

DOTFILES = {
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".flake8",
    ".pylintrc",
    ".coveragerc",
}


def looks_textual(path: Path) -> bool:
    name = path.name.lower()
    if name in DOTFILES:
        return True
    if path.suffix.lower() in TEXT_EXTS:
        return True
    if name.startswith(TEXT_PREFIXES):
        return True
    return False


def build_replacer(old: str, new: str):
    pattern = re.compile(r"\b" + re.escape(old) + r"\b", re.IGNORECASE)

    def _repl(match: re.Match) -> str:
        token = match.group(0)
        if token.isupper():
            return new.upper()
        if token.islower():
            return new.lower()
        if token.istitle():
            return new.title()
        return new

    return pattern, _repl


def replace_in_file(path: Path, pattern, repl) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    new_text = pattern.sub(repl, text)
    if new_text == text:
        return False
    try:
        path.write_text(new_text, encoding="utf-8")
    except OSError:
        return False
    return True


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2

    project_dir = Path(argv[1]).resolve()
    new_name = argv[2]

    if not project_dir.is_dir():
        print(f"error: {project_dir} is not a directory", file=sys.stderr)
        return 1
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", new_name):
        print(f"error: '{new_name}' is not a valid Python identifier", file=sys.stderr)
        return 1

    old_name = project_dir.name
    if old_name == new_name:
        print("error: old and new names are identical", file=sys.stderr)
        return 1

    pattern, repl = build_replacer(old_name, new_name)

    files_updated = 0
    for dirpath, dirnames, filenames in os.walk(project_dir):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fname in sorted(filenames):
            p = Path(dirpath) / fname
            if looks_textual(p) and replace_in_file(p, pattern, repl):
                files_updated += 1

    to_rename: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(project_dir, topdown=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames + dirnames:
            if pattern.search(name):
                to_rename.append(Path(dirpath) / name)

    renamed: list[tuple[str, str]] = []
    for src in to_rename:
        new_filename = pattern.sub(repl, src.name)
        dst = src.with_name(new_filename)
        if dst.exists():
            continue
        src.rename(dst)
        renamed.append((src.name, new_filename))

    target_dir = project_dir.with_name(new_name)
    if target_dir.exists():
        print(f"error: {target_dir} already exists", file=sys.stderr)
        return 1
    project_dir.rename(target_dir)

    print(f"Renamed project '{old_name}' -> '{new_name}'")
    print(f"  new path:              {target_dir}")
    print(f"  files updated:         {files_updated}")
    print(f"  files/folders renamed: {len(renamed)}")
    for old, new in renamed:
        print(f"    {old}  ->  {new}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
