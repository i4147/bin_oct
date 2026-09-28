#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that recursively scans the current working directory for all files with a .sh extension and normalizes their shebang line to "#!/data/data/com.termux/files/usr/bin/bash", which is the standard interpreter path used in Termux environments on Android.
For each matching file, it should replace an existing shebang line (if the first line starts with "#!") or insert a new one if missing, ensuring a blank line follows the shebang when the next line isn't already empty, then rewrite the file in place.
It should print progress messages indicating which file is being processed and confirming the update, and if the file's path includes a "bin" directory component, it should also set the file's permissions to 0o755 (executable)."""

from pathlib import Path

TARGET_SHEBANG = "#!/data/data/com.termux/files/usr/bin/bash"
cwd = Path.cwd()


def process_file(path: Path) -> None:
    path = Path(path)
    print(f"processing {path.name}")
    with path.open("r+", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            return
        if lines[0].startswith("#!"):
            lines[0] = TARGET_SHEBANG + "\n"
            if len(lines) > 1 and lines[1].strip() != "":
                lines.insert(1, "\n")
        else:
            lines.insert(0, TARGET_SHEBANG + "\n")
            if len(lines) > 1 and lines[1].strip() != "":
                lines.insert(1, "\n")
        f.seek(0)
        f.writelines(lines)
        f.truncate()
        print(f"{path.name} updated")
    if "bin" in path.parts:
        path.chmod(0o755)


if __name__ == "__main__":
    for path in cwd.rglob("*.sh"):
        process_file(path)
