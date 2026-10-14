#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts Jupyter notebook files (.ipynb) into plain Python source files, so the resulting scripts can be run, linted, or version-controlled as ordinary code.
The tool should accept one or more notebook file paths (or a directory to search recursively) as input, and write a corresponding .py file for each notebook, either alongside the original or into a specified output location. It should process multiple notebooks concurrently using a small pool of worker processes to speed up batch conversions.
Key behaviors:
- Only code cells should be carried over into the output. Markdown and raw cells should either be omitted or converted into comments, so the resulting file remains valid Python.
- Each code cell should be clearly separated in the output with a readable marker or comment indicating the cell boundary, so the user can trace code back to its original position in the notebook.
- IPython-specific syntax such as line magics (lines starting with `%`), shell escapes (lines starting with `!`), and cell magics (starting with `%%`) must not break the output. These lines should be preserved as comments, clearly tagged so the user knows they were originally magic commands, including multi-line magics that continue with a trailing backslash.
- Import statements should be gathered and consolidated near the top of the generated file, with duplicates removed, so the script reads cleanly and imports are easy to inspect.
- Cell outputs, execution counts, and notebook metadata should be discarded; only the source code matters in the result.
- Empty or whitespace-only code cells should be skipped.
- The tool should handle malformed or unreadable notebooks gracefully, logging a clear warning or error for each failed file without stopping the whole batch.
- Provide a summary at the end reporting how many notebooks were converted successfully and how many failed.
- Include a command-line interface with options for input paths, output directory, and the number of parallel workers, with sensible defaults.
- Use structured, informative logging so the user can follow progress across parallel conversions.
- Ensure the output files are written with UTF-8 encoding and end with a trailing newline.
---"""

from __future__ import annotations
from multiprocessing import Pool
from pathlib import Path
import sys
from typing import TYPE_CHECKING
from loguru import logger
import nbformat
from nbformat import NotebookNode

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
POOL_SIZE: int = 8
MAGIC_PREFIXES: tuple[str, ...] = ("%", "!", "%%")
IMPORT_PREFIXES: tuple[str, ...] = ("import ", "from ")


def is_import_line(line: str) -> bool:
    return line.startswith(IMPORT_PREFIXES)


def strip_magics(source: str) -> str:
    lines: list[str] = source.split("\n")
    result: list[str] = []
    i: int = 0
    while i < len(lines):
        line: str = lines[i]
        stripped: str = line.lstrip()
        if stripped.startswith(MAGIC_PREFIXES):
            result.append(f"# [MAGIC] {line.rstrip()}")
            while i < len(lines) - 1 and line.rstrip().endswith("\\"):
                i += 1
                line = lines[i]
                result.append(f"# [MAGIC] {line.rstrip()}")
        else:
            result.append(line)
        i += 1
    return "\n".join(result)


def nb2py(notebook: NotebookNode) -> str:
    imports: list[str] = []
    os_mods: list[str] = []
    sys_mods: list[str] = []
    main_code: list[str] = []
    cell: NotebookNode
    for cell in notebook.cells:
        if cell.cell_type == "markdown":
            md_text: str = str(cell.source).replace("\n", "\n# ")
            main_code.append(f"# {md_text}\n")
        elif cell.cell_type == "code":
            cell_code: str = str(cell.source)
            line: str
            for line in cell_code.split("\n"):
                if line.strip().startswith("!nb2py"):
                    continue
                if is_import_line(line):
                    imports.append(line)
                    continue
                if line.startswith("os.environ"):
                    os_mods.append(line)
                    continue
                if line.startswith("sys.path"):
                    sys_mods.append(line)
                    continue
                cleaned: str = strip_magics(line)
                main_code.append(cleaned)
    idx: int
    line = ""
    for idx, line in enumerate(imports):
        if "import os" in line or "from os import" in line:
            for mod in sorted(os_mods, reverse=True):
                imports.insert(idx + 1, mod)
            break
    for idx, line in enumerate(imports):
        if "import sys" in line or "from sys import" in line:
            for mod in sorted(sys_mods, reverse=True):
                imports.insert(idx + 1, mod)
            break
    imports_str: str = "\n".join(imports) + "\n\n"
    main_str: str = "\n".join(main_code)
    indent: str = "    "
    main_indented: str = "\n".join(f"{indent}{ln}" for ln in main_str.split("\n"))
    return f"{imports_str}if __name__ == '__main__':\n{main_indented}"


def process_file(path: Path) -> str | None:
    path = Path(path)
    fo: Path = path.with_suffix(".py")
    if fo.exists():
        return None
    with path.open(encoding="utf-8") as f:
        nb: NotebookNode = nbformat.read(f, as_version=4)
    py_code: str = nb2py(nb)
    with fo.open("w", encoding="utf-8") as out:
        out.write(py_code)
    return f"Exported → {fo.name}"


def _collect_files(args: Sequence[str]) -> list[Path]:
    if not args:
        return list(Path.cwd().rglob("*.ipynb"))
    files: list[Path] = []
    arg: str
    for arg in args:
        p: Path = Path(arg)
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(p.rglob("*.ipynb"))
    return files


def main(argv: Iterable[str] | None = None) -> int:
    args: list[str] = list(argv) if argv is not None else sys.argv[1:]
    files: list[Path] = _collect_files(args)
    if not files:
        logger.info("No .ipynb files found")
        return 0
    logger.info("Found {} notebook(s) to convert using {} workers", len(files), POOL_SIZE)
    with Pool(processes=POOL_SIZE) as pool:
        results = [pool.apply_async(process_file, (f,)) for f in files]
        result: AsyncResult[str | None]
        for result in results:
            message: str | None = result.get()
            if message:
                logger.info("{}", message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
