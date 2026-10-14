#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory (recursively, including subdirectories) for all Python source files and collects every top-level import statement from them plain imports and "from ... import" statements. The script should parse each file's source code structurally rather than using simple text matching, so that only genuine top-level import statements are captured. Relative imports (those starting with a leading dot, referring to the package's own modules) must be excluded from the results. Duplicate import statements appearing across multiple files should be included only once, while preserving the order in which they were first discovered.
The script should process files in parallel to remain efficient on large projects. Once all imports are gathered, it must write them into a single consolidated Python file placed in an output directory located in the user's home folder under a "tmp/output" path (create the directory if it does not exist). The output file should be named after the current working directory's folder name with an "_importz.py" suffix. If a file with that name already exists, the script must not overwrite it and instead generate a unique alternative filename. The output file should contain the collected import lines, one per line, and nothing else. The script should run as a command-line tool with no required arguments, and it should print a brief confirmation message indicating where the consolidated import file was saved.
---"""

from __future__ import annotations
from pathlib import Path
from dh import get_files, mpf, unique_path
from tree_sitter import Language, Parser
import tree_sitter_python as tsp

OUTPUT_DIR = Path.home() / "tmp" / "output"
parser = Parser()
parser.language = Language(tsp.language())
VALID = {"import_statement", "import_from_statement"}


def process_file(path):
    path = Path(path)
    src = path.read_bytes()
    tree = parser.parse(src)
    root = tree.root_node
    return [src[node.start_byte : node.end_byte].decode() for node in root.children if node.type in VALID]


def main() -> None:
    cwd = Path.cwd()
    outfile = OUTPUT_DIR / f"{cwd.name}_importz.py"
    if outfile.exists():
        outfile = unique_path(outfile)
    all_imports = []
    files = get_files(cwd, ext=[".py"])
    results = mpf(process_file, files)
    for imports in results:
        if imports:
            for k in imports:
                if not k.startswith("from .") and k not in all_imports:
                    all_imports.append(k)
    all_imports = sorted(set(all_imports))
    outfile.write_text("\n".join(all_imports), encoding="utf-8")
    print("done.")


if __name__ == "__main__":
    raise SystemExit(main())
