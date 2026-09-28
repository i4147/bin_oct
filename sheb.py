#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that recursively scans a directory tree and normalizes shebang lines in Python scripts for Termux compatibility.
It should skip empty files and __init__.py files, and detect Python files either by the ".py" extension or by inspecting the first non-comment line for typical Python syntax (import, from, class, def) or an existing python shebang.
For each detected file, it should either replace an existing shebang line with "#!/data/data/com.termux/files/usr/bin/env python" (inserting a blank line after it if needed) or prepend this shebang if the file contains Python code but lacks one, leaving other files untouched."""

import os
from pathlib import Path
TARGET_SHEBANG = "#!/data/data/com.termux/files/usr/bin/env python"
def is_python_file(path) -> bool:
    if Path(path).stat().st_size == 0 or path.endswith("__init__.py"):
        return False
    if path.endswith(".py"):
        return True
    try:
        with Path(path).open(encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line.startswith("#!") and "python" in first_line:
                return True
            if first_line.startswith("#!") and "python" in first_line:
                return True
            f.seek(0)
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    return line.startswith(("import ", "from ", "class ", "def "))
            return False
    except (OSError, UnicodeDecodeError):
        return False
def process_file(path) -> None:
    Path(path)
    with Path(path).open("r+", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            return
        if lines and lines[0].startswith("#!"):
            lines[0] = TARGET_SHEBANG + "\n"
            if len(lines) > 1 and lines[1].strip():
                lines.insert(1, "\n")
        else:
            has_python_code = any(
                line.strip().startswith(("import ", "from ", "def ", "class "))
                for line in lines
            )
            if has_python_code:
                lines.insert(0, TARGET_SHEBANG + "\n")
                lines.insert(1, "\n")
        f.seek(0)
        f.writelines(lines)
        f.truncate()
        print(f"{os.path.relpath(path)} updated.")
    if "bin" in path.split(os.sep):
        Path(path).chmod(0o755)
def traverse_directory(directory: Path) -> None:
    for root, _, files in os.walk(directory):
        for filename in files:
            path = os.path.join(root, filename)
            if Path(path).is_symlink():
                continue
            if is_python_file(path):
                process_file(path)
if __name__ == "__main__":
    traverse_directory(Path.cwd())