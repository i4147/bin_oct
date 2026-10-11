#!/data/data/com.termux/files/usr/bin/env python
"""You are reproducing a Python utility script from scratch. Write a single, self-contained Python 3 script that meets the specification below. Output only the script's source code, with no commentary before or after it.

**Purpose:** The script is a Termux-targeted (Android, `/data/data/com.termux` shebang) code-extraction tool. It scans a directory tree for Python source files and archive files, extracts Python source out of archives, parses each Python file's AST, and splits the code into individual entity files (functions, classes, and similar top-level or nested definitions) saved under an output directory.

**Configuration constants to define:**
- An output directory named `output`, relative to the current working directory.
- A tuple of recognized archive extensions: `.whl`, `.zip`, `.tar.gz`, `.tgz`, `.tar.zst`, `.tar.xz`, `.tar`, `.zst`. Note that compound extensions such as `.tar.gz` must be matched before the simpler ones.
- A tuple of allowed Python file extensions: `.py` and the empty string (to accept extensionless scripts that are verified as Python).

**Main components:**

1. **An AST-based entity extractor** that subclasses the standard library's node visitor. It is constructed with the full source text and the original file path. It keeps a list of extracted entities and a scope-depth counter. It splits source text into lines preserving line endings, and provides a helper that extracts the exact source text of a given AST node by line range and column offsets (trimming the first line's start column and the last line's end column). A shared save helper appends each entity as a record containing at least its name, type, source code, and origin path, and it should also track whether the entity is nested. Visit handlers should cover function definitions (sync and async) and class definitions, incrementing and decrementing scope depth while descending into their bodies so nested definitions are recorded with appropriate context.

2. **Archive handling:** Detect archives by extension (using the compound-extension list correctly). Extract them into a temporary working location, then walk the extracted tree to find Python files. Support `.zip` and `.whl` via the zipfile module, and the tar-based formats via tarfile. For `.zst` and `.tar.zst` formats, use an external decompression approach (for example, invoking the `zstd` command-line tool via subprocess) since the standard library does not support zstd; handle the case where that tool is missing gracefully. Guard against path traversal when extracting archives (reject members whose resolved paths escape the target directory). Clean up temporary extraction directories afterward using shutil.

3. **Python file discovery:** Walk the input directory recursively. A file qualifies as Python if its extension is in the allowed list, and for extensionless files, check whether the content parses as valid Python (or whether the first line is a Python shebang) before accepting it. Skip files that cannot be read as text and files that fail to parse, logging a short warning rather than crashing.

4. **Processing pipeline:** For each discovered Python file, read it as UTF-8 (with a tolerant fallback such as ignoring decode errors), parse with `ast.parse`, run the extractor, and write each extracted entity to its own file under the output directory, organized into a subdirectory per source file. Output file names should be sanitized (replace unsafe characters with underscores) and must avoid collisions by appending a counter when needed.

5. **Parallelism:** Use `multiprocessing.Pool` sized to the CPU count (via `cpu_count()`) to process files concurrently. The per-file worker function must be a top-level function so it is picklable. Collect and report aggregate results from the pool.

**Command-line usage:** Accept one or more input paths (files or directories) as command-line arguments, with the output directory defaulting to `output`. If no arguments are given, print a usage message and exit with a non-zero status. Print a summary at the end showing the number of files scanned, Python files processed, entities extracted, and any files skipped or failed.

**Error handling and edge cases:**
- Never let one bad file or archive abort the whole run; catch exceptions per item and report them.
- Handle missing input paths by reporting them and continuing with the rest.
- Handle empty files, files containing only comments, syntax errors, decode errors, and archives that are corrupt or unsupported.
- Ensure the output directory is created if missing, and that re-running does not corrupt previously written output (overwrite or namespace consistently).
- Handle symbolic links safely (do not follow links out of the input tree during the walk, or do so only with cycle protection).

**Dependencies:** Only the Python standard library is used: `ast`, `os`, `re`, `shutil`, `tarfile`, `zipfile`, `multiprocessing`, `pathlib`, `typing`, `subprocess`, `sys`, `tempfile`. Target Python 3.8+ and begin the file with `from __future__ import annotations`. The script should be runnable directly via its shebang line and as `python script.py <paths...>`.

**Style:** Use type hints where they aid clarity, `pathlib.Path` for paths, concise docstrings or comments only where they help, and keep the code idiomatic and readable.
---"""

