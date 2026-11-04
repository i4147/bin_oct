#!/usr/bin/env python3
"""Create the hand-reviewed first batch of documentation-only copies.

Run from the repository root. Original source files are never written.
"""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent.parent
EDITS = {
    '23.py': [
        ('#!/data/data/com.termux/files/usr/bin/env python\n', '#!/data/data/com.termux/files/usr/bin/env python\n"""Run Ruff checks and formatting on Python files below the current directory."""\n'),
        ('def walk_files(directory: Path) -> Iterator[Path]:\n', 'def walk_files(directory: Path) -> Iterator[Path]:\n    """Yield paths for files found recursively under directory."""\n'),
        ('def is_python_file(path: Path) -> bool:\n', 'def is_python_file(path: Path) -> bool:\n    """Recognize .py files or extensionless files with markers in their first 64 bytes."""\n'),
        ('def process_file(path: Path) -> None:\n', 'def process_file(path: Path) -> None:\n    """Run Ruff fixes and formatting on path, reporting command failures."""\n'),
        ('def get_all_files(cwd: Path) -> list[Path]:\n', 'def get_all_files(cwd: Path) -> list[Path]:\n    """Collect Python file paths recursively under cwd."""\n'),
        ('def main() -> None:\n', 'def main() -> None:\n    """Process discovered Python files in a worker pool."""\n'),
        ('        if len(pending) > 32:\n', '        # Bound the number of queued results before waiting for a worker.\n        if len(pending) > 32:\n'),
    ],
    '480mkv.py': [
        ('#!/data/data/com.termux/files/usr/bin/env python\n', '#!/data/data/com.termux/files/usr/bin/env python\n"""Keep lines containing mkv or mp4 and a selected resolution in a file.\n\nPass a file path as the first argument. The selected string is 480 if it\nappears anywhere in the file, otherwise 720. Rewrite only if lines match.\n"""\n'),
    ],
    '7ziper.py': [
        ('#!/data/data/com.termux/files/usr/bin/env python\n', '#!/data/data/com.termux/files/usr/bin/env python\n"""Compress or decompress entries in the current directory using 7-Zip modes.\n\nThe basic, named, and full subcommands can remove inputs after processing.\n"""\n'),
        ('def run_basic(args: argparse.Namespace) -> int:\n', 'def run_basic(args: argparse.Namespace) -> int:\n    """Compress current-directory entries in worker pools and log results.\n\n    Successfully compressed source files and directories are removed.\n    The namespace supplies the log file and compression preset.\n    """\n'),
        ('class NamedResult:\n', 'class NamedResult:\n    """Hold a named-mode source, destination, success flag, and error message."""\n\n'),
        ('        _named_remove(path)\n        return NamedResult(str(path), str(tar_path), True)', '        # Keep the source until the tar archive has been closed successfully.\n        _named_remove(path)\n        return NamedResult(str(path), str(tar_path), True)'),
        ('def run_named(args: argparse.Namespace) -> int:\n', 'def run_named(args: argparse.Namespace) -> int:\n    """Archive current-directory entries using named-mode workers and log results.\n\n    Directories become tar files, files become 7z archives, and successful\n    inputs are removed. The namespace supplies the log file.\n    """\n'),
        ('def run_full(args: argparse.Namespace) -> int:\n', 'def run_full(args: argparse.Namespace) -> int:\n    """Run full-mode compression or decompression in the current directory.\n\n    The namespace selects the mode and supplies compression settings.\n    Successfully processed inputs may be removed.\n    """\n'),
        ('def build_parser() -> argparse.ArgumentParser:\n', 'def build_parser() -> argparse.ArgumentParser:\n    """Build the parser for the basic, named, and full subcommands."""\n'),
        ('def main(argv: Optional[list] = None) -> int:\n', 'def main(argv: Optional[list] = None) -> int:\n    """Parse arguments and dispatch to the selected archive mode.\n\n    Returns the mode result, or 1 if interrupted or an error is caught.\n    """\n'),
    ],
    'a-b.py': [
        ('#!/data/data/com.termux/files/usr/bin/env python\n', '#!/data/data/com.termux/files/usr/bin/env python\n"""Remove lines from the first file that also occur in the second file.\n\nPass the two file paths as command-line arguments; the first file is replaced.\n"""\n'),
        ('def main() -> None:\n', 'def main() -> None:\n    """Replace the first argument file with lines absent from the second."""\n'),
    ],
    'abline.py': [
        ('#!/data/data/com.termux/files/usr/bin/env python\n', '#!/data/data/com.termux/files/usr/bin/env python\n"""Keep text before or near a marker in each nonempty input line.\n\nPass mode, file path, and marker as arguments; nonempty results replace\nthe file. Mode -a selects text before the first marker; other modes select\nfrom one character after its start.\n"""\n'),
        ('def read_lines(path: Path) -> list[str]:\n', 'def read_lines(path: Path) -> list[str]:\n    """Read UTF-8 lines from path, retaining line endings."""\n'),
        ('def process_a(line: str, target_char: str) -> str:\n', 'def process_a(line: str, target_char: str) -> str:\n    """Return stripped text before the first delimiter, or the whole text."""\n'),
        ('def process_b(line: str, target_char: str) -> str:\n', 'def process_b(line: str, target_char: str) -> str:\n    """Return text from one character after the first marker, or all text."""\n'),
    ],
}

class StripDocstrings(ast.NodeTransformer):
    """Discard docstrings for structural comparison without executing sources."""
    def clean(self, node):
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            node.body.pop(0)
        return self.generic_visit(node)
    visit_Module = clean
    visit_FunctionDef = clean
    visit_AsyncFunctionDef = clean
    visit_ClassDef = clean

for name, replacements in EDITS.items():
    original = (ROOT / name).read_text(encoding='utf-8')
    result = original
    for before, after in replacements:
        count = result.count(before)
        if count != 1:
            raise ValueError(f'{name}: expected one match, got {count}: {before[:60]!r}')
        result = result.replace(before, after, 1)
    old_tree = StripDocstrings().visit(ast.parse(original, filename=name))
    new_tree = StripDocstrings().visit(ast.parse(result, filename=name))
    if ast.dump(old_tree, include_attributes=False) != ast.dump(new_tree, include_attributes=False):
        raise ValueError(f'{name}: non-documentation AST change')
    dest = ROOT / 'documented' / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(result, encoding='utf-8')
    print(f'{name}: verified documentation-only AST and wrote {dest.relative_to(ROOT)}')
