#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans a directory for Lua source files, checks each file for syntax errors using a Lua-aware parser, and quarantines any file that fails validation. The tool should operate on the current working directory by default and examine every Lua file it finds there. For each file, it should read the source, parse it with a Lua grammar, and walk the resulting syntax tree to detect any malformed or missing constructs. Files that parse cleanly should be left untouched. Files containing syntax errors should be moved into a dedicated subfolder named "error" created alongside them, so that the original folder structure is preserved without overwriting anything. If a file with the same name already exists in that subfolder, the tool should rename the incoming file with a numeric suffix rather than replacing the existing one. Every move should be reported to the user with a clear message showing the original and new locations. The script should be runnable from the command line, handle missing or unreadable files gracefully, and produce a concise summary of how many files were checked, how many were valid, and how many were moved.
---"""

from __future__ import annotations
from pathlib import Path
from tree_sitter import Language, Parser
import tree_sitter_lua


def make_parser() -> Parser:
    language = Language(tree_sitter_lua.language())
    return Parser(language)


def has_syntax_error(parser: Parser, source: bytes) -> bool:
    tree = parser.parse(source)
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.is_error or node.is_missing:
            return True
        stack.extend(node.children)
    return False


def move_to_error_dir(path: Path) -> None:
    error_dir = path.parent / "error"
    error_dir.mkdir(exist_ok=True)
    target = error_dir / path.name
    if target.exists():
        i = 1
        while True:
            candidate = error_dir / f"{path.stem}_{i}{path.suffix}"
            if not candidate.exists():
                target = candidate
                break
            i += 1
    path.rename(target)
    print(f"Moved: {path} -> {target}")


def main() -> None:
    parser = make_parser()
    cwd = Path.cwd()
    for lua_file in cwd.rglob("*.lua"):
        if "error" in lua_file.parts:
            continue
        try:
            source = lua_file.read_bytes()
        except OSError as e:
            print(f"Could not read {lua_file}: {e}")
            continue
        if has_syntax_error(parser, source):
            move_to_error_dir(lua_file)
        else:
            print(f"OK: {lua_file}")


if __name__ == "__main__":
    main()