from __future__ import annotations

import ast
import os
import re
import shutil
import tarfile
import zipfile
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any

OUTPUT_DIR = Path("output")
ARCHIVE_EXTENSIONS = (
    ".whl",
    ".zip",
    ".tar.gz",
    ".tgz",
    ".tar.zst",
    ".tar.xz",
    ".tar",
    ".zst",
)
ALLOWED_PYTHON_EXTENSIONS = (".py", "")


class EntityExtractor(ast.NodeVisitor):
    def __init__(self, source_content: str, original_path: Path):
        self.entities = []
        self.source_lines = source_content.splitlines(keepends=True)
        self.original_path = original_path
        self.scope_depth = 0

    def _get_source_slice(self, node: ast.AST) -> str:
        start_line = node.lineno - 1
        end_line = node.end_lineno or node.lineno
        code_slice = self.source_lines[start_line:end_line]
        if node.col_offset is not None:
            code_slice[0] = code_slice[0][node.col_offset :]
        if node.end_col_offset is not None and node.end_col_offset > 0:
            last_line = code_slice[-1]
            code_slice[-1] = last_line[: node.end_col_offset]
        return "".join(code_slice)

    def _extract_and_save(self, node: ast.AST, entity_type: str, name: str):
        entity_code = self._get_source_slice(node)
        self.entities.append({
            "name": name,
            "full_name": name,
            "type": entity_type,
            "code": entity_code,
            "path": str(self.original_path),
            "is_constant": entity_type == "constant",
            "is_class": entity_type == "class",
            "is_function": entity_type == "function",
        })

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.scope_depth == 0:
            self._extract_and_save(node, "function", node.name)
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        if self.scope_depth == 0:
            self._extract_and_save(node, "function", node.name)
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1

    def visit_ClassDef(self, node: ast.ClassDef):
        if self.scope_depth == 0:
            self._extract_and_save(node, "class", node.name)
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1

    def visit_Assign(self, node: ast.Assign):
        if self.scope_depth == 0 and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
            if re.match("^[A-Z_][A-Z0-9_]*$", target_name):
                self._extract_and_save(node, "constant", target_name)

    def generic_visit(self, node: ast.AST):
        super().generic_visit(node)


def get_unique_path(base_path: Path) -> Path:
    if not base_path.exists():
        return base_path
    name = base_path.stem
    suffix = base_path.suffix
    i = 1
    while True:
        new_path = base_path.with_name(f"{name}_{i}{suffix}")
        if not new_path.exists():
            return new_path
        i += 1


def save_entity(entity: dict[str, Any]):
    filename_base = f"{entity['full_name']}.py"
    output_path_base = OUTPUT_DIR / entity["type"] / filename_base
    output_path_base.parent.mkdir(parents=True, exist_ok=True)
    comment = f"# Original path: {entity['path']}\n"
    content = comment + entity["code"]
    final_py_path = get_unique_path(output_path_base)
    try:
        with open(final_py_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"Error saving {final_py_path}: {e}")


def extract_entities_from_content(content: str, path: Path) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(content)
        extractor = EntityExtractor(content, path)
        extractor.visit(tree)
        return extractor.entities
    except SyntaxError:
        return []
    except Exception as e:
        print(f"Error parsing AST for {path}: {e}")
        return []


def is_python_file_no_extension(path: Path) -> bool:
    if path.suffix:
        return False
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            first_lines = "".join(f.readlines(1024))
            if re.match(r"#!\s*/.*python", first_lines):
                return True
            if "def " in first_lines or "class " in first_lines or "import " in first_lines:
                return True
    except:
        pass
    return False


def process_single_file(path: Path) -> list[dict[str, Any]]:
    try:
        if path.suffix == ".py" or is_python_file_no_extension(path):
            content = path.read_text(encoding="utf-8", errors="ignore")
            return extract_entities_from_content(content, path)
        return []
    except Exception as e:
        print(f"Error reading file {path}: {e}")
        return []


def process_archive(path: Path) -> list[dict[str, Any]]:
    entities = []
    if path.suffix in (".zip", ".whl"):
        try:
            with zipfile.ZipFile(path, "r") as zf:
                for member in zf.namelist():
                    member_path = Path(member)
                    if member_path.suffix == ".py":
                        with zf.open(member) as member_file:
                            content = member_file.read().decode("utf-8", errors="ignore")
                            virtual_path = Path(f"{path}/{member}")
                            entities.extend(extract_entities_from_content(content, virtual_path))
        except Exception as e:
            print(f"Error processing ZIP/WHL archive {path}: {e}")
    elif any(path.name.endswith(ext) for ext in [".tar", ".tar.gz", ".tgz", ".tar.zst", ".tar.xz"]):
        mode_map = {
            ".tar.gz": "r:gz",
            ".tgz": "r:gz",
            ".tar.zst": "r:zst",
            ".tar.xz": "r:xz",
            ".tar": "r",
        }
        mode = next((mode_map[ext] for ext in mode_map if path.name.endswith(ext)), "r")
        try:
            with tarfile.open(path, mode) as tf:
                for member in tf.getmembers():
                    member_path = Path(member.name)
                    if member.isfile() and member_path.suffix == ".py":
                        member_file = tf.extractfile(member)
                        if member_file:
                            content = member_file.read().decode("utf-8", errors="ignore")
                            virtual_path = Path(f"{path}/{member.name}")
                            entities.extend(extract_entities_from_content(content, virtual_path))
        except tarfile.ReadError:
            pass
        except Exception as e:
            print(f"Error processing TAR archive {path}: {e}")
    return entities


def worker_process(path_str: str) -> list[dict[str, Any]]:
    path = Path(path_str)
    if path.name.endswith(ARCHIVE_EXTENSIONS):
        return process_archive(path)
    return process_single_file(path)


def main():
    print(f"Starting analysis in {Path.cwd()}...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
        print(f"Cleaned previous output directory: {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(exist_ok=True)
    files_to_process = []
    current_dir = Path()
    for root, _, filenames in os.walk(current_dir):
        for name in filenames:
            path = Path(root) / name
            if path.is_relative_to(OUTPUT_DIR):
                continue
            is_archive = path.suffix in ARCHIVE_EXTENSIONS or any(path.name.endswith(ext) for ext in ARCHIVE_EXTENSIONS)
            is_py = path.suffix in ALLOWED_PYTHON_EXTENSIONS or is_python_file_no_extension(path)
            if is_archive or is_py:
                files_to_process.append(str(path))
    if not files_to_process:
        print("No Python files or archives found to process.")
        return
    print(f"Found {len(files_to_process)} relevant files/archives. Starting multiprocessing pool...")
    num_cpus = cpu_count()
    all_entities = []
    with Pool(processes=num_cpus) as pool:
        results_list = pool.map(worker_process, files_to_process)
        for result in results_list:
            all_entities.extend(result)
    print(f"Processing complete. Extracted {len(all_entities)} entities.")
    print(f"Saving entities to {OUTPUT_DIR}...")
    for entity in all_entities:
        save_entity(entity)
    print("\n\nAll tasks finished successfully!")
    print(f"Results are saved in the '{OUTPUT_DIR}' folder, organized by entity type (class, function, constant).")


if __name__ == "__main__":
    raise SystemExit(main())
